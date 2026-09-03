"""
Ingestion des fichiers stock SIRENE dans DuckDB.

Principe : on ne charge JAMAIS le fichier en pandas (12 Go décompressés).
DuckDB lit le parquet/CSV directement et ne matérialise que les colonnes retenues.

Deux modes :

  1. ÉCHANTILLON DISTANT — pour développer sans attendre le téléchargement.
     DuckDB lit le parquet par plages HTTP et s'arrête après N lignes.
         python ingestion/load_duckdb.py --sample 200000

  2. COMPLET LOCAL — une fois les fichiers téléchargés dans data/.
         python ingestion/load_duckdb.py

Résultat : sirene.duckdb avec trois tables dans le schéma `raw`.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import zipfile
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DB_PATH = ROOT / "sirene.duckdb"

# --- Colonnes retenues -------------------------------------------------------
# Le fichier établissements compte 95 variables. On en garde 16 : tout ce qui
# n'entre pas dans la question "où la création accélère-t-elle, par secteur et
# par département" est du poids mort. C'est le premier levier de performance.

COLS_ETABLISSEMENTS = [
    "siren", "nic", "siret",
    "statutDiffusionEtablissement",
    "dateCreationEtablissement",
    "trancheEffectifsEtablissement",
    "etablissementSiege",
    "codeCommuneEtablissement",
    "codePostalEtablissement",
    "libelleCommuneEtablissement",
    "dateDebut",
    "etatAdministratifEtablissement",
    "activitePrincipaleEtablissement",
    "nomenclatureActivitePrincipaleEtablissement",
    "activitePrincipaleNAF25Etablissement",
    "caractereEmployeurEtablissement",
]

COLS_UNITES_LEGALES = [
    "siren",
    "statutDiffusionUniteLegale",
    "dateCreationUniteLegale",
    "categorieEntreprise",
    "anneeCategorieEntreprise",
    "categorieJuridiqueUniteLegale",
    "etatAdministratifUniteLegale",
    "activitePrincipaleUniteLegale",
    "activitePrincipaleNAF25UniteLegale",
    "denominationUniteLegale",
    "trancheEffectifsUniteLegale",
]

COLS_HISTORIQUE = [
    "siren", "nic", "siret",
    "dateDebut", "dateFin",
    "etatAdministratifEtablissement",
    "changementEtatAdministratifEtablissement",
    "activitePrincipaleEtablissement",
    "changementActivitePrincipaleEtablissement",
]

# Colonnes à forcer en VARCHAR : un SIRET lu en integer perd ses zéros de tête
# et casse toutes les jointures. Erreur n°1 sur ce dataset.
FORCE_VARCHAR = {"siren", "nic", "siret", "codeCommuneEtablissement",
                 "codePostalEtablissement", "activitePrincipaleEtablissement",
                 "activitePrincipaleUniteLegale", "categorieJuridiqueUniteLegale"}

SOURCES = {
    "etablissements": (COLS_ETABLISSEMENTS, "StockEtablissement"),
    "unites_legales": (COLS_UNITES_LEGALES, "StockUniteLegale"),
    "etablissements_historique": (COLS_HISTORIQUE, "StockEtablissementHistorique"),
}

def sample_urls() -> dict[str, str]:
    """
    URL du parquet distant, résolues par download.py et déposées dans data/resources.json.
    DuckDB les lit par plages HTTP : on obtient un échantillon réel en quelques secondes,
    sans attendre la fin du téléchargement complet.
    """
    fichier = DATA_DIR / "resources.json"
    if not fichier.exists():
        raise SystemExit(
            "data/resources.json absent — lance d'abord :\n"
            "    python ingestion/download.py --list\n"
            "ou lance le téléchargement, qui écrit ce fichier dès la résolution des URL."
        )
    resolues = json.loads(fichier.read_text(encoding="utf-8"))
    return {nom: resolues[prefix] for nom, (_, prefix) in SOURCES.items() if prefix in resolues}


def unzip_if_needed(zip_path: Path) -> Path:
    """Extrait le CSV d'un zip stock s'il n'a pas déjà été extrait."""
    with zipfile.ZipFile(zip_path) as zf:
        inner = zf.namelist()[0]
        target = DATA_DIR / inner
        if not target.exists():
            print(f"  décompression de {zip_path.name} → {inner}")
            zf.extract(inner, DATA_DIR)
    return target


def find_local(prefix: str) -> Path | None:
    """
    Trouve le fichier local disponible : parquet, puis csv, puis zip.

    Le nom de base est compare exactement : un glob "StockEtablissement*" capturerait
    aussi StockEtablissementHistorique et chargerait le mauvais fichier en silence.
    """
    for ext in (".parquet", ".csv", ".zip"):
        candidats = [p for p in DATA_DIR.glob(f"*{ext}")
                     if p.stem.split("_")[0] == prefix]
        if candidats:
            path = sorted(candidats)[0]
            return unzip_if_needed(path) if path.suffix == ".zip" else path
    return None


def build_scan(path_or_url: str, cols: list[str]) -> str:
    """Construit l'expression de lecture DuckDB adaptée au format."""
    if path_or_url.endswith(".parquet"):
        return f"read_parquet('{path_or_url}')"
    types = ", ".join(f"'{c}': 'VARCHAR'" for c in cols if c in FORCE_VARCHAR)
    return (
        f"read_csv('{path_or_url}', header=true, delim=',', "
        f"types={{{types}}}, ignore_errors=false)"
    )


def load(con: duckdb.DuckDBPyConnection, table: str, source: str,
         cols: list[str], limit: int | None) -> None:
    scan = build_scan(source, cols)
    select = ", ".join(f'"{c}"' for c in cols)
    tail = f" LIMIT {limit}" if limit else ""

    print(f"[{table}] lecture de {source.split('/')[-1]}")
    start = time.time()
    con.execute(f"CREATE OR REPLACE TABLE raw.{table} AS "
                f"SELECT {select} FROM {scan}{tail}")
    n = con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()[0]
    print(f"  {n:,} lignes en {time.time() - start:.1f}s".replace(",", " "))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, metavar="N",
                        help="charger N lignes depuis le parquet distant (dev)")
    parser.add_argument("--only", choices=list(SOURCES))
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    urls_distantes: dict[str, str] = {}
    if args.sample:
        con.execute("INSTALL httpfs; LOAD httpfs;")
        urls_distantes = sample_urls()

    cibles = [args.only] if args.only else list(SOURCES)

    for nom in cibles:
        cols, prefix = SOURCES[nom]
        if args.sample:
            source = urls_distantes[nom]
        else:
            local = find_local(prefix)
            if local is None:
                print(f"[{nom}] fichier absent de data/ — lance download.py d'abord")
                continue
            source = str(local)
        load(con, nom, source, cols, args.sample)

    print("\nContrôle rapide — top 5 départements par nombre d'établissements actifs :")
    try:
        rows = con.execute("""
            SELECT
                CASE WHEN left(codeCommuneEtablissement, 2) = '97'
                     THEN left(codeCommuneEtablissement, 3)
                     ELSE left(codeCommuneEtablissement, 2) END AS departement,
                count(*) AS n
            FROM raw.etablissements
            WHERE etatAdministratifEtablissement = 'A'
            GROUP BY 1 ORDER BY n DESC LIMIT 5
        """).fetchall()
        for dep, n in rows:
            print(f"  {dep}  {n:,}".replace(",", " "))
    except duckdb.Error as exc:
        print(f"  (contrôle impossible : {exc})")

    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
