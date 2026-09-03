{{ config(materialized='table') }}

-- Dimension geographique, enrichie du stock d'etablissements actifs, qui sert de
-- denominateur pour comparer des departements de tailles tres differentes.

with referentiel as (

    select * from {{ ref('ref_departements') }}

),

-- Codes geographiques presents dans les donnees mais absents du referentiel :
-- codes errones du repertoire, ou territoires apparus depuis. On les fait figurer
-- explicitement plutot que de les perdre dans une jointure non aboutie. La
-- dimension reste ainsi exhaustive et l'anomalie reste visible.
codes_non_references as (

    select distinct
        code_departement,
        'Code non reference (' || code_departement || ')' as libelle_departement,
        'Non reference'                                   as libelle_region
    from {{ ref('int_etablissements_enrichis') }}
    where code_departement is not null
      and code_departement not in (select code_departement from referentiel)

),

departements as (

    select * from referentiel
    union all
    select * from codes_non_references

),

stock as (

    select
        code_departement,
        count(*)                                                  as nb_etablissements,
        count(*) filter (where etat_administratif = 'A')           as nb_etablissements_actifs
    from {{ ref('int_etablissements_enrichis') }}
    where code_departement is not null
    group by 1

)

select
    d.code_departement,
    d.libelle_departement,
    d.libelle_region,
    coalesce(s.nb_etablissements, 0)        as nb_etablissements,
    coalesce(s.nb_etablissements_actifs, 0) as nb_etablissements_actifs
from departements d
left join stock s on d.code_departement = s.code_departement
