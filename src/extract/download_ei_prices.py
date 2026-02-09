from pathlib import Path
import requests

# Ei: Historiska jämförpriser (xlsx). Länkar kan uppdateras över tid, men detta är en bra start.
URL_2018_PLUS = "https://ei.se/download/18.73711b7218a262cd92b5a8b/1768563665818/Statistik-slutkundspriser.xlsx"
URL_2008_2019 = "https://ei.se/download/18.75fbb4c4177d803861e85aae/1663335379210/Statistik-elhandelspriser-2008-2019.xlsx"

def dl(url: str, out_path: Path):
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    out_path.write_bytes(r.content)
    print(f"✅ Saved: {out_path}")

def main():
    out_dir = Path("data/raw/ei")
    out_dir.mkdir(parents=True, exist_ok=True)

    dl(URL_2018_PLUS, out_dir / "ei_slutkundspriser_2018plus.xlsx")
    dl(URL_2008_2019, out_dir / "ei_elhandelspriser_2008_2019.xlsx")

if __name__ == "__main__":
    main()
