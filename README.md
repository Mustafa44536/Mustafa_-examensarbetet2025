# Examensarbete – Elprisdata pipeline (G-nivå)

## Syfte
Bygga en enkel data pipeline för elprisdata och visualisera svenska elområden (SE1–SE4).

## Datakällor
- Ember – grossistpriser per land (daily)
- elprisetjustnu – svenska spotpriser per elområde (15-min)

## Körordning
1. Installera beroenden
   pip install pandas requests duckdb openpyxl

2. Hämta Ember-data
   python src/extract/download_ember_fetchseries.py

3. Transformera Ember → staging
   python src/transform/ember_to_stg.py

4. Hämta svenska elpriser (SE1–SE4)
   python src/extract/download_se_prices_elprisetjustnu.py --start 2026-02-01 --end 2026-02-07 --currency SEK --save-raw

5. Bygg warehouse
   python src/load/build_warehouse_duckdb.py

6. Power BI
   Importera: data/processed/sweden_se_prices.csv
