{{ config(materialized='view') }}

-- L'unite legale porte categorieEntreprise (PME / ETI / GE), absente au niveau
-- etablissement : c'est la seule voie pour segmenter la demographie par taille.

with source as (

    select * from {{ source('sirene', 'unites_legales') }}

),

renamed as (

    select
        cast(siren as varchar)                          as siren,
        nullif(trim(cast(statutDiffusionUniteLegale as varchar)), '') as statut_diffusion,
        try_cast(dateCreationUniteLegale as date)       as date_creation,
        nullif(trim(cast(categorieEntreprise as varchar)), '')        as categorie_entreprise,
        try_cast(anneeCategorieEntreprise as integer)   as annee_categorie_entreprise,
        nullif(trim(cast(categorieJuridiqueUniteLegale as varchar)), '') as categorie_juridique,
        nullif(trim(cast(etatAdministratifUniteLegale as varchar)), '')  as etat_administratif,
        nullif(trim(cast(activitePrincipaleUniteLegale as varchar)), '') as code_ape,
        nullif(trim(cast(activitePrincipaleNAF25UniteLegale as varchar)), '') as code_ape_naf25,
        nullif(trim(cast(denominationUniteLegale as varchar)), '')     as denomination,
        nullif(trim(cast(trancheEffectifsUniteLegale as varchar)), '') as tranche_effectifs
    from source

)

select * from renamed
where statut_diffusion is distinct from 'P'
