-- Test de reconciliation : le total des creations de la table de faits doit egaler
-- le nombre d'evenements de creation de la couche intermediate, une fois retires
-- les etablissements sans departement (exclus du mart, et seulement ceux-la).
--
-- C'est le seul test du projet qui attrape une vraie erreur de modelisation :
-- une jointure qui duplique des lignes ou un filtre involontaire passent inapercus
-- des tests d'unicite et de completude, mais font diverger ces deux comptes.

with attendu as (

    select count(*) as n
    from {{ ref('int_evenements_demographiques') }}
    where type_evenement = 'CREATION'
      and code_departement is not null

),

obtenu as (

    select coalesce(sum(nb_creations), 0) as n
    from {{ ref('fct_demographie_mensuelle') }}

)

select
    attendu.n as n_attendu,
    obtenu.n  as n_obtenu
from attendu, obtenu
where attendu.n <> obtenu.n
