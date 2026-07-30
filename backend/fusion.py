"""Deterministic fusion and restoration guidance for ReefGuardian AI."""

from __future__ import annotations

from typing import Any

try:
    from .environmental_stress import calculate_environmental_stress
    from .intervention_simulation import build_intervention_options
    from .predict_risk import predict_14_day_bleaching_risk
except ImportError:  # Support direct execution from the backend directory.
    from environmental_stress import calculate_environmental_stress
    from intervention_simulation import build_intervention_options
    from predict_risk import predict_14_day_bleaching_risk


RISK_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3, "UNKNOWN": 1}
HEALTH_RANK = {"Healthy": 0, "Bleached": 2, "Dead": 3, "Uncertain": 1}


def normalize_visual_assessment(visual: dict[str, Any]) -> dict[str, Any]:
    health = (
        visual.get("overall_condition")
        or visual.get("health")
        or visual.get("status")
        or "Uncertain"
    )
    canonical = {
        "healthy": "Healthy",
        "bleached": "Bleached",
        "dead": "Dead",
        "uncertain": "Uncertain",
        "unknown": "Uncertain",
        "no_reliable_coral_detected": "Uncertain",
    }.get(str(health).lower(), str(health).title())
    confidence = float(visual.get("confidence", 0.0) or 0.0)
    status = visual.get(
        "status",
        "no_reliable_coral_detected" if canonical == "Uncertain" else "ok",
    )
    return {
        "health": canonical,
        "confidence": max(0.0, min(1.0, confidence)),
        "status": status,
    }


def fuse_assessments(
    visual: dict[str, Any],
    environmental: dict[str, Any],
) -> dict[str, Any]:
    """Combine independent evidence while preserving uncertainty/disagreement."""

    normalized_visual = normalize_visual_assessment(visual)
    health = normalized_visual["health"]
    risk_level = str(environmental.get("risk_level", "UNKNOWN")).upper()
    risk_score = float(environmental.get("bleaching_risk_score", 50) or 50)
    flags: list[str] = []

    if normalized_visual["status"] != "ok" or health == "Uncertain":
        flags.append("no_reliable_visual_detection")
    if normalized_visual["confidence"] < 0.60 and health != "Uncertain":
        flags.append("low_visual_confidence")
    if health == "Healthy" and risk_level in {"HIGH", "CRITICAL"}:
        flags.append("healthy_visual_but_high_environmental_risk")
    if health in {"Bleached", "Dead"} and risk_level == "LOW":
        flags.append("visual_environmental_disagreement")

    combined_rank = max(
        HEALTH_RANK.get(health, 1),
        RISK_RANK.get(risk_level, 1),
    )
    priority = {
        0: "LOW",
        1: "MODERATE",
        2: "HIGH",
        3: "CRITICAL",
    }[combined_rank]

    if health == "Uncertain":
        overall_status = (
            f"{risk_level.title()} environmental risk; visual review required"
        )
    elif flags:
        overall_status = (
            f"{priority.title()} priority with model disagreement/review flag"
        )
    else:
        overall_status = f"{priority.title()} restoration priority"

    return {
        "overall_status": overall_status,
        "priority": priority,
        "review_required": bool(flags),
        "review_flags": flags,
        "visual_assessment": normalized_visual,
        "environmental_assessment": {
            **environmental,
            "bleaching_risk_score": round(risk_score, 2),
            "risk_level": risk_level,
        },
        "interpretation": (
            "Visual health and environmental risk are independent signals. "
            "A review flag is retained when they disagree or visual evidence "
            "does not pass the reliability gate."
        ),
    }


def deterministic_recommendation(
    cv_output: dict[str, Any],
    sensor_data: dict[str, Any],
    location_name: str,
) -> dict[str, Any]:
    """Generate an auditable recommendation when Ollama is unavailable."""

    normalized = normalize_visual_assessment(cv_output)
    stress = calculate_environmental_stress(
        water_temp_c=float(sensor_data["water_temp_c"]),
        ph_level=float(sensor_data["ph_level"]),
        turbidity_ntu=float(sensor_data["turbidity_ntu"]),
        salinity_ppt=float(sensor_data["salinity_ppt"]),
    )
    risk_factors: list[str] = []
    if normalized["health"] == "Uncertain":
        risk_factors.append("Visual evidence did not pass the reliability gate")
    if float(sensor_data["water_temp_c"]) > 29.0:
        risk_factors.append("Elevated water temperature")
    if float(sensor_data["ph_level"]) < 8.0:
        risk_factors.append("Low pH")
    if float(sensor_data["turbidity_ntu"]) > 5.0:
        risk_factors.append("Elevated turbidity")
    if not risk_factors:
        risk_factors.append("No major threshold exceedance in supplied readings")

    alert_level = stress["stress_level"]
    if normalized["health"] == "Bleached" and alert_level in {"LOW", "MODERATE"}:
        alert_level = "HIGH"
    if normalized["health"] == "Dead":
        alert_level = "CRITICAL"

    required_prediction_inputs = (
        "latitude",
        "longitude",
        "depth_m",
        "sst_kelvin",
        "dhw",
    )
    if all(sensor_data.get(field) is not None for field in required_prediction_inputs):
        prediction = predict_14_day_bleaching_risk(
            latitude=float(sensor_data["latitude"]),
            longitude=float(sensor_data["longitude"]),
            depth=float(sensor_data["depth_m"]),
            sst_kelvin=float(sensor_data["sst_kelvin"]),
            dhw=float(sensor_data["dhw"]),
            coral_health=normalized["health"],
        )
        baseline_risk = float(prediction["bleaching_risk_score"])
    else:
        baseline_risk = float(stress["stress_score"])

    interventions = build_intervention_options(
        cv_output={
            "health": normalized["health"],
            "confidence": normalized["confidence"],
        },
        sensor_data=sensor_data,
        location_name=location_name,
        baseline_risk_score=baseline_risk,
        limit=4,
    )
    primary = interventions[0]
    confidence = min(
        normalized["confidence"] if normalized["health"] != "Uncertain" else 0.45,
        primary["confidence_score"],
    )

    return {
        "alert_level": alert_level,
        "coral_health_summary": (
            f"{normalized['health']} visual assessment at "
            f"{normalized['confidence']:.0%} detector confidence."
        ),
        "environmental_assessment": (
            f"{stress['stress_level']} environmental stress "
            f"({stress['stress_score']}/100)."
        ),
        "recommended_technique": primary["technique_id"],
        "technique_name": primary["name"],
        "reasoning": (
            f"For {location_name}, {primary['name']} is the highest-ranked "
            "threshold-based scenario. Compare the detailed alternatives and "
            "obtain marine-specialist review before deployment."
        ),
        "predicted_survival_rate": primary["predicted_survival_rate"],
        "estimated_cost_per_hectare": primary["cost_per_hectare"],
        "baseline_risk_score": round(baseline_risk),
        "interventions": interventions,
        "risk_factors": risk_factors,
        "next_steps": primary["implementation_steps"],
        "confidence_score": round(confidence, 3),
        "recommendation_source": "deterministic_threshold_engine",
        "decision_support_disclaimer": (
            "Prototype prioritisation support only; not an ecological diagnosis."
        ),
    }
