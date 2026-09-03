"""
Jeu de donnees synthetique reproduisant le schema des fichiers stock SIRENE.

Sert a deux choses :
  - faire tourner et deboguer toute la chaine dbt pendant que les vrais fichiers
    telechargent (le pipeline est valide avant la premiere ligne reelle) ;
  - servir de fixture reproductible si tu ajoutes des tests plus tard.

Les cas tordus du repertoire reel sont volontairement injectes : SIRET a zero de
tete, commune corse (2A), commune DOM (974), date de creation nulle, date future,
unite en diffusion partielle ('P'), etablissement sans unite legale appariee.

    python ingestion/make_fixtures.py
"""

from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "sirene.duckdb"

random.seed(42)

COMMUNES = ["75056", "69123", "13055", "2A004", "97411", "59350", "33063", "31555"]
APE = ["62.01Z", "56.10A", "43.34Z", "68.20B", "47.11D", "86.21Z", "01.11Z", "99.00Z"]
CATEGORIES = ["PME", "PME", "PME", "ETI", "GE", None]

N_ETABLISSEMENTS = 5000


def main() -> None:
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    etabs, uls, hist = [], [], []
    aujourd_hui = date.today()

    for i in range(N_ETABLISSEMENTS):
        siren = f"{i:09d}"           # zeros de tete conserves
        siret = siren + f"{i % 100:05d}"
        commune = random.choice(COMMUNES)
        ape = random.choice(APE)

        # Date de creation etalee sur 6 ans, avec quelques cas degrades.
        if i % 500 == 0:
            creation = None                                   # date manquante
        elif i % 777 == 0:
            creation = aujourd_hui + timedelta(days=90)       # date future aberrante
        else:
            creation = aujourd_hui - timedelta(days=random.randint(0, 2200))

        ferme = i % 4 == 0
        statut = "P" if i % 250 == 0 else "O"                 # diffusion partielle

        etabs.append((
            siren, f"{i % 100:05d}", siret, statut,
            creation.isoformat() if creation else None,
            "11", i % 3 == 0, commune, commune[:2] + "000",
            "COMMUNE TEST", (creation or aujourd_hui).isoformat(),
            "F" if ferme else "A", ape, "NAFRev2", ape.replace(".", "")[:4] + "A", "O",
        ))

        # 1 etablissement sur 10 n'a pas d'unite legale appariee (SIREN orphelin).
        if i % 10 != 0:
            uls.append((
                siren, statut,
                creation.isoformat() if creation else None,
                random.choice(CATEGORIES), 2025, "5710",
                "C" if ferme else "A", ape, ape.replace(".", "")[:4] + "A",
                f"ENTREPRISE TEST {i}", "11",
            ))

        # Historique : periode d'ouverture, puis periode de fermeture si ferme.
        hist.append((siren, f"{i % 100:05d}", siret,
                     (creation or aujourd_hui).isoformat(), None, "A", True, ape, False))
        if ferme:
            fermeture = aujourd_hui - timedelta(days=random.randint(0, 900))
            hist.append((siren, f"{i % 100:05d}", siret,
                         fermeture.isoformat(), None, "F", True, ape, False))

    con.execute("""
        CREATE OR REPLACE TABLE raw.etablissements (
            siren VARCHAR, nic VARCHAR, siret VARCHAR,
            statutDiffusionEtablissement VARCHAR,
            dateCreationEtablissement VARCHAR,
            trancheEffectifsEtablissement VARCHAR,
            etablissementSiege BOOLEAN,
            codeCommuneEtablissement VARCHAR,
            codePostalEtablissement VARCHAR,
            libelleCommuneEtablissement VARCHAR,
            dateDebut VARCHAR,
            etatAdministratifEtablissement VARCHAR,
            activitePrincipaleEtablissement VARCHAR,
            nomenclatureActivitePrincipaleEtablissement VARCHAR,
            activitePrincipaleNAF25Etablissement VARCHAR,
            caractereEmployeurEtablissement VARCHAR)
    """)
    con.executemany("INSERT INTO raw.etablissements VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", etabs)

    con.execute("""
        CREATE OR REPLACE TABLE raw.unites_legales (
            siren VARCHAR, statutDiffusionUniteLegale VARCHAR,
            dateCreationUniteLegale VARCHAR, categorieEntreprise VARCHAR,
            anneeCategorieEntreprise INTEGER, categorieJuridiqueUniteLegale VARCHAR,
            etatAdministratifUniteLegale VARCHAR, activitePrincipaleUniteLegale VARCHAR,
            activitePrincipaleNAF25UniteLegale VARCHAR, denominationUniteLegale VARCHAR,
            trancheEffectifsUniteLegale VARCHAR)
    """)
    con.executemany("INSERT INTO raw.unites_legales VALUES (?,?,?,?,?,?,?,?,?,?,?)", uls)

    con.execute("""
        CREATE OR REPLACE TABLE raw.etablissements_historique (
            siren VARCHAR, nic VARCHAR, siret VARCHAR,
            dateDebut VARCHAR, dateFin VARCHAR,
            etatAdministratifEtablissement VARCHAR,
            changementEtatAdministratifEtablissement BOOLEAN,
            activitePrincipaleEtablissement VARCHAR,
            changementActivitePrincipaleEtablissement BOOLEAN)
    """)
    con.executemany("INSERT INTO raw.etablissements_historique VALUES (?,?,?,?,?,?,?,?,?)", hist)

    for t in ("etablissements", "unites_legales", "etablissements_historique"):
        n = con.execute(f"SELECT count(*) FROM raw.{t}").fetchone()[0]
        print(f"raw.{t} : {n} lignes")
    con.close()


if __name__ == "__main__":
    main()
