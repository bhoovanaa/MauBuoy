# validate_new_dataset.py
import pandas as pd
import os

print("="*70)
print("VALIDATING NEW DATASET")
print("="*70)

# Find the file
file_path = "data/realistic_ocean_climate_dataset.csv"

if not os.path.exists(file_path):
    print(f"❌ Dataset not found: {file_path}")
    exit(1)

print(f"✅ Found: {file_path}")

# Load
if file_path.endswith('.xlsx'):
    df = pd.read_excel(file_path)
else:
    df = pd.read_csv(file_path)

print(f"\n📊 Shape: {df.shape[0]} rows × {df.shape[1]} columns")

print(f"\n📋 Columns:")
for col in df.columns:
    print(f"   - {col}")

# Check target distribution
print(f"\n🎯 Bleaching Severity Distribution:")
if 'Bleaching Severity' in df.columns:
    print(df['Bleaching Severity'].value_counts())
    total = len(df)
    print(f"\n📈 Percentages:")
    for severity, count in df['Bleaching Severity'].value_counts().items():
        print(f"   {severity:<10} → {count:5d} ({count/total*100:.1f}%)")
else:
    print("❌ 'Bleaching Severity' column not found!")

# Check for missing values
print(f"\n⚠️  Missing Values:")
missing = df.isnull().sum()
if missing.sum() == 0:
    print("   ✅ No missing values!")
else:
    print(missing[missing > 0])

# Check SST range
if 'SST (°C)' in df.columns:
    print(f"\n🌡️  SST Range: {df['SST (°C)'].min():.1f}°C - {df['SST (°C)'].max():.1f}°C")

# Check pH range
if 'pH Level' in df.columns:
    print(f"🧪 pH Range: {df['pH Level'].min():.2f} - {df['pH Level'].max():.2f}")

print("\n" + "="*70)
print("VALIDATION COMPLETE")
print("="*70)