# backend/create_synthetic_data.py
"""
ReefGuardian AI - Synthetic Data Generator
Creates scientifically valid "no-event" records using NOAA thresholds.
"""

import pandas as pd
import numpy as np
import os

def create_synthetic_no_event_data(n_records, feature_columns, seed=42):
    """
    Generates synthetic "no bleaching event" records using NOAA thresholds.
    
    NOAA Scientific Basis:
    - Coral reefs exist between 30°N and 30°S latitude
    - Normal SST for healthy corals: 24-29°C (297-302K)
    - DHW < 4 means no bleaching risk
    - Reef depths: 1-30m typical
    
    Args:
        n_records: Number of synthetic records to generate
        feature_columns: List of column names to match training data
        seed: Random seed for reproducibility
    
    Returns:
        DataFrame with synthetic no-event records
    """
    
    np.random.seed(seed)
    print(f"🧪 Generating {n_records} synthetic no-event records...")
    
    synthetic_data = []
    
    for _ in range(n_records):
        record = {}
        
        for col in feature_columns:
            col_lower = col.lower()
            
            if 'lat' in col_lower:
                # Tropical reef zones only (-30 to 30)
                record[col] = np.random.uniform(-30, 30)
                
            elif 'lon' in col_lower or 'long' in col_lower:
                # Global ocean coverage
                record[col] = np.random.uniform(-180, 180)
                
            elif 'depth' in col_lower:
                # Typical reef depths (1-30m)
                record[col] = np.random.uniform(1, 30)
                
            elif 'year' in col_lower or 'date' in col_lower:
                # Recent years (2000-2024)
                record[col] = np.random.randint(2000, 2025)
                
            elif 'sst' in col_lower or 'temp' in col_lower or 'climsst' in col_lower:
                # BELOW bleaching threshold (< 302.65K / 29.5°C)
                # Normal coral temperatures: 297-302K (24-29°C)
                record[col] = np.random.uniform(297.0, 302.5)
                
            elif 'dhw' in col_lower or 'heating' in col_lower:
                # BELOW bleaching threshold (< 4)
                # Normal DHW: 0-3.9 (4+ means bleaching risk)
                record[col] = np.random.uniform(0, 3.9)
                
            else:
                # Unknown column - set to 0
                record[col] = 0
        
        synthetic_data.append(record)
    
    df_synthetic = pd.DataFrame(synthetic_data)
    
    print(f"✅ Generated {len(df_synthetic)} synthetic records")
    print(f"\n📊 Data ranges:")
    for col in feature_columns:
        col_lower = col.lower()
        if 'sst' in col_lower or 'temp' in col_lower:
            print(f"   {col}: {df_synthetic[col].min():.1f}K - {df_synthetic[col].max():.1f}K")
        elif 'dhw' in col_lower:
            print(f"   {col}: {df_synthetic[col].min():.1f} - {df_synthetic[col].max():.1f}")
        elif 'lat' in col_lower:
            print(f"   {col}: {df_synthetic[col].min():.1f}° - {df_synthetic[col].max():.1f}°")
        elif 'depth' in col_lower:
            print(f"   {col}: {df_synthetic[col].min():.1f}m - {df_synthetic[col].max():.1f}m")
    
    return df_synthetic


if __name__ == "__main__":
    # Example usage
    feature_cols = ['Latitude_Degrees', 'Longitude_Degrees', 'Depth_m', 
                    'Date_Year', 'ClimSST', 'SSTA_DHW']
    
    df_synth = create_synthetic_no_event_data(2669, feature_cols)
    
    # Save to CSV
    os.makedirs('data', exist_ok=True)
    output_path = 'data/synthetic_no_event.csv'
    df_synth.to_csv(output_path, index=False)
    print(f"\n💾 Saved to: {output_path}")