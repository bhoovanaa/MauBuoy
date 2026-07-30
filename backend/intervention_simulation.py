"""Deterministic intervention ranking and scenario-impact calculations."""

from __future__ import annotations

from typing import Any

try:
    from .environmental_stress import calculate_environmental_stress
    from .restoration_knowledge_base import (
        RESTORATION_TECHNIQUES,
        rank_technique_recommendations,
    )
    from .roi_calculator import calculate_restoration_roi
except ImportError:
    from environmental_stress import calculate_environmental_stress
    from restoration_knowledge_base import (
        RESTORATION_TECHNIQUES,
        rank_technique_recommendations,
    )
    from roi_calculator import calculate_restoration_roi


DEFAULT_STEPS = {
    "temporary_shading": [
        "Map and prioritise colonies experiencing the highest heat and light exposure.",
        "Install storm-safe UV-filtering shade structures without contacting live coral.",
        "Record temperature, light and visual-health readings daily, then remove structures when acute stress subsides.",
    ],
    "coral_gardening": [
        "Confirm donor colonies and nursery sites with permits and genetic-diversity safeguards.",
        "Establish tagged nursery fragments and monitor survival, disease and growth monthly.",
        "Outplant only after environmental conditions stabilise and verify survival through a field survey.",
    ],
    "access_limit": [
        "Define a temporary exclusion zone around vulnerable colonies and anchoring areas.",
        "Coordinate signage, patrols and visitor communication with site managers and operators.",
        "Track compliance, turbidity and physical-damage indicators before reviewing the restriction.",
    ],
    "microfragmenting": [
        "Select suitable colonies and confirm species-specific handling protocols with specialists.",
        "Prepare tagged microfragments in a controlled nursery with disease screening.",
        "Outplant trial arrays, monitor tissue fusion and scale only after survival targets are met.",
    ],
    "substrate_stabilization": [
        "Survey unstable rubble and select structures suited to local hydrodynamics.",
        "Install a limited pilot without covering live colonies or altering navigation routes.",
        "Measure stability, recruitment and sediment movement before expanding the footprint.",
    ],
    "heat_resistant_outplanting": [
        "Verify heat-tolerant stock provenance, permits and genetic-diversity safeguards.",
        "Run a limited tagged outplanting pilot across representative microhabitats.",
        "Monitor survival, disease and bleaching through the next thermal-stress period before scaling.",
    ],
    "larval_propagation": [
        "Confirm spawning windows, broodstock diversity and a permitted larval-rearing protocol.",
        "Deploy settlement substrates only where water quality and sediment conditions meet thresholds.",
        "Measure settlement and juvenile survival at fixed intervals before repeating release.",
    ],
    "no_intervention_monitoring": [
        "Establish fixed photo quadrats and environmental monitoring thresholds.",
        "Set escalation triggers for mortality, disease, heat stress and water-quality deterioration.",
        "Review observations with marine specialists before initiating active restoration.",
    ],
}


def _timeline(technique: dict[str, Any]) -> str:
    days = int(technique.get("time_to_impact_days", 30))
    if days <= 1:
        return "Immediate"
    if days < 14:
        return f"{days} days"
    if days < 60:
        return f"{round(days / 7)} weeks"
    return f"{round(days / 30)} months"


def build_intervention_options(
    cv_output: dict[str, Any],
    sensor_data: dict[str, Any],
    location_name: str,
    baseline_risk_score: float,
    gemma_options: list[dict[str, Any]] | None = None,
    limit: int = 4,
) -> list[dict[str, Any]]:
    """Return at least three ranked options with grounded scenario impacts."""

    ranked = rank_technique_recommendations(cv_output, sensor_data, location_name)
    valid_ids = set(RESTORATION_TECHNIQUES)
    narratives: dict[str, dict[str, Any]] = {}
    requested_ids: list[str] = []

    for option in gemma_options or []:
        technique_id = str(option.get("technique_id") or "")
        if technique_id in valid_ids and technique_id not in requested_ids:
            requested_ids.append(technique_id)
            narratives[technique_id] = option

    for technique_id, _ in ranked:
        if technique_id not in requested_ids:
            requested_ids.append(technique_id)
        if len(requested_ids) >= max(3, limit):
            break

    stress = calculate_environmental_stress(
        water_temp_c=float(sensor_data["water_temp_c"]),
        ph_level=float(sensor_data["ph_level"]),
        turbidity_ntu=float(sensor_data["turbidity_ntu"]),
        salinity_ppt=float(sensor_data["salinity_ppt"]),
    )
    rank_scores = {technique_id: record["score"] for technique_id, record in ranked}
    health_status = str(cv_output.get("health", "unknown"))
    baseline = max(0, min(100, round(float(baseline_risk_score))))
    options: list[dict[str, Any]] = []

    for rank, technique_id in enumerate(requested_ids[: max(3, limit)], start=1):
        technique = RESTORATION_TECHNIQUES[technique_id]
        score = float(rank_scores.get(technique_id, 0))
        suitability = max(0.45, min(1.0, (score + 20) / 100))
        relative_reduction = (
            float(technique["risk_reduction_potential_percent"]) * suitability
        )
        reduction_points = min(
            baseline,
            max(1, round(baseline * relative_reduction / 100)),
        )
        projected = max(0, baseline - reduction_points)
        roi = calculate_restoration_roi(
            technique=technique_id,
            health_status=health_status,
            stress_score=float(stress["stress_score"]),
        )
        narrative = narratives.get(technique_id, {})
        steps = narrative.get("implementation_steps") or DEFAULT_STEPS[technique_id]
        caveats = narrative.get("caveats") or technique["limitations"]

        options.append(
            {
                "technique_id": technique_id,
                "rank": rank,
                "name": technique["name"],
                "summary": technique["description"],
                "rationale": narrative.get("rationale")
                or (
                    f"This option scored {score:.0f} in the site-condition match "
                    f"for {location_name}. It is a scenario for specialist review, "
                    "not a guaranteed reduction in bleaching."
                ),
                "implementation_steps": list(steps)[:6],
                "caveats": list(caveats)[:6],
                "cost_per_hectare": f"${technique['cost_per_hectare_usd']:,}",
                "timeline": _timeline(technique),
                "predicted_survival_rate": roi["predicted_survival_rate"],
                "recovery_boost_percent": technique["recovery_boost_percent"],
                "baseline_risk_score": baseline,
                "projected_risk_score": projected,
                "risk_reduction_points": reduction_points,
                "risk_reduction_percent": round(
                    (reduction_points / baseline * 100) if baseline else 0,
                    1,
                ),
                "confidence_score": round(0.45 + suitability * 0.45, 2),
                "impact_horizon_days": technique["time_to_impact_days"],
            }
        )

    return options
