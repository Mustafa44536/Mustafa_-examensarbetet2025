from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from pathlib import Path
import json

import pandas as pd
import requests

API_URL = "https://mgrey.se/espot?format=json&date={d}"  # docs: mgrey.se/espot/api

AREAS = ["SE1", "SE2", "SE3", "SE4"]

def daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)

def fetch_day(d: date, timeout: int = 30) -> dict:
    url = API_URL.format(d=d.isoformat())
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()

def normalize_day(payload: dict, currency: str) -> pd.DataFrame:
    # payload: { "date": "YYYY-MM-DD", "SE1": [{"hour":..,"price_sek":..,"price_eur":..}], ...}
    d = payload.get("date")
    rows = []
    for area in AREAS:
        for item in payload.get(area, []):
            hour = item.get("hour")
            if currency.upper() == "SEK":
                price = item.get("price_sek")
                unit = "öre/kWh"
            else:
                price = item.get("price_eur")
                unit = "cent/kWh"

            rows.append({
                "source": "mgrey_espot",
                "country": "Sweden",
                "area": area,
                "date": d,
                "hour": hour,
                "price": price,
                "currency": currency.upper(),
                "unit": unit,
                "granularity": "hourly",
                "ingested_at": pd.Timestamp.now("UTC"),
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce").astype("Int64")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["date", "hour"])  # måste finnas
    return df

def append_to_staging(stg_path: Path, new_df: pd.DataFrame):
    cols = ["source","country","area","date","hour","price","currency","unit","granularity","ingested_at"]
    new_df = new_df[cols].copy()

    if stg_path.exists():
        old = pd.read_csv(stg_path)
        # säkerställ kolumner
        for c in cols:
            if c not in old.columns:
                old[c] = pd.NA
        out = pd.concat([old[cols], new_df], ignore_index=True)
    else:
        out = new_df

    out.to_csv(stg_path, index=False)
    return len(new_df), len(out)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")
    p.add_argument("--currency", default="SEK", choices=["SEK","EUR","sek","eur"])
    p.add_argument("--save-raw", action="store_true", help="Save raw JSON per day to data/raw/nordpool/")
    p.add_argument("--timeout", type=int, default=30)
    args = p.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()

    raw_dir = Path("data/raw/nordpool")  # vi återanvänder din nordpool-mapp
    raw_dir.mkdir(parents=True, exist_ok=True)

    stg_path = Path("data/processed/stg_prices.csv")
    Path("data/processed").mkdir(parents=True, exist_ok=True)

    all_rows = 0
    for d in daterange(start, end):
        payload = fetch_day(d, timeout=args.timeout)

        if args.save_raw:
            (raw_dir / f"mgrey_espot_{d.isoformat()}.json").write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

        df = normalize_day(payload, currency=args.currency)
        if not df.empty:
            all_rows += len(df)

    # Om vi inte sparade mellan-resultat i loop: hämta om och bygg en gång (snabbt nog)
    dfs = []
    for d in daterange(start, end):
        payload = fetch_day(d, timeout=args.timeout)
        df = normalize_day(payload, currency=args.currency)
        if not df.empty:
            dfs.append(df)
    if not dfs:
        print("⚠️ No rows fetched (check dates).")
        return

    new_df = pd.concat(dfs, ignore_index=True)
    added, total = append_to_staging(stg_path, new_df)

    print(f"✅ Added {added} rows to {stg_path}")
    print(f"✅ Staging total rows now: {total}")
    print(new_df.head(8))

if __name__ == "__main__":
    main()
