import pandas as pd

df = pd.read_excel("data/raw/ember/ember_wholesale_prices_daily.xlsx")

print(df.head())
print("\nColumns:\n", df.columns)
print("\nShape:", df.shape)
