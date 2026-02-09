from pathlib import Path
import requests

URL = "https://www.fetchseries.com/electricity/wholesale-electrictiy-prices-in-europe/wholesale-electrictiy-prices-in-europe.xlsx"

def main():
    out = Path("data/raw/ember/ember_wholesale_prices_daily.xlsx")
    out.parent.mkdir(parents=True, exist_ok=True)

    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    out.write_bytes(r.content)

    print(f"✅ Saved: {out}")

if __name__ == "__main__":
    main()
