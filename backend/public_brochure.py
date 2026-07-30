"""Gemma 4 generation for bilingual public reef-alert brochures."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, ValidationError

try:
    from .gemma_orchestrator import (
        GemmaResponseError,
        GemmaUnavailableError,
        _ollama_chat,
        _ollama_model,
    )
except ImportError:  # Support direct execution from backend/.
    from gemma_orchestrator import (
        GemmaResponseError,
        GemmaUnavailableError,
        _ollama_chat,
        _ollama_model,
    )


class BrochureCopy(BaseModel):
    title: str = Field(min_length=1, max_length=140)
    alert_label: str = Field(min_length=1, max_length=80)
    introduction: str = Field(min_length=1, max_length=700)
    what_is_happening: list[str] = Field(min_length=2, max_length=5)
    why_it_matters: list[str] = Field(min_length=2, max_length=5)
    public_actions: list[str] = Field(min_length=3, max_length=6)
    reassurance: str = Field(min_length=1, max_length=500)
    official_information_note: str = Field(min_length=1, max_length=500)


class BilingualBrochure(BaseModel):
    english: BrochureCopy
    mauritian_creole: BrochureCopy


COPY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "alert_label": {"type": "string"},
        "introduction": {"type": "string"},
        "what_is_happening": {
            "type": "array",
            "items": {"type": "string"},
        },
        "why_it_matters": {
            "type": "array",
            "items": {"type": "string"},
        },
        "public_actions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "reassurance": {"type": "string"},
        "official_information_note": {"type": "string"},
    },
    "required": [
        "title",
        "alert_label",
        "introduction",
        "what_is_happening",
        "why_it_matters",
        "public_actions",
        "reassurance",
        "official_information_note",
    ],
    "additionalProperties": False,
}

BROCHURE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "english": COPY_SCHEMA,
        "mauritian_creole": COPY_SCHEMA,
    },
    "required": ["english", "mauritian_creole"],
    "additionalProperties": False,
}


def _prompt(alert: dict[str, Any]) -> str:
    return (
        "Create a bilingual public-education brochure for the reef alert below. "
        "Write for residents, fishers, boat operators, tourists, and school-age "
        "readers in Mauritius. Return English and a natural Mauritian Creole "
        "(Kreol Morisien) translation with the same facts and meaning.\n\n"
        "Rules:\n"
        "- Use calm, clear, non-technical language and short printable sentences.\n"
        "- Explain DHW, pH, temperature, or bleaching values in everyday language.\n"
        "- Do not invent measurements, causes, closures, forecasts, diagnoses, "
        "contact details, or government actions.\n"
        "- Do not tell the public to deploy restoration equipment or touch coral.\n"
        "- Give at least three safe, practical public actions such as avoiding "
        "contact with coral, reducing pollution, respecting marked zones, and "
        "following official guidance.\n"
        "- Make clear that monitoring alerts are early-warning information, not "
        "proof that every coral colony is damaged.\n"
        "- The official information note must tell readers to follow updates from "
        "Mauritian marine and environmental authorities; do not invent a URL.\n"
        "- Do not include Markdown, prices, fundraising requests, or political claims.\n"
        "- Follow the supplied JSON schema exactly.\n\n"
        "Alert evidence:\n"
        + json.dumps(alert, indent=2, ensure_ascii=False, default=str)
    )


def _fallback_copy(alert: dict[str, Any]) -> BilingualBrochure:
    site = str(alert.get("site_name") or "the monitored reef")
    alert_type = str(alert.get("alert_type") or "Reef health alert")
    severity = str(alert.get("severity") or "Warning")
    factors = [str(value) for value in alert.get("factors") or []]
    english_facts = factors or [
        "Monitoring instruments detected conditions that need closer observation.",
        "Reef conditions can change, so further checks are important.",
    ]
    creole_facts = [
        f"Nou bann instriman finn anrezistre sa lindikater-la: {factor}."
        for factor in factors
    ] or [
        "Bann instriman finn detekte bann kondision ki bizin plis sirveyans.",
        "Kondision lor resif kapav sanze, alor bizin kontign fer verifikasion.",
    ]

    return BilingualBrochure(
        english=BrochureCopy(
            title=f"Help protect the reef at {site}",
            alert_label=f"{severity}: {alert_type}",
            introduction=(
                "MauBuoy monitoring has identified conditions that may place the "
                "reef under stress. This is an early warning to support careful "
                "monitoring and responsible public behaviour."
            ),
            what_is_happening=english_facts[:5],
            why_it_matters=[
                "Healthy coral reefs support marine life, coastal protection, tourism, and fisheries.",
                "Reducing additional pressure gives coral a better chance to cope with environmental stress.",
            ],
            public_actions=[
                "Do not touch, stand on, collect, or anchor on coral.",
                "Keep litter, wastewater, fuel, and chemicals out of the sea.",
                "Respect marked marine zones and instructions from authorised officers.",
                "Share verified information and follow updates from official sources.",
            ],
            reassurance=(
                "An alert does not mean every coral colony is damaged. Scientists "
                "and reef managers use monitoring data to decide what checks are needed."
            ),
            official_information_note=(
                "For current advice, follow updates from Mauritian marine and "
                "environmental authorities."
            ),
        ),
        mauritian_creole=BrochureCopy(
            title=f"Ed protez resif dan {site}",
            alert_label=f"{severity}: {alert_type}",
            introduction=(
                "Sirveyans MauBuoy finn idantifie bann kondision ki kapav met resif "
                "anba presion. Sa se enn lavertisman boner pou ankouraz plis "
                "sirveyans ek enn konportman responsab."
            ),
            what_is_happening=creole_facts[:5],
            why_it_matters=[
                "Bann resif koray an bonn sante soutenir lavi marin, protez lakot, tourism ek lapes.",
                "Kan nou diminie lezot presion, koray gagn plis sans pou fer fas ar stres lanvironnman.",
            ],
            public_actions=[
                "Pa tous, pa mars lor, pa ramas, ek pa zet lank lor koray.",
                "Pa les salte, delo ize, karbiran ouswa prodwi simik rant dan lamer.",
                "Respekte bann zonn marin marke ek bann instriksion bann ofisie otorize.",
                "Partaz zis linformasion verifie ek swiv bann kominikasion ofisiel.",
            ],
            reassurance=(
                "Enn alert pa vedir ki tou koloni koray finn abime. Bann siantifik "
                "ek responsab resif servi done sirveyans pou deside ki verifikasion bizin fer."
            ),
            official_information_note=(
                "Pou bann konsey aktiel, swiv kominikasion bann lotorite marin ek "
                "lanvironnman Moris."
            ),
        ),
    )


def generate_public_brochure(alert: dict[str, Any]) -> dict[str, Any]:
    """Generate English and Kreol Morisien brochure copy with Gemma 4."""

    generated_at = datetime.now(timezone.utc).isoformat()
    try:
        response = _ollama_chat(
            {
                "model": _ollama_model(),
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a Mauritius ocean-education writer. Convert "
                            "monitoring evidence into accurate, calm, actionable "
                            "public information without adding unsupported claims."
                        ),
                    },
                    {"role": "user", "content": _prompt(alert)},
                ],
                "format": BROCHURE_SCHEMA,
                "stream": False,
                "think": False,
                "options": {
                    "temperature": 0.2,
                    "num_ctx": 6144,
                    "num_predict": 1500,
                },
            }
        )
        content = str(response["message"].get("content") or "")
        brochure = BilingualBrochure.model_validate_json(content)
        return {
            **brochure.model_dump(),
            "generation_source": "gemma4_ollama",
            "model": _ollama_model(),
            "generated_at": generated_at,
        }
    except (
        GemmaUnavailableError,
        GemmaResponseError,
        ValidationError,
        KeyError,
        ValueError,
    ) as exc:
        fallback = _fallback_copy(alert)
        return {
            **fallback.model_dump(),
            "generation_source": "deterministic_fallback_after_gemma_error",
            "model": _ollama_model(),
            "generated_at": generated_at,
            "gemma_error": str(exc),
        }
