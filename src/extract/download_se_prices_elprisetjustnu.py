from __future__ import annotations

import argparse
from datetime import datetime, date, timedelta
from pathlib import Path
import json
import time

import pandas as pd
import requests

BASE = "https://www.elprisetjustnu.se/api/v1/prices/{yyyy}/{mmdd}_{area}.json"
AREAS = ["SE1", "SE2", "SE3", "SE4"]

def daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)

def fetch_with_retry(url: str, timeout: int, retries: int = 5, backoff: float = 1.5):
    last_err = None
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout, headers={"User-Agent": "sti-exam/1.0"})
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            sleep_s = backoff ** i
            time.sleep(sleep_s)
    raise last_err

def normalize(area: str, day: date, payload: list[dict], currency: str) -> pd.DataFrame:
    rows = []
    for item in payload:
        ts_start = item.get("time_start")
        ts_end = item.get("time_end")
        # Välj prisfält
        if currency.upper() == "SEK":
            price = item.get("SEK_per_kWh")
            unit = "SEK/kWh"
        else:
            price = item.get("EUR_per_kWh")
            unit = "EUR/kWh"

        # time_start har tidszon i ISO8601 (ex: 2022-11-24T00:00:00+01:00)
        # Vi plockar ut timmen (för kvartsvärden kommer flera rader ha samma timme)
        hour = None
        try:
            dt = datetime.fromisoformat(ts_start)
            hour = dt.hour
        except Exception:
            hour = None

        rows.append({
            "source": "elprisetjustnu",
            "country": "Sweden",
            "area": area,
            "date": day.isoformat(),
            "hour": hour,
            "price": price,
            "currency": currency.upper(),
            "unit": unit,
            "granularity": "hourly_or_quarter",
            "time_start": ts_start,
            "time_end": ts_end,
            "ingested_at": pd.Timestamp.now("UTC"),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce").astype("Int64")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["date"])  # datum måste finnas
    return df

def append_to_staging(stg_path: Path, new_df: pd.DataFrame):
    base_cols = ["source","country","area","date","hour","price","currency","unit","granularity","ingested_at"]
    extra_cols = ["time_start","time_end"]
    cols = base_cols + extra_cols

    # säkerställ kolumner
    for c in cols:
        if c not in new_df.columns:
            new_df[c] = pd.NA
    new_df = new_df[cols].copy()

    if stg_path.exists():
        old = pd.read_csv(stg_path)
        # om staging saknar extra kolumner, lägg till
        for c in cols:
            if c not in old.columns:
                old[c] = pd.NA
        out = pd.concat([old[cols], new_df], ignore_index=True)
    else:
        out = new_df

    stg_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(stg_path, index=False)
    return len(new_df), len(out)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, help="YYYY-MM-DD")
    p.add_argument("--end", required=True, help="YYYY-MM-DD")
    p.add_argument("--currency", default="SEK", choices=["SEK","EUR","sek","eur"])
    p.add_argument("--save-raw", action="store_true")
    p.add_argument("--timeout", type=int, default=30)
    args = p.parse_args()

    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end = datetime.strptime(args.end, "%Y-%m-%d").date()

    raw_dir = Path("data/raw/nordpool")  # återanvänder din mapp
    raw_dir.mkdir(parents=True, exist_ok=True)
    stg_path = Path("data/processed/stg_prices.csv")

    dfs = []
    for d in daterange(start, end):
        yyyy = d.strftime("%Y")
        mmdd = d.strftime("%m-%d")
        for area in AREAS:
            url = BASE.format(yyyy=yyyy, mmdd=mmdd, area=area)
            payload = fetch_with_retry(url, timeout=args.timeout)

            if args.save_raw:
                (raw_dir / f"elprisetjustnu_{area}_{d.isoformat()}.json").write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )

            df = normalize(area, d, payload, currency=args.currency)
            if not df.empty:
                dfs.append(df)

    if not dfs:
        print("⚠️ No rows fetched. Kontrollera datum (API har historik från 2022-11-01 och framåt).")
        return

    new_df = pd.concat(dfs, ignore_index=True)
    added, total = append_to_staging(stg_path, new_df)

    print(f"✅ Added {added} rows to {stg_path}")
    print(f"✅ Staging total rows now: {total}")
    print(new_df.head(8))

if __name__ == "__main__":
    main()
