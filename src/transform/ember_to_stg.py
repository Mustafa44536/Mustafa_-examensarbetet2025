import pandas as pd
from pathlib import Path

IN_FILE = "data/raw/ember/ember_wholesale_prices_daily.xlsx"
OUT_FILE = "data/processed/stg_prices.csv"

# Välj vilka länder du vill ta med (du kan lägga till fler senare)
COUNTRIES = ["Sweden", "Finland", "Norway"]

def main():
    df = pd.read_excel(IN_FILE)

    # Rad 0 innehåller "rubriker i datan" -> vi tar bort den
    df = df.iloc[1:].copy()

    # Första kolumnen verkar vara datumsträng
    df = df.rename(columns={"Unnamed: 0": "date"})

    # Gör om till long format: date + land + price
    long_rows = []
    for c in COUNTRIES:
        col = f"Wholesale electricity price (EUR / MWh) - {c} - Ember - Daily"
        if col not in df.columns:
            raise ValueError(f"Hittar inte kolumnen: {col}")

        tmp = df[["date", col]].copy()
        tmp = tmp.rename(columns={col: "price"})
        tmp["country"] = c
        long_rows.append(tmp)

    out = pd.concat(long_rows, ignore_index=True)

    # Typer & städning
    out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date
    out["price"] = pd.to_numeric(out["price"], errors="coerce")

    out = out.dropna(subset=["date"])  # datum måste finnas
    # price får vara NaN (inget pris vissa dagar), men du kan droppa om du vill:
    # out = out.dropna(subset=["price"])

    out["source"] = "ember"
    out["area"] = out["country"]   # här är area = land (för Ember)
    out["hour"] = pd.NA            # daily data -> ingen timme
    out["currency"] = "EUR"
    out["unit"] = "EUR/MWh"
    out["granularity"] = "daily"
    out["ingested_at"] = pd.Timestamp.utcnow()

    # Ordna kolumner
    out = out[[
        "source", "country", "area", "date", "hour",
        "price", "currency", "unit", "granularity", "ingested_at"
    ]].sort_values(["country", "date"])

    Path("data/processed").mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_FILE, index=False)

    print(f"✅ Created staging file: {OUT_FILE}")
    print(out.head(10))

if __name__ == "__main__":
    main()

