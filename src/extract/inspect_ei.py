import pandas as pd

files = [
    "data/raw/ei/ei_slutkundspriser_2018plus.xlsx",
    "data/raw/ei/ei_elhandelspriser_2008_2019.xlsx",
]

for f in files:
    print("\n====", f, "====")
    xl = pd.ExcelFile(f)
    print("Sheets:", xl.sheet_names)

    # testa första sheet snabbt
    df = pd.read_excel(f, sheet_name=xl.sheet_names[0])
    print("Head:\n", df.head())
    print("Columns:\n", list(df.columns))
    print("Shape:", df.shape)
