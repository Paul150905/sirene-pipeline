"""
Téléchargement des fichiers stock SIRENE (INSEE) depuis data.gouv.fr.

Les URL directes des fichiers changent à chaque publication mensuelle : les coder
en dur condamne le script à casser au mois suivant. On interroge donc l'API du
catalogue data.gouv pour résoudre, à l'exécution, l'URL stable de chaque ressource
à partir de son nom de fichier.

Trois fichiers suffisent pour répondre à la question du projet :
  - StockEtablissement           : état courant des ~13 M d'établissements (créations)
  - StockUniteLegale             : l'entreprise porteuse (categorieEntreprise = PME/ETI/GE)
  - StockEtablissementHistorique : valeurs historisées (reconstitution des CESSATIONS)

Le format parquet est privilégié : plus compact au transfert, et DuckDB le lit sans
décompression en ne matérialisant que les colonnes projetées.

Usage :
    python ingestion/download.py --list     # afficher les ressources disponibles
    python ingestion/download.py            # télécharger les trois fichiers
    python ingestion/download.py --format zip
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"

DATASET_ID = "5b7ffc618b4c4169d30727e0"  # Base Sirene des entreprises et de leurs etablissements
CATALOGUE_API = f"https://www.data.gouv.fr/api/1/datasets/{DATASET_ID}/"
URL_STABLE = "https://www.data.gouv.fr/api/1/datasets/r/{id}"

FICHIERS = ["StockEtablissement", "StockUniteLegale", "StockEtablissementHistorique"]

HEADERS = {"User-Agent": "sirene-pipeline/1.0"}


def lire_catalogue() -> list[dict]:
    """Recupere la liste des ressources publiees pour le jeu de donnees Sirene."""
    req = Request(CATALOGUE_API, headers=HEADERS)
    with urlopen(req, timeout=60) as resp:
        return json.load(resp).get("resources", [])


def nom_fichier(titre: str) -> str | None:
    """
    Extrait le nom canonique du fichier depuis le titre de la ressource.

    Les titres suivent la forme "Sirene : Fichier StockEtablissement du 01 ...".
    On compare le nom complet et non un simple `in`, sans quoi "StockEtablissement"
    capturerait aussi "StockEtablissementHistorique".
    """
    match = re.search(r"(Stock[A-Za-z]+)", titre or "")
    return match.group(1) if match else None


def resoudre(resources: list[dict], format_voulu: str) -> dict[str, dict]:
    """Associe chaque fichier recherche a sa ressource, dans le format demande."""
    trouves: dict[str, dict] = {}
    for r in resources:
        nom = nom_fichier(r.get("title", ""))
        if nom in FICHIERS and (r.get("format") or "").lower() == format_voulu:
            # Le catalogue peut porter plusieurs millesimes : on garde le plus recent.
            precedent = trouves.get(nom)
            if precedent is None or (r.get("last_modified") or "") > (precedent.get("last_modified") or ""):
                trouves[nom] = r
    return trouves


def download(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"  deja present, ignore : {dest.name} ({dest.stat().st_size / 1e9:.2f} Go)")
        return

    tmp = dest.with_suffix(dest.suffix + ".part")
    req = Request(url, headers=HEADERS)
    start = time.time()

    with urlopen(req, timeout=120) as resp, open(tmp, "wb") as f:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while chunk := resp.read(1 << 20):  # 1 Mo
            f.write(chunk)
            done += len(chunk)
            if total:
                pct = 100 * done / total
                vitesse = done / 1e6 / max(time.time() - start, 0.1)
                print(f"\r  {dest.name} {pct:5.1f}%  {done/1e9:.2f}/{total/1e9:.2f} Go  "
                      f"{vitesse:.1f} Mo/s", end="", flush=True)
            else:
                print(f"\r  {dest.name} {done/1e9:.2f} Go", end="", flush=True)

    tmp.rename(dest)
    print(f"\r  {dest.name} termine en {time.time() - start:.0f}s" + " " * 30)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", default="parquet", choices=["parquet", "zip"])
    parser.add_argument("--only", choices=FICHIERS)
    parser.add_argument("--list", action="store_true",
                        help="afficher les ressources du catalogue et sortir")
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)

    print(f"Lecture du catalogue data.gouv ({DATASET_ID})...")
    try:
        resources = lire_catalogue()
    except Exception as exc:  # noqa: BLE001
        print(f"ECHEC de l'appel au catalogue : {exc}")
        return 1
    print(f"  {len(resources)} ressources publiees\n")

    if args.list:
        for r in resources:
            print(f"  [{(r.get('format') or '?'):8}] {r.get('title')}")
            print(f"             {URL_STABLE.format(id=r['id'])}")
        return 0

    trouves = resoudre(resources, args.format)
    manquants = [f for f in FICHIERS if f not in trouves]
    if manquants:
        print(f"Non trouves au format {args.format} : {', '.join(manquants)}")
        print("Relance avec --list pour inspecter les titres reellement publies.")
        if not trouves:
            return 1

    # Les URL resolues sont conservees : le mode echantillon de load_duckdb.py les
    # reutilise pour lire le parquet a distance sans attendre le telechargement.
    (DATA_DIR / "resources.json").write_text(json.dumps(
        {nom: URL_STABLE.format(id=r["id"]) for nom, r in trouves.items()},
        indent=2, ensure_ascii=False), encoding="utf-8")

    cibles = [args.only] if args.only else FICHIERS
    for nom in cibles:
        r = trouves.get(nom)
        if r is None:
            continue
        taille = r.get("filesize")
        suffixe = f" - {taille / 1e9:.2f} Go" if taille else ""
        print(f"[{nom}]{suffixe}")
        try:
            download(URL_STABLE.format(id=r["id"]), DATA_DIR / f"{nom}.{args.format}")
        except Exception as exc:  # noqa: BLE001
            print(f"\n  ECHEC : {exc}")
            return 1

    print("\nTelechargement termine. Enchaine avec : python ingestion/load_duckdb.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
