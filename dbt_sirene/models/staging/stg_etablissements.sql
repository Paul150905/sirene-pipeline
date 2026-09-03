{{ config(materialized='view') }}

-- Couche staging : cast, renommage, aucune logique métier.
-- Deux décisions structurantes :
--   1. SIRET et SIREN en VARCHAR. Un cast integer perd les zeros de tete et
--      casse toutes les jointures aval.
--   2. Exclusion des unites en diffusion partielle (statut 'P', RGPD) : ces unites
--      font l'objet d'une opposition a la rediffusion de leurs donnees.
--      Variante : les conserver pour les comptages agreges et masquer les seuls
--      attributs nominatifs. Arbitrage documente dans le README.

with source as (

    select * from {{ source('sirene', 'etablissements') }}

),

renamed as (

    select
        cast(siret as varchar)                              as siret,
        cast(siren as varchar)                              as siren,
        nullif(trim(cast(statutDiffusionEtablissement as varchar)), '') as statut_diffusion,
        try_cast(dateCreationEtablissement as date)         as date_creation,
        try_cast(dateDebut as date)                         as date_debut_periode,
        nullif(trim(cast(etatAdministratifEtablissement as varchar)), '') as etat_administratif,
        lower(cast(etablissementSiege as varchar)) in ('true', '1') as is_siege,
        nullif(trim(cast(codeCommuneEtablissement as varchar)), '')  as code_commune,
        nullif(trim(cast(codePostalEtablissement as varchar)), '')   as code_postal,
        nullif(trim(cast(libelleCommuneEtablissement as varchar)), '') as libelle_commune,
        nullif(trim(cast(activitePrincipaleEtablissement as varchar)), '') as code_ape,
        nullif(trim(cast(nomenclatureActivitePrincipaleEtablissement as varchar)), '') as nomenclature_ape,
        nullif(trim(cast(activitePrincipaleNAF25Etablissement as varchar)), '') as code_ape_naf25,
        nullif(trim(cast(trancheEffectifsEtablissement as varchar)), '') as tranche_effectifs,
        nullif(trim(cast(caractereEmployeurEtablissement as varchar)), '') as caractere_employeur
    from source

),

final as (

    select
        *,
        -- Departement : les DOM occupent 3 caracteres (971 a 976) ; la Corse
        -- utilise 2A / 2B, qui sortent correctement d'un left(code, 2).
        case
            when code_commune is null then null
            when left(code_commune, 2) = '97' then left(code_commune, 3)
            else left(code_commune, 2)
        end as code_departement,

        -- Division NAF : deux premiers chiffres du code APE. Le point est retire
        -- pour absorber les deux ecritures presentes dans le repertoire.
        try_cast(left(replace(code_ape, '.', ''), 2) as integer) as division_naf
    from renamed

)

select * from final
where statut_diffusion is distinct from 'P'
