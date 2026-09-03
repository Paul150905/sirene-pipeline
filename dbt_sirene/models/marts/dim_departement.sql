{{ config(materialized='table') }}

-- Dimension geographique, enrichie du stock d'etablissements actifs, qui sert de
-- denominateur pour comparer des departements de tailles tres differentes.

with departements as (

    select * from {{ ref('ref_departements') }}

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
