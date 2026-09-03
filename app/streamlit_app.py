"""
Dashboard de restitution : ou la creation d'entreprises accelere-t-elle en France ?

Lit directement la table de faits dbt dans DuckDB. Aucune logique metier ici :
tout calcul appartient a la couche marts, l'application ne fait qu'afficher.
C'est la separation qu'on attend d'un projet analytics engineering.

    streamlit run app/streamlit_app.py
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parents[1] / "sirene.duckdb"

st.set_page_config(page_title="Demographie des entreprises françaises",
                   layout="wide", page_icon="📊")


@st.cache_resource
def get_connection() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DB_PATH), read_only=True)


@st.cache_data
def query(sql: str, params: tuple = ()) -> pd.DataFrame:
    return get_connection().execute(sql, params).df()


st.title("Démographie des entreprises françaises")
st.caption(
    "Source : fichiers stock du répertoire SIRENE (INSEE, data.gouv.fr) — "
    "créations issues du stock courant, cessations reconstituées depuis les valeurs historisées. "
    "Unités en diffusion partielle exclues (RGPD)."
)

bornes = query("SELECT min(annee) AS a_min, max(annee) AS a_max FROM main.fct_demographie_mensuelle")
a_min, a_max = int(bornes.a_min[0]), int(bornes.a_max[0])

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    annees = st.slider("Période", a_min, a_max, (max(a_min, a_max - 5), a_max))
with col2:
    categories = query(
        "SELECT DISTINCT categorie_entreprise FROM main.fct_demographie_mensuelle ORDER BY 1"
    ).categorie_entreprise.tolist()
    categorie = st.selectbox("Catégorie d'entreprise", ["Toutes"] + categories)
with col3:
    sections = query(
        "SELECT DISTINCT code_section, libelle_section FROM main.dim_naf ORDER BY 1"
    )
    libelles = ["Tous secteurs"] + [
        f"{r.code_section} — {r.libelle_section}" for r in sections.itertuples()
    ]
    section = st.selectbox("Section NAF", libelles)

filtres = ["annee BETWEEN ? AND ?"]
params: list = [annees[0], annees[1]]
if categorie != "Toutes":
    filtres.append("categorie_entreprise = ?")
    params.append(categorie)
if section != "Tous secteurs":
    filtres.append("code_section = ?")
    params.append(section.split(" — ")[0])
where = " AND ".join(filtres)

# --- Indicateurs de tete -----------------------------------------------------
kpi = query(f"""
    SELECT sum(nb_creations) AS creations,
           sum(nb_cessations) AS cessations,
           sum(solde_net) AS solde
    FROM main.fct_demographie_mensuelle WHERE {where}
""", tuple(params))

k1, k2, k3 = st.columns(3)
k1.metric("Créations", f"{int(kpi.creations[0] or 0):,}".replace(",", " "))
k2.metric("Cessations", f"{int(kpi.cessations[0] or 0):,}".replace(",", " "))
k3.metric("Solde net", f"{int(kpi.solde[0] or 0):,}".replace(",", " "))

# --- Ou ca accelere ----------------------------------------------------------
st.subheader("Où la création accélère-t-elle ?")
st.caption(
    "Croissance des créations entre la première et la dernière année de la période, "
    "restreinte aux départements dépassant 500 créations sur la période afin d'éviter "
    "les variations en pourcentage sur de petits volumes."
)

acceleration = query(f"""
    WITH annuel AS (
        SELECT code_departement, libelle_departement, libelle_region, annee,
               sum(nb_creations) AS creations
        FROM main.fct_demographie_mensuelle WHERE {where}
        GROUP BY 1, 2, 3, 4
    ),
    bornes AS (
        SELECT code_departement, libelle_departement, libelle_region,
               sum(creations) AS creations_periode,
               arg_min(creations, annee) AS creations_debut,
               arg_max(creations, annee) AS creations_fin
        FROM annuel GROUP BY 1, 2, 3
    )
    SELECT libelle_departement AS "Département",
           libelle_region AS "Région",
           creations_periode AS "Créations (période)",
           creations_debut AS "Début",
           creations_fin AS "Fin",
           round(100.0 * (creations_fin - creations_debut)
                 / nullif(creations_debut, 0), 1) AS "Croissance %"
    FROM bornes
    WHERE creations_periode >= 500
    ORDER BY "Croissance %" DESC NULLS LAST
    LIMIT 20
""", tuple(params))
st.dataframe(acceleration, use_container_width=True, hide_index=True)

# --- Serie temporelle --------------------------------------------------------
st.subheader("Créations et cessations dans le temps")
serie = query(f"""
    SELECT mois, sum(nb_creations) AS "Créations", sum(nb_cessations) AS "Cessations"
    FROM main.fct_demographie_mensuelle WHERE {where}
    GROUP BY 1 ORDER BY 1
""", tuple(params)).set_index("mois")
st.line_chart(serie)

# --- Secteurs ----------------------------------------------------------------
st.subheader("Secteurs les plus dynamiques")
secteurs = query(f"""
    SELECT libelle_section AS "Secteur",
           sum(nb_creations) AS "Créations",
           sum(nb_cessations) AS "Cessations",
           sum(solde_net) AS "Solde net"
    FROM main.fct_demographie_mensuelle WHERE {where}
    GROUP BY 1 ORDER BY "Créations" DESC LIMIT 15
""", tuple(params))
st.dataframe(secteurs, use_container_width=True, hide_index=True)
