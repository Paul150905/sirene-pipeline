"""Génère les deux seeds de référence du projet (exécuté une seule fois)."""

import csv
from pathlib import Path

SEEDS = Path(__file__).resolve().parents[1] / "dbt_sirene" / "seeds"

DEPARTEMENTS = [
    ("01", "Ain", "Auvergne-Rhône-Alpes"), ("02", "Aisne", "Hauts-de-France"),
    ("03", "Allier", "Auvergne-Rhône-Alpes"), ("04", "Alpes-de-Haute-Provence", "Provence-Alpes-Côte d'Azur"),
    ("05", "Hautes-Alpes", "Provence-Alpes-Côte d'Azur"), ("06", "Alpes-Maritimes", "Provence-Alpes-Côte d'Azur"),
    ("07", "Ardèche", "Auvergne-Rhône-Alpes"), ("08", "Ardennes", "Grand Est"),
    ("09", "Ariège", "Occitanie"), ("10", "Aube", "Grand Est"),
    ("11", "Aude", "Occitanie"), ("12", "Aveyron", "Occitanie"),
    ("13", "Bouches-du-Rhône", "Provence-Alpes-Côte d'Azur"), ("14", "Calvados", "Normandie"),
    ("15", "Cantal", "Auvergne-Rhône-Alpes"), ("16", "Charente", "Nouvelle-Aquitaine"),
    ("17", "Charente-Maritime", "Nouvelle-Aquitaine"), ("18", "Cher", "Centre-Val de Loire"),
    ("19", "Corrèze", "Nouvelle-Aquitaine"), ("2A", "Corse-du-Sud", "Corse"),
    ("2B", "Haute-Corse", "Corse"), ("21", "Côte-d'Or", "Bourgogne-Franche-Comté"),
    ("22", "Côtes-d'Armor", "Bretagne"), ("23", "Creuse", "Nouvelle-Aquitaine"),
    ("24", "Dordogne", "Nouvelle-Aquitaine"), ("25", "Doubs", "Bourgogne-Franche-Comté"),
    ("26", "Drôme", "Auvergne-Rhône-Alpes"), ("27", "Eure", "Normandie"),
    ("28", "Eure-et-Loir", "Centre-Val de Loire"), ("29", "Finistère", "Bretagne"),
    ("30", "Gard", "Occitanie"), ("31", "Haute-Garonne", "Occitanie"),
    ("32", "Gers", "Occitanie"), ("33", "Gironde", "Nouvelle-Aquitaine"),
    ("34", "Hérault", "Occitanie"), ("35", "Ille-et-Vilaine", "Bretagne"),
    ("36", "Indre", "Centre-Val de Loire"), ("37", "Indre-et-Loire", "Centre-Val de Loire"),
    ("38", "Isère", "Auvergne-Rhône-Alpes"), ("39", "Jura", "Bourgogne-Franche-Comté"),
    ("40", "Landes", "Nouvelle-Aquitaine"), ("41", "Loir-et-Cher", "Centre-Val de Loire"),
    ("42", "Loire", "Auvergne-Rhône-Alpes"), ("43", "Haute-Loire", "Auvergne-Rhône-Alpes"),
    ("44", "Loire-Atlantique", "Pays de la Loire"), ("45", "Loiret", "Centre-Val de Loire"),
    ("46", "Lot", "Occitanie"), ("47", "Lot-et-Garonne", "Nouvelle-Aquitaine"),
    ("48", "Lozère", "Occitanie"), ("49", "Maine-et-Loire", "Pays de la Loire"),
    ("50", "Manche", "Normandie"), ("51", "Marne", "Grand Est"),
    ("52", "Haute-Marne", "Grand Est"), ("53", "Mayenne", "Pays de la Loire"),
    ("54", "Meurthe-et-Moselle", "Grand Est"), ("55", "Meuse", "Grand Est"),
    ("56", "Morbihan", "Bretagne"), ("57", "Moselle", "Grand Est"),
    ("58", "Nièvre", "Bourgogne-Franche-Comté"), ("59", "Nord", "Hauts-de-France"),
    ("60", "Oise", "Hauts-de-France"), ("61", "Orne", "Normandie"),
    ("62", "Pas-de-Calais", "Hauts-de-France"), ("63", "Puy-de-Dôme", "Auvergne-Rhône-Alpes"),
    ("64", "Pyrénées-Atlantiques", "Nouvelle-Aquitaine"), ("65", "Hautes-Pyrénées", "Occitanie"),
    ("66", "Pyrénées-Orientales", "Occitanie"), ("67", "Bas-Rhin", "Grand Est"),
    ("68", "Haut-Rhin", "Grand Est"), ("69", "Rhône", "Auvergne-Rhône-Alpes"),
    ("70", "Haute-Saône", "Bourgogne-Franche-Comté"), ("71", "Saône-et-Loire", "Bourgogne-Franche-Comté"),
    ("72", "Sarthe", "Pays de la Loire"), ("73", "Savoie", "Auvergne-Rhône-Alpes"),
    ("74", "Haute-Savoie", "Auvergne-Rhône-Alpes"), ("75", "Paris", "Île-de-France"),
    ("76", "Seine-Maritime", "Normandie"), ("77", "Seine-et-Marne", "Île-de-France"),
    ("78", "Yvelines", "Île-de-France"), ("79", "Deux-Sèvres", "Nouvelle-Aquitaine"),
    ("80", "Somme", "Hauts-de-France"), ("81", "Tarn", "Occitanie"),
    ("82", "Tarn-et-Garonne", "Occitanie"), ("83", "Var", "Provence-Alpes-Côte d'Azur"),
    ("84", "Vaucluse", "Provence-Alpes-Côte d'Azur"), ("85", "Vendée", "Pays de la Loire"),
    ("86", "Vienne", "Nouvelle-Aquitaine"), ("87", "Haute-Vienne", "Nouvelle-Aquitaine"),
    ("88", "Vosges", "Grand Est"), ("89", "Yonne", "Bourgogne-Franche-Comté"),
    ("90", "Territoire de Belfort", "Bourgogne-Franche-Comté"), ("91", "Essonne", "Île-de-France"),
    ("92", "Hauts-de-Seine", "Île-de-France"), ("93", "Seine-Saint-Denis", "Île-de-France"),
    ("94", "Val-de-Marne", "Île-de-France"), ("95", "Val-d'Oise", "Île-de-France"),
    ("971", "Guadeloupe", "Guadeloupe"), ("972", "Martinique", "Martinique"),
    ("973", "Guyane", "Guyane"), ("974", "La Réunion", "La Réunion"),
    ("976", "Mayotte", "Mayotte"),
    # Collectivites d'outre-mer : absentes de la liste des departements au sens
    # strict, mais bien presentes dans SIRENE. Les omettre laisse des dizaines de
    # milliers d'evenements sans rattachement geographique.
    ("975", "Saint-Pierre-et-Miquelon", "Saint-Pierre-et-Miquelon"),
    ("977", "Saint-Barthelemy", "Saint-Barthelemy"),
    ("978", "Saint-Martin", "Saint-Martin"),
    ("984", "Terres australes et antarctiques", "Terres australes et antarctiques"),
    ("986", "Wallis-et-Futuna", "Wallis-et-Futuna"),
    ("987", "Polynesie francaise", "Polynesie francaise"),
    ("988", "Nouvelle-Caledonie", "Nouvelle-Caledonie"),
    ("989", "Ile de Clipperton", "Ile de Clipperton"),
]

