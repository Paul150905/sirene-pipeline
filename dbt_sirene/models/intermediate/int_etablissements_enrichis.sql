{{ config(materialized='table') }}

-- Table de travail centrale : un etablissement, ses attributs geographiques et
-- sectoriels normalises, et la categorie d'entreprise heritee de l'unite legale.
-- Tout le reste du projet lit ce modele plutot que le staging.

with etablissements as (

    select * from {{ ref('stg_etablissements') }}

),

unites_legales as (

    select
        siren,
        categorie_entreprise,
        categorie_juridique,
        denomination,
        etat_administratif as etat_administratif_ul
    from {{ ref('stg_unites_legales') }}

),

departements as (

    select * from {{ ref('ref_departements') }}

),

sections as (

    select * from {{ ref('ref_naf_sections') }}

)

select
    e.siret,
    e.siren,
    e.date_creation,
    e.etat_administratif,
    e.is_siege,
    e.code_commune,
    e.libelle_commune,
    e.code_departement,
    d.libelle_departement,
    d.libelle_region,
    e.code_ape,
    e.code_ape_naf25,
    e.division_naf,
    s.code_section,
    s.libelle_section,
    e.tranche_effectifs,
    -- Une unite legale non appariee laisse la categorie a NULL : on la qualifie
    -- explicitement plutot que de la laisser silencieuse dans les agregats.
    coalesce(u.categorie_entreprise, 'NON_RENSEIGNE') as categorie_entreprise,
    u.categorie_juridique,
    u.denomination,
    u.etat_administratif_ul
from etablissements e
left join unites_legales u on e.siren = u.siren
left join departements   d on e.code_departement = d.code_departement
left join sections       s on e.division_naf between s.division_min and s.division_max
