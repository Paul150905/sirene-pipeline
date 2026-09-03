{{ config(materialized='table') }}

-- Table de faits. GRAIN : un enregistrement par
--   mois x departement x section NAF x categorie d'entreprise.
-- Formuler ce grain explicitement est ce qu'on attend d'un modele analytique :
-- il fixe ce qu'une ligne represente et rend le test d'unicite verifiable.

with evenements as (

    select * from {{ ref('int_evenements_demographiques') }}
    where code_departement is not null

),

agrege as (

    select
        date_trunc('month', date_evenement)                     as mois,
        code_departement,
        libelle_departement,
        libelle_region,
        coalesce(code_section, 'ZZ')                            as code_section,
        coalesce(libelle_section, 'Section non determinee')     as libelle_section,
        categorie_entreprise,
        count(*) filter (where type_evenement = 'CREATION')     as nb_creations,
        count(*) filter (where type_evenement = 'CESSATION')    as nb_cessations
    from evenements
    group by 1, 2, 3, 4, 5, 6, 7

)

select
    -- Cle de substitution derivee du grain : rend le test d'unicite direct.
    md5(cast(mois as varchar) || code_departement || code_section || categorie_entreprise) as cle_fait,
    mois,
    year(mois)                              as annee,
    month(mois)                             as numero_mois,
    code_departement,
    libelle_departement,
    libelle_region,
    code_section,
    libelle_section,
    categorie_entreprise,
    nb_creations,
    nb_cessations,
    nb_creations - nb_cessations            as solde_net,
    -- Taux de renouvellement : cessations rapportees aux creations du meme mois.
    -- NULL quand aucune creation, plutot que zero, pour ne pas fausser les moyennes.
    case when nb_creations > 0
         then round(nb_cessations * 1.0 / nb_creations, 3)
    end                                     as ratio_cessations_creations
from agrege
