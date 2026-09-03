{{ config(materialized='table') }}

-- Dimension sectorielle au niveau section NAF Rev2, avec le stock actif associe.
-- La ligne 'ZZ' absorbe les etablissements dont le code APE est absent ou hors
-- nomenclature : elle rend visible ce qui serait autrement perdu dans un NULL.

with sections as (

    select
        code_section,
        libelle_section,
        division_min,
        division_max
    from {{ ref('ref_naf_sections') }}

    union all

    select 'ZZ', 'Section non determinee', null, null

),

stock as (

    select
        coalesce(code_section, 'ZZ')                     as code_section,
        count(*)                                         as nb_etablissements,
        count(*) filter (where etat_administratif = 'A') as nb_etablissements_actifs
    from {{ ref('int_etablissements_enrichis') }}
    group by 1

)

select
    s.code_section,
    s.libelle_section,
    s.division_min,
    s.division_max,
    coalesce(k.nb_etablissements, 0)        as nb_etablissements,
    coalesce(k.nb_etablissements_actifs, 0) as nb_etablissements_actifs
from sections s
left join stock k on s.code_section = k.code_section
