.PHONY: install fixtures sample download load build test docs dashboard all

install:
	pip install -r requirements.txt

# Chaine complete sur donnees synthetiques : valide le pipeline sans les vrais fichiers
fixtures:
	python ingestion/make_fixtures.py

# Echantillon reel lu a distance, sans attendre le telechargement complet
sample:
	python ingestion/load_duckdb.py --sample 200000

download:
	python ingestion/download.py

load:
	python ingestion/load_duckdb.py

build:
	cd dbt_sirene && dbt seed --profiles-dir . && dbt run --profiles-dir .

test:
	cd dbt_sirene && dbt test --profiles-dir .

docs:
	cd dbt_sirene && dbt docs generate --profiles-dir . && dbt docs serve --profiles-dir .

dashboard:
	streamlit run app/streamlit_app.py

all: fixtures build test
