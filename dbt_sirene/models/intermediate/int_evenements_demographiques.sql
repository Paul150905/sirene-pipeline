{{ config(materialized='table') }}

-- Unification des creations et des cessations en une seule table evenementielle :
-- un evenement par ligne, meme grain, memes attributs. C'est ce modele qui rend
-- la table de faits triviale a construire et le solde net coherent par construction.
--
-- Creations  : dateCreationEtablissement du fichier stock (etat courant).
-- Cessations : reconstituees depuis les valeurs historisees. Chaque ligne dont
--              l'etat vaut 'F' avec un changement d'etat marque a vrai correspond
--              a une fermeture datee par dateDebut. Un etablissement rouvert puis
--              referme genere deux evenements, ce qui est le comportement voulu.

with etablissements as (

    select * from {{ ref('int_etablissements_enrichis') }}

),

historique as (

    select * from {{ ref('stg_etablissements_historique') }}

),

creations as (

    select
        siret,
        siren,
        'CREATION'      as type_evenement,
        date_creation   as date_evenement,
        code_departement,
        libelle_departement,
        libelle_region,
        code_section,
        libelle_section,
        categorie_entreprise
    from etablissements
    where date_creation is not null
      -- Bornes de vraisemblance : le repertoire porte des dates sentinelles
      -- anciennes et, plus rarement, des dates futures.
      and date_creation >= date '1900-01-01'
      and date_creation <= current_date

),

cessations as (

    select
        h.siret,
        h.siren,
        'CESSATION'     as type_evenement,
        h.date_debut    as date_evenement,
        e.code_departement,
        e.libelle_departement,
        e.libelle_region,
        e.code_section,
        e.libelle_section,
        e.categorie_entreprise
    from historique h
    -- Jointure interne assumee : les etablissements exclus au staging (diffusion
    -- partielle) ne doivent pas reapparaitre par la porte de l'historique.
    inner join etablissements e on h.siret = e.siret
    where h.etat_administratif = 'F'
      and h.changement_etat
      and h.date_debut is not null
      and h.date_debut >= date '1900-01-01'
      and h.date_debut <= current_date

)

select * from creations
union all
select * from cessations