# Sections NAF Rev2 : bornes de divisions (2 premiers chiffres du code APE).
SECTIONS_NAF = [
    ("A", 1, 3, "Agriculture, sylviculture et pêche"),
    ("B", 5, 9, "Industries extractives"),
    ("C", 10, 33, "Industrie manufacturière"),
    ("D", 35, 35, "Production et distribution d'électricité, gaz, vapeur"),
    ("E", 36, 39, "Eau, assainissement, gestion des déchets"),
    ("F", 41, 43, "Construction"),
    ("G", 45, 47, "Commerce, réparation d'automobiles et de motocycles"),
    ("H", 49, 53, "Transports et entreposage"),
    ("I", 55, 56, "Hébergement et restauration"),
    ("J", 58, 63, "Information et communication"),
    ("K", 64, 66, "Activités financières et d'assurance"),
    ("L", 68, 68, "Activités immobilières"),
    ("M", 69, 75, "Activités spécialisées, scientifiques et techniques"),
    ("N", 77, 82, "Activités de services administratifs et de soutien"),
    ("O", 84, 84, "Administration publique"),
    ("P", 85, 85, "Enseignement"),
    ("Q", 86, 88, "Santé humaine et action sociale"),
    ("R", 90, 93, "Arts, spectacles et activités récréatives"),
    ("S", 94, 96, "Autres activités de services"),
    ("T", 97, 98, "Activités des ménages en tant qu'employeurs"),
    ("U", 99, 99, "Activités extra-territoriales"),
]


def main() -> None:
    SEEDS.mkdir(parents=True, exist_ok=True)

    with open(SEEDS / "ref_departements.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code_departement", "libelle_departement", "libelle_region"])
        w.writerows(DEPARTEMENTS)

    with open(SEEDS / "ref_naf_sections.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code_section", "division_min", "division_max", "libelle_section"])
        w.writerows(SECTIONS_NAF)

    print(f"{len(DEPARTEMENTS)} départements et {len(SECTIONS_NAF)} sections NAF écrits dans {SEEDS}")


if __name__ == "__main__":
    main()
