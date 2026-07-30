"""Train the updated binary Random Forest environmental-risk model."""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


ROOT_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = ROOT_DIR / "data" / "synthetic_bleaching_dataset.csv"
MODEL_PATH = ROOT_DIR / "backend" / "bleaching_predictor.pkl"
METADATA_PATH = ROOT_DIR / "backend" / "model_metadata.pkl"

FEATURE_COLUMNS = [
    "Latitude",
    "Longitude",
    "Depth_m",
    "Year",
    "Sea_Surface_Temperature_C",
    "Degree_Heating_Weeks",
]
TARGET_COLUMN = "Bleaching_Label"


def train_model() -> RandomForestClassifier:
    print("=" * 70)
    print("REEFGUARDIAN AI - BINARY BLEACHING MODEL TRAINING")
    print("=" * 70)

    if not DATASET_PATH.is_file():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    frame = pd.read_csv(DATASET_PATH)
    required = set(FEATURE_COLUMNS + [TARGET_COLUMN])
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Dataset is missing columns: {', '.join(missing)}")

    clean = frame[FEATURE_COLUMNS + [TARGET_COLUMN]].dropna()
    X = clean[FEATURE_COLUMNS]
    y = clean[TARGET_COLUMN].astype(int)
    if set(y.unique()) != {0, 1}:
        raise ValueError("Bleaching_Label must contain binary values 0 and 1.")

    print(f"Loaded {len(frame)} rows; training with {len(clean)} complete rows.")
    print("Class distribution:")
    print(y.value_counts().sort_index())

    X_train, X_temporary, y_train, y_temporary = train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=42,
        stratify=y,
    )
    X_validation, X_test, y_validation, y_test = train_test_split(
        X_temporary,
        y_temporary,
        test_size=0.50,
        random_state=42,
        stratify=y_temporary,
    )

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=12,
        min_samples_split=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    print("\nEvaluation:")
    for name, features, labels in [
        ("Train", X_train, y_train),
        ("Validation", X_validation, y_validation),
        ("Test", X_test, y_test),
    ]:
        accuracy = accuracy_score(labels, model.predict(features))
        print(f"{name}: {accuracy:.2%}")

    print("\nTest classification report:")
    print(
        classification_report(
            y_test,
            model.predict(X_test),
            target_names=["No Bleaching", "Bleaching"],
            zero_division=0,
        )
    )

    print("Feature importance:")
    for column, importance in sorted(
        zip(FEATURE_COLUMNS, model.feature_importances_),
        key=lambda item: item[1],
        reverse=True,
    ):
        print(f"  {column:<30} {importance:.4f}")

    metadata = {
        "model_type": "RandomForestClassifier",
        "task": "binary_bleaching_risk",
        "feature_columns": FEATURE_COLUMNS,
        "feature_units": {
            "Latitude": "degrees",
            "Longitude": "degrees",
            "Depth_m": "metres",
            "Year": "calendar_year",
            "Sea_Surface_Temperature_C": "degrees_celsius",
            "Degree_Heating_Weeks": "DHW",
        },
        "target_column": TARGET_COLUMN,
        "model_classes": [int(value) for value in model.classes_],
        "classes": ["No Bleaching", "Bleaching"],
        "positive_class": 1,
        "training_rows": len(clean),
        "sklearn_version": sklearn.__version__,
        "dataset": DATASET_PATH.name,
    }
    joblib.dump(model, MODEL_PATH)
    joblib.dump(metadata, METADATA_PATH)
    print(f"\nSaved model: {MODEL_PATH}")
    print(f"Saved metadata: {METADATA_PATH}")
    return model


if __name__ == "__main__":
    train_model()
