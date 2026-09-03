{{ config(materialized='view') }}

-- Le fichier stock ne donne que l'etat COURANT : il ne permet pas de dater une
-- fermeture. Le fichier des valeurs historisees porte une ligne par periode de
-- validite ; la transition vers l'etat 'F' y est datee par dateDebut.
-- C'est la source des cessations, et la moitie du sujet du projet.

with source as (

    select * from {{ source('sirene', 'etablissements_historique') }}

),

renamed as (

    select
        cast(siret as varchar)                      as siret,
        cast(siren as varchar)                      as siren,
        try_cast(dateDebut as date)                 as date_debut,
        try_cast(dateFin as date)                   as date_fin,
        nullif(trim(cast(etatAdministratifEtablissement as varchar)), '') as etat_administratif,
        lower(cast(changementEtatAdministratifEtablissement as varchar)) in ('true', '1')
                                                    as changement_etat,
        nullif(trim(cast(activitePrincipaleEtablissement as varchar)), '') as code_ape,
        lower(cast(changementActivitePrincipaleEtablissement as varchar)) in ('true', '1')
                                                    as changement_ape
    from source

)

select * from renamed
