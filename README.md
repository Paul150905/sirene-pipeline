# Démographie des entreprises françaises — pipeline analytique end-to-end

**Question traitée :** où la création d'entreprises accélère-t-elle en France, par secteur d'activité et par département ?

**Source :** fichiers stock mensuels du répertoire SIRENE (INSEE, data.gouv.fr) — environ 13 millions d'établissements, 95 variables.

**Stack :** Python (ingestion) → DuckDB (stockage analytique) → dbt (modélisation en trois couches) → Streamlit (restitution).

```
ingestion/          scripts de téléchargement et de chargement
dbt_sirene/         projet dbt : staging / intermediate / marts
app/                dashboard Streamlit
data/               fichiers sources (non versionnés)
sirene.duckdb       base analytique (non versionnée)
```

## Démarrage

```bash
pip install -r requirements.txt

make fixtures     # jeu synthétique : valide toute la chaîne en 30 secondes
make build        # dbt seed + dbt run
make test         # suite de tests
make dashboard    # Streamlit

# Puis sur les données réelles :
make download     # ~5 Go, à lancer en premier et laisser tourner
make load         # chargement dans DuckDB
make build test
```

## Décisions d'architecture

**Fichiers stock plutôt qu'API.** L'API Sirene est conçue pour l'interrogation unitaire ou multicritère : valider un SIRET, retrouver un siège. Compter des créations sur 13 millions d'établissements par ce canal représenterait des jours de requêtes pour un résultat que le fichier stock donne en une lecture. L'API reste pertinente pour un rafraîchissement incrémental, via `dateDernierTraitementEtablissement`.

**DuckDB plutôt que Postgres.** Traitement analytique sur des dizaines de millions de lignes, en local, sans serveur à administrer. Le moteur lit le parquet directement, ne matérialise que les colonnes projetées et exécute les agrégations en colonnaire. Un Postgres exigerait une instance, un chargement complet et de l'indexation pour un gain nul sur des requêtes qui balaient toute la table.

**Jamais de pandas à l'ingestion.** `pd.read_csv()` sur 12 Go décompressés sature la mémoire. DuckDB lit la source et écrit la table ; Python ne fait qu'orchestrer.

**Trois couches dbt.** `staging` type et renomme sans logique métier ; `intermediate` joint et enrichit ; `marts` agrège au grain de restitution. Chaque couche a une responsabilité unique, ce qui rend un bug localisable à une couche.

## Le point difficile : reconstituer les cessations

Le fichier stock ne contient que l'**état courant** de chaque établissement. Il donne la date de création, mais aucune date de fermeture : un établissement fermé porte simplement `etatAdministratifEtablissement = 'F'`, sans indication du moment.

Les cessations sont reconstituées depuis le fichier des **valeurs historisées**, qui porte une ligne par période de validité. Chaque ligne dont l'état vaut `F` avec `changementEtatAdministratifEtablissement` à vrai correspond à une transition A → F, datée par `dateDebut`. Un établissement rouvert puis refermé génère deux événements, ce qui est le comportement voulu.

`int_evenements_demographiques` unifie créations et cessations en une seule table événementielle, au même grain et avec les mêmes attributs. La table de faits en découle par simple agrégation, et le solde net est cohérent par construction plutôt que par recollement de deux calculs séparés.

## Grain de la table de faits

`fct_demographie_mensuelle` : **un enregistrement par mois × département × section NAF × catégorie d'entreprise.**

La clé de substitution `cle_fait` dérive directement de ce grain, ce qui rend le test d'unicité vérifiable plutôt que déclaratif.

## Qualité des données

Six pièges traités explicitement, chacun documenté dans le code :

| Piège | Traitement |
|---|---|
| SIRET lu en integer | Cast forcé en VARCHAR à l'ingestion — sinon les zéros de tête disparaissent et toutes les jointures cassent |
| Départements DOM et Corse | `left(code, 3)` pour les codes commençant par 97, `left(code, 2)` sinon ; 2A/2B sortent correctement |
| Cessations absentes du stock | Reconstituées depuis les valeurs historisées (voir ci-dessus) |
| Volumétrie | Lecture parquet par DuckDB, projection de 16 colonnes sur 95 |
| Dates de création aberrantes | Bornes de vraisemblance dans `int_evenements_demographiques`, test dédié en surveillance |
| RGPD | Unités en diffusion partielle (`statutDiffusion = 'P'`) exclues dès le staging |

Sur le RGPD, l'arbitrage mérite d'être explicité : exclure ces unités écarte une fraction du champ des comptages agrégés. L'alternative consisterait à les conserver pour le dénombrement et à ne masquer que les attributs nominatifs. L'exclusion a été retenue pour sa lisibilité et parce que la fraction concernée est faible ; le filtre est isolé sur une seule ligne de chaque modèle de staging, donc réversible.

## Tests

```
dbt test    # 28 tests
```

- `unique` et `not_null` sur les clés primaires de chaque couche
- `accepted_values` sur l'état administratif et la catégorie d'entreprise
- `relationships` de la table de faits vers ses deux dimensions
- **réconciliation** : le total des créations du mart doit égaler le compte de la couche intermediate. C'est le seul test qui attrape une vraie erreur de modélisation — une jointure qui duplique des lignes passe inaperçue des tests d'unicité mais fait diverger ces deux comptes.
- vraisemblance des dates, en `warn` : l'anomalie vient de la source, elle est déjà neutralisée en aval, mais elle est surveillée à chaque exécution.

## Documentation

```
dbt docs generate && dbt docs serve
```

Le graphe de lignage montre le chemin complet de chaque source vers la table de faits.

## Limites connues

- Le stock ne conserve qu'une image mensuelle : les créations suivies de fermeture avant publication du fichier n'apparaissent pas.
- La section NAF est calculée en NAF Rev2. Le code NAF2025, diffusé par anticipation par l'INSEE avant la bascule de janvier 2027, est conservé en colonne mais pas encore utilisé pour le sectionnement.
- Le stock d'établissements actifs des dimensions est une photographie à la date du fichier, pas une série historique.
