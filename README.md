# Mustafa Mahamud DEE24

# ⚡ Elpris-datapipeline – Data Engineering-projekt

## 📌 Projektöversikt

Detta examensarbete demonstrerar hur en modern datapipeline kan byggas för att samla in, bearbeta, lagra och visualisera elprisdata.

Projektet analyserar spotpriser på el i Sverige med fokus på elområdena **SE1–SE4**, med syftet att identifiera:

- prisvariationer över tid  
- regionala skillnader  
- pristoppar  
- dygnsmönster  

Pipeline följer en klassisk arkitektur:

Extract → Transform → Load → Visualize

Detta representerar ett end-to-end Data Engineering workflow — från rådata till beslutsunderlag.

---

## 🎯 Syfte

Målet med projektet var att:

- bygga en automatiserad datapipeline  
- arbeta med verkliga energidata  
- strukturera data i ett data warehouse  
- skapa en interaktiv dashboard  
- generera insikter från elmarknaden  

Projektet visar hur Data Engineering används praktiskt för att göra rådata analysbar.

---

## ⚡ Vad är spotpris?

Spotpriset är marknadspriset på el — det pris energibolag betalar när de köper el från producenter.

Detta pris:

- styrs av utbud och efterfrågan  
- påverkas av väder, konsumtion och produktion  
- ligger till grund för kundernas elpris  

Genom att analysera spotpriser kan vi förstå dynamiken bakom elmarknaden.

---

## 🏗️ Arkitektur

Projektet är uppdelat enligt datapipeline-principer.

### 1️⃣ Extract – Datainsamling

Data hämtas automatiskt från öppna datakällor via API och filnedladdning.

**Datakällor:**

Svenska spotpriser  
https://www.elprisetjustnu.se/

Europeiska elpriser  
https://ember-climate.org/

Energimarknadsinspektionen  
https://www.energimarknadsinspektionen.se/

**Verktyg:**
- Python  
- Requests  
- Pandas  

---

### 2️⃣ Transform – Databearbetning

Transformationen gjordes i Python med Pandas.

**Exempel på steg:**
- rensning av felaktiga värden  
- standardisering av datatyper  
- konvertering av tidsformat  
- strukturering av datum och timkolumner  
- harmonisering av dataset  

Resultatet sparades som:

stg_prices.csv

---

### 3️⃣ Load – Data Warehouse

Den transformerade datan laddades in i ett analytiskt data warehouse.

**Teknik:** DuckDB  

Valdes eftersom det är snabbt, lättviktigt och SQL-baserat.

Warehouse innehåller en star schema-modell med faktatabell och dimensioner.

---

### 4️⃣ Visualize – Dashboard

Datan visualiserades i en interaktiv dashboard byggd med Streamlit.

Dashboarden möjliggör:

- analys av pris över tid  
- jämförelse mellan elområden  
- identifiering av pristoppar  
- analys av dygnsmönster  

---

## 📊 Dataset

Elområden:
- SE1 – Norra Norrland  
- SE2 – Norra Sverige  
- SE3 – Mellansverige  
- SE4 – Södra Sverige  

Tidsupplösning: 15 minuter  
Antal datapunkter: ~2700  

Den höga tidsupplösningen möjliggör detaljerad analys.

---

## 📁 Projektstruktur

src/  
extract/ – hämtar data  
transform/ – rensar data  
load/ – bygger warehouse  

data/  
raw/ – originaldata  
processed/ – staging  
warehouse/ – DuckDB  

app/  
dashboard.py – Streamlit dashboard  

---

## ▶️ Hur man kör projektet

### Installera beroenden
pip install pandas requests duckdb streamlit openpyxl

### Hämta data
python src/extract/download_se_prices_elprisetjustnu.py

### Transformera
python src/transform/ember_to_stg.py

### Bygg warehouse
python src/load/build_warehouse_duckdb.py

### Starta dashboard
streamlit run app/dashboard.py

---

## 🔑 Insikter

- El är ofta dyrast på kvällen  
- Södra Sverige tenderar att ha högre priser  
- Priser varierar kraftigt under dygnet  

---

## ✅ Slutsats

Projektet demonstrerar ett komplett dataflöde — från rådata till visualiserade insikter.

Genom att implementera en strukturerad datapipeline blev det möjligt att analysera elmarknaden effektivt.


