{{ config(severity='warn') }}

-- Severite 'warn' assumee : ces valeurs existent dans le repertoire source et sont
-- deja neutralisees par les bornes de vraisemblance de int_evenements_demographiques.
-- Bloquer le pipeline sur une anomalie source connue et traitee n'apporte rien ;
-- la surveiller a chaque run, si.

-- Aucune creation ne peut etre posterieure a la date du jour, ni anterieure a la
-- creation du repertoire. Le fichier stock porte des valeurs aberrantes de ce type ;
-- ce test rend le nettoyage explicite au lieu de le laisser implicite dans un WHERE.

select
    siret,
    date_creation
from {{ ref('stg_etablissements') }}
where date_creation > current_date
   or date_creation < date '1800-01-01'
