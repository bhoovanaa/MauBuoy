# diagnose_model.py
import joblib
import pandas as pd
import numpy as np

# Load model and metadata
model = joblib.load('bleaching_predictor.pkl')
metadata = joblib.load('model_metadata.pkl')

print("Model classes:", model.classes_)
print("Features:", metadata['feature_columns'])

# Test with Blue Bay data
test_data = {
    'Latitude_Degrees': -20.40,
    'Longitude_Degrees': 57.70,
    'Depth_m': 5.0,
    'Date_Year': 2024,
    'ClimSST': 303.5,
    'SSTA_DHW': 8.5
}

df = pd.DataFrame([test_data])
print("\nInput data:")
print(df)

# Get raw probabilities
probs = model.predict_proba(df)
print(f"\nRaw probabilities: {probs}")
print(f"P(no_event): {probs[0][0]:.4f}")
print(f"P(bleaching_event): {probs[0][1]:.4f}")

# Get prediction
pred = model.predict(df)
print(f"\nPrediction: {pred[0]}")

# Check feature importance
print("\nFeature importance:")
for feat, imp in zip(metadata['feature_columns'], model.feature_importances_):
    print(f"  {feat}: {imp:.3f}")