# backend/combine_datasets.py
"""
ReefGuardian AI - Dataset Combiner
Combines real bleaching events with synthetic no-event data.
"""

import pandas as pd
import os

def extract_bleaching_events(file_path):
    """Extracts only bleaching event records from the NOAA dataset."""
    
    print(f"📂 Loading: {file_path}")
    
    # Load data
    df = None
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
    
    if df is None:
        print(f"❌ Could not load file: {file_path}")
        exit(1)
    
    print(f"📊 Original dataset: {len(df)} records")
    
    # Find text column
    text_col = None
    for col in df.columns:
        if df[col].dtype == 'object':
            avg_len = df[col].astype(str).str.len().mean()
            if avg_len > 20:
                text_col = col
                break
    
    if text_col is None:
        text_col = df.columns[-1]
    
    print(f"📝 Text column: '{text_col}'")
    
    # Check for bleaching keywords
    bleach_count = df[text_col].astype(str).str.contains('bleach', case=False, na=False).sum()
    print(f"🔍 Records containing 'bleach': {bleach_count}")
    
    # Filter to ONLY bleaching records
    bleach_mask = df[text_col].astype(str).str.contains('bleach', case=False, na=False)
    df_bleached = df[bleach_mask].copy()
    
    print(f"🔥 Extracted {len(df_bleached)} bleaching events")
    
    return df_bleached


def combine_datasets(real_bleached_path, synthetic_path, feature_columns):
    """Combines real bleaching events with synthetic no-event data."""
    
    print(f"\n⚖️  Combining datasets...")
    
    # Load real bleaching data
    df_real = pd.read_csv(real_bleached_path)
    X_real = df_real[feature_columns].copy()
    
    # Convert to numeric
    for col in feature_columns:
        X_real[col] = pd.to_numeric(X_real[col], errors='coerce')
    
    # Drop missing values
    X_real = X_real.dropna()
    print(f"   Real bleaching records: {len(X_real)}")
    
    # Load synthetic data
    df_synth = pd.read_csv(synthetic_path)
    X_synth = df_synth[feature_columns]
    print(f"   Synthetic no-event records: {len(X_synth)}")
    
    # Combine
    X_combined = pd.concat([X_real, X_synth], ignore_index=True)
    y_combined = pd.Series([1] * len(X_real) + [0] * len(X_synth))
    
    print(f"\n📊 Combined dataset:")
    print(f"   Total records: {len(X_combined)}")
    print(f"   Bleaching events (1): {y_combined.sum()} ({y_combined.mean()*100:.1f}%)")
    print(f"   No events (0): {(y_combined == 0).sum()} ({(1-y_combined.mean())*100:.1f}%)")
    print(f"   ✅ Balanced 50/50 split!")
    
    return X_combined, y_combined


if __name__ == "__main__":
    feature_cols = ['Latitude_Degrees', 'Longitude_Degrees', 'Depth_m', 
                    'Date_Year', 'ClimSST', 'SSTA_DHW']
    
    # Step 1: Use the EXACT filename
    real_data_file = 'data/global_bleaching_environmental.csv'
    
    if not os.path.exists(real_data_file):
        print(f"❌ File not found: {real_data_file}")
        print("Available files in data/:")
        for f in os.listdir('data'):
            print(f"   - {f}")
        exit(1)
    
    print(f"✅ Found real data file: {real_data_file}")
    
    # Step 2: Extract bleaching events
    df_bleached = extract_bleaching_events(real_data_file)
    
    if len(df_bleached) == 0:
        print("\n❌ No bleaching events found!")
        print("Trying alternative keywords...")
        # Try loading the file and checking what keywords exist
        df = pd.read_csv(real_data_file, sep='\t', na_values=['nd', 'ND'])
        text_col = [col for col in df.columns if df[col].dtype == 'object'][-1]
        for kw in ['white', 'stress', 'mortality', 'dead', 'disease', 'coral']:
            count = df[text_col].astype(str).str.contains(kw, case=False, na=False).sum()
            if count > 0:
                print(f"   '{kw}': {count} records")
        exit(1)
    
    # Save extracted bleaching events
    os.makedirs('data', exist_ok=True)
    df_bleached[feature_cols].to_csv('data/real_bleaching_events.csv', index=False)
    print(f"💾 Saved bleaching events to: data/real_bleaching_events.csv")
    
    # Step 3: Combine datasets
    X, y = combine_datasets(
        'data/real_bleaching_events.csv',
        'data/synthetic_no_event.csv',
        feature_cols
    )
    
    # Save combined dataset
    combined_df = X.copy()
    combined_df['target'] = y
    combined_df.to_csv('data/combined_dataset.csv', index=False)
    print(f"💾 Saved combined dataset to: data/combined_dataset.csv")
    
    print("\n🎉 Dataset combination complete!")
    print("Next step: python backend/train_prediction_model.py")