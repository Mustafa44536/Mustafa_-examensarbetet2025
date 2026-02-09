import pandas as pd

FILE = "data/raw/ei/ei_slutkundspriser_2018plus.xlsx"
SHEET = "Villa 20 000 kWh"  # vi kör på denna

df = pd.read_excel(FILE, sheet_name=SHEET, header=None)

print("Shape:", df.shape)
print("\n--- First 25 rows (raw) ---")
print(df.head(25))

print("\n--- Row candidates containing 'År' or 'Ar' ---")
for i in range(min(40, len(df))):
    row = df.iloc[i].astype(str).str.lower()
    if row.str.contains("år").any() or row.str.contains("ar").any():
        print("Row", i, ":", df.iloc[i].tolist())
