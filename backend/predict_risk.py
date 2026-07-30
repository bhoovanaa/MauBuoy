"""Binary environmental bleaching-risk prediction for ReefGuardian."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "bleaching_predictor.pkl"
METADATA_PATH = BASE_DIR / "model_metadata.pkl"

try:
    predictor = joblib.load(MODEL_PATH)
    metadata = joblib.load(METADATA_PATH)
    FEATURE_COLS = list(
        metadata.get(
            "feature_columns",
            getattr(predictor, "feature_names_in_", []),
        )
    )
    CLASSES = list(metadata.get("classes", ["No Bleaching", "Bleaching"]))
    print(f"Model loaded. Classes: {CLASSES}")
    print(f"   Features: {FEATURE_COLS}")
except FileNotFoundError:
    print("Model not found. Run: python backend/train_prediction_model.py")
    predictor = None
    FEATURE_COLS = []
    CLASSES = ["No Bleaching", "Bleaching"]


def _risk_level(score: int) -> str:
    if score < 30:
        return "LOW"
    if score < 60:
        return "MODERATE"
    if score < 80:
        return "HIGH"
    return "CRITICAL"


def _class_name(value: Any) -> str:
    normalized = str(value).strip().lower().replace("_", " ")
    if normalized in {"0", "no bleaching", "no event", "false"}:
        return "No Bleaching"
    if normalized in {"1", "bleaching", "bleaching event", "true"}:
        return "Bleaching"
    return str(value)


def predict_bleaching_risk(
    latitude: float,
    longitude: float,
    depth_m: float,
    sst_celsius: float,
    dhw: float,
    year: int | None = None,
    coral_health: str = "unknown",
) -> dict[str, Any]:
    """Predict binary bleaching probability from the updated six-feature model."""

    if predictor is None:
        return {
            "probabilities": {"No Bleaching": 0.5, "Bleaching": 0.5},
            "predicted_class": "unknown",
            "confidence": 0.0,
            "bleaching_risk_score": 50,
            "risk_level": "UNKNOWN",
            "disease_outbreak_probability": "50%",
            "recovery_potential": "50%",
            "reasoning": "Prediction model unavailable.",
        }

    feature_values = {
        "Latitude": latitude,
        "Longitude": longitude,
        "Depth_m": depth_m,
        "Year": year if year is not None else datetime.now().year,
        "Sea_Surface_Temperature_C": sst_celsius,
        "Degree_Heating_Weeks": dhw,
    }
    missing = [column for column in FEATURE_COLS if column not in feature_values]
    if missing:
        raise ValueError(
            "Model metadata contains unsupported features: " + ", ".join(missing)
        )

    features = pd.DataFrame(
        [{column: feature_values[column] for column in FEATURE_COLS}]
    )
    raw_probabilities = predictor.predict_proba(features)[0]
    probabilities = {
        _class_name(model_class): float(probability)
        for model_class, probability in zip(
            predictor.classes_,
            raw_probabilities,
        )
    }
    probabilities.setdefault("No Bleaching", 0.0)
    probabilities.setdefault("Bleaching", 0.0)

    predicted_class = max(probabilities, key=probabilities.get)
    confidence = probabilities[predicted_class]
    bleaching_probability = probabilities["Bleaching"]
    risk_score = int(round(bleaching_probability * 100))
    risk_level = _risk_level(risk_score)
    disease_probability = min(95, risk_score + 15)
    base_recovery = max(5, 100 - risk_score)

    health = coral_health.strip().lower()
    if health == "healthy":
        recovery = base_recovery
        health_reasoning = "Visual assessment is healthy; continue preventive monitoring."
    elif health == "stressed":
        recovery = max(10, base_recovery - 20)
        health_reasoning = "Visual stress elevates the need for early intervention."
    elif health == "bleached":
        recovery = max(5, base_recovery - 40)
        health_reasoning = "Visual bleaching reduces recovery potential."
    elif health == "dead":
        recovery = 0
        health_reasoning = "Dead coral requires restoration planning rather than recovery monitoring."
    else:
        recovery = base_recovery
        health_reasoning = "No reliable visual health state was supplied."

    reasoning = (
        f"Model predicts {predicted_class} at {confidence:.1%} confidence. "
        f"Bleaching risk is {risk_score}/100 ({risk_level}), based on "
        f"SST {sst_celsius:.1f} C and DHW {dhw:.1f}. {health_reasoning}"
    )

    return {
        "probabilities": {
            name: round(probability, 4)
            for name, probability in probabilities.items()
        },
        "predicted_class": predicted_class,
        "confidence": round(confidence, 4),
        "bleaching_risk_score": risk_score,
        "risk_level": risk_level,
        "disease_outbreak_probability": f"{disease_probability}%",
        "recovery_potential": f"{recovery}%",
        "reasoning": reasoning,
    }


def predict_14_day_bleaching_risk(
    latitude: float,
    longitude: float,
    depth: float,
    sst_kelvin: float,
    dhw: float,
    coral_health: str = "unknown",
) -> dict[str, Any]:
    """Keep the API contract while converting its Kelvin input to Celsius."""

    return predict_bleaching_risk(
        latitude=latitude,
        longitude=longitude,
        depth_m=depth,
        sst_celsius=sst_kelvin - 273.15,
        dhw=dhw,
        coral_health=coral_health,
    )


if __name__ == "__main__":
    scenarios = [
        ("Le Morne", -20.46, 57.32, 18.0, 27.5, 0.5, "healthy"),
        ("Blue Bay", -20.44, 57.72, 5.0, 31.2, 8.5, "bleached"),
    ]
    for name, latitude, longitude, depth, sst, dhw, health in scenarios:
        result = predict_bleaching_risk(
            latitude,
            longitude,
            depth,
            sst,
            dhw,
            coral_health=health,
        )
        print(f"\n{name}:")
        print(result)
