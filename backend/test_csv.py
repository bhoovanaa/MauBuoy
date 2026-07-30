# debug_csv.py
import pandas as pd

# Load the CSV
df = pd.read_csv('data/global_bleaching_environmental.csv', sep='\t', header=None, na_values=['nd'])

print(f"Total columns: {df.shape[1]}")
print(f"Total rows: {df.shape[0]}")
print("\nFirst row (all columns):")
for i, val in enumerate(df.iloc[0]):
    print(f"  Column {i}: {val}")