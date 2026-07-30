# debug_combine.py
import pandas as pd
import glob
import os

print("="*70)
print("DEBUGGING COMBINE_DATASETS")
print("="*70)

# Step 1: Find the data file
print("\n🔍 Step 1: Finding data file...")
file_path = None
for pattern in ['data/*bleaching*.csv', 'data/*bleaching*.xlsx']:
    files = glob.glob(pattern)
    if files:
        file_path = files[0]
        break

if file_path is None:
    print("❌ No CSV/Excel file found!")
    print("Files in data/:")
    for f in os.listdir('data'):
        print(f"   - {f}")
    exit(1)

print(f"✅ Found: {file_path}")

# Step 2: Load the file
print(f"\n📂 Step 2: Loading file...")
if file_path.endswith('.xlsx'):
    df = pd.read_excel(file_path)
else:
    for sep in [',', '\t', ';']:
        try:
            test = pd.read_csv(file_path, sep=sep, nrows=3)
            if len(test.columns) > 5:
                df = pd.read_csv(file_path, sep=sep, na_values=['nd', 'ND', ''])
                print(f"✅ Loaded with separator: {repr(sep)}")
                break
        except:
            continue

print(f"📊 Dataset shape: {df.shape[0]} rows × {df.shape[1]} columns")

# Step 3: Find text column
print(f"\n📝 Step 3: Finding text column...")
text_col = None
for col in df.columns:
    if df[col].dtype == 'object':
        avg_len = df[col].astype(str).str.len().mean()
        if avg_len > 20:
            text_col = col
            break

if text_col is None:
    text_col = df.columns[-1]

print(f"Text column: '{text_col}'")

# Step 4: Check for bleaching keywords
print(f"\n🔥 Step 4: Checking for 'bleach' keyword...")
bleach_count = df[text_col].astype(str).str.contains('bleach', case=False, na=False).sum()
print(f"Records containing 'bleach': {bleach_count}")

if bleach_count == 0:
    print("\n❌ NO BLEACHING RECORDS FOUND!")
    print("\nTrying alternative keywords:")
    for kw in ['white', 'stress', 'mortality', 'dead', 'disease']:
        count = df[text_col].astype(str).str.contains(kw, case=False, na=False).sum()
        if count > 0:
            print(f"   '{kw}': {count} records")

# Step 5: Show sample text values
print(f"\n📋 Step 5: Sample text values (first 10):")
print("="*70)
for i, val in enumerate(df[text_col].head(10)):
    print(f"[{i}] {str(val)[:150]}")
print("="*70)

# Step 6: Check if real_bleaching_events.csv exists
print(f"\n💾 Step 6: Checking real_bleaching_events.csv...")
if os.path.exists('data/real_bleaching_events.csv'):
    df_real = pd.read_csv('data/real_bleaching_events.csv')
    print(f"✅ File exists with {len(df_real)} records")
    print(f"Columns: {list(df_real.columns)}")
else:
    print("❌ File does not exist!")

# Step 7: Check combined_dataset.csv
print(f"\n📊 Step 7: Checking combined_dataset.csv...")
if os.path.exists('data/combined_dataset.csv'):
    df_combined = pd.read_csv('data/combined_dataset.csv')
    print(f"✅ File exists with {len(df_combined)} records")
    print(f"Target distribution:")
    print(df_combined['target'].value_counts())
else:
    print("❌ File does not exist!")