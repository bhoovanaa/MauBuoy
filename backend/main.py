"""FastAPI integration layer for ReefGuardian AI."""

from __future__ import annotations

import os
from typing import Any, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
from starlette.concurrency import run_in_threadpool

# On Windows, scikit-learn and PyTorch both load native numerical runtimes.
# Initializing PyTorch first avoids a DLL/OpenMP initialization conflict when
# the environmental predictor is imported before the vision model.
if os.name == "nt":
    import torch as _torch  # noqa: F401

try:
    from .cv_model import ModelUnavailableError, VISION_SERVICE
    from .fusion import (
        deterministic_recommendation,
        fuse_assessments,
        normalize_visual_assessment,
    )
    from .predict_risk import predict_14_day_bleaching_risk
except ImportError:  # Support: uvicorn main:app from inside backend/
    from cv_model import ModelUnavailableError, VISION_SERVICE
    from fusion import (
        deterministic_recommendation,
        fuse_assessments,
        normalize_visual_assessment,
    )
    from predict_risk import predict_14_day_bleaching_risk


MAX_IMAGE_BYTES = int(os.getenv("REEFGUARDIAN_MAX_IMAGE_MB", "20")) * 1024 * 1024
MAX_VIDEO_BYTES = int(os.getenv("REEFGUARDIAN_MAX_VIDEO_MB", "500")) * 1024 * 1024
ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/jfif",
    "image/png",
    "image/webp",
    "image/bmp",
}
ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
    "application/octet-stream",
}


class EnvironmentalRiskRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    depth_m: float = Field(ge=0, le=200)
    dhw: float = Field(ge=0)
    coral_health: str = Field(default="unknown")
    sst_kelvin: float | None = Field(default=None, ge=250, le=330)
    water_temp_c: float | None = Field(default=None, ge=-2, le=50)

    @model_validator(mode="after")
    def require_temperature(self) -> "EnvironmentalRiskRequest":
        if self.sst_kelvin is None and self.water_temp_c is None:
            raise ValueError("Provide either sst_kelvin or water_temp_c.")
        return self

    def resolved_sst_kelvin(self) -> float:
        if self.sst_kelvin is not None:
            return self.sst_kelvin
        assert self.water_temp_c is not None
        return self.water_temp_c + 273.15


class FusionRequest(BaseModel):
    visual_assessment: dict[str, Any]
    environmental_assessment: dict[str, Any]


class SensorData(BaseModel):
    water_temp_c: float = Field(ge=-2, le=50)
    ph_level: float = Field(ge=0, le=14)
    salinity_ppt: float = Field(ge=0, le=60)
    turbidity_ntu: float = Field(ge=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    depth_m: float | None = Field(default=None, ge=0, le=200)
    sst_kelvin: float | None = Field(default=None, ge=250, le=330)
    dhw: float | None = Field(default=None, ge=0)
    timestamp: str | None = None


class RecommendationRequest(BaseModel):
    visual_assessment: dict[str, Any]
    sensor_data: SensorData
    location_name: str = Field(min_length=1, max_length=200)
    use_gemma: bool = True


class PublicBrochureRequest(BaseModel):
    alert_id: str = Field(min_length=1, max_length=200)
    alert_type: str = Field(min_length=1, max_length=200)
    severity: Literal["Warning", "Critical"]
    site_name: str = Field(min_length=1, max_length=200)
    buoy_name: str = Field(min_length=1, max_length=200)
    factors: list[str] = Field(default_factory=list, max_length=12)
    recommended_action: str = Field(min_length=1, max_length=500)


class AuditDecisionRequest(BaseModel):
    decision_key: str = Field(min_length=1, max_length=500)
    analysis_timestamp: str = Field(min_length=1, max_length=100)
    site_id: str = Field(min_length=1, max_length=200)
    site_name: str = Field(min_length=1, max_length=200)
    buoy_id: str = Field(min_length=1, max_length=200)
    buoy_name: str = Field(min_length=1, max_length=200)
    media_type: Literal["image", "video"]
    visual_condition: str = Field(min_length=1, max_length=200)
    visual_confidence: float = Field(ge=0, le=1)
    environmental_risk_score: float = Field(ge=0, le=100)
    environmental_risk_level: str = Field(min_length=1, max_length=50)
    fusion_priority: str = Field(min_length=1, max_length=50)
    recommendation_source: str = Field(min_length=1, max_length=200)
    ai_recommended_technique_id: str = Field(min_length=1, max_length=200)
    ai_recommended_technique_name: str = Field(min_length=1, max_length=200)
    selected_technique_id: str = Field(min_length=1, max_length=200)
    selected_technique_name: str = Field(min_length=1, max_length=200)
    selected_rank: int = Field(ge=1)
    selection_rationale: str = Field(min_length=1, max_length=4000)
    implementation_steps: list[str] = Field(min_length=1, max_length=20)
    caveats: list[str] = Field(default_factory=list, max_length=20)
    timeline: str = Field(min_length=1, max_length=200)
    predicted_survival_rate: str = Field(min_length=1, max_length=100)
    baseline_risk_score: float = Field(ge=0, le=100)
    projected_risk_score: float = Field(ge=0, le=100)
    risk_reduction_points: float = Field(ge=0, le=100)
    confidence_score: float = Field(ge=0, le=1)
    impact_horizon_days: int = Field(ge=1, le=3650)
    admin_name: str = Field(min_length=1, max_length=200)
    admin_notes: str = Field(default="", max_length=4000)


app = FastAPI(
    title="ReefGuardian AI",
    version="0.2.0",
    description=(
        "Coral photo/video assessment, environmental bleaching risk, "
        "evidence fusion, and restoration decision support."
    ),
)

cors_origins = [
    value.strip()
    for value in os.getenv(
        "REEFGUARDIAN_CORS_ORIGINS",
        "http://localhost:3000",
    ).split(",")
    if value.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def _read_upload(
    upload: UploadFile,
    maximum_bytes: int,
    allowed_types: set[str],
    kind: str,
) -> bytes:
    content_type = (upload.content_type or "application/octet-stream").lower()
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported {kind} type: {content_type}",
        )
    payload = await upload.read(maximum_bytes + 1)
    if len(payload) > maximum_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"{kind.title()} exceeds the configured upload limit.",
        )
    if not payload:
        raise HTTPException(status_code=400, detail=f"Uploaded {kind} is empty.")
    return payload


def _model_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ModelUnavailableError):
        return HTTPException(status_code=503, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail=f"Inference failed: {exc}")


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "service": "ReefGuardian AI",
        "status": "ready",
        "docs": "/docs",
        "model_status": VISION_SERVICE.model_status(),
    }


@app.get("/health")
def health() -> dict[str, Any]:
    status = VISION_SERVICE.model_status()
    return {
        "status": "ok" if status["yolo"]["available"] else "degraded",
        "models": status,
    }


@app.get("/models/status")
def models_status() -> dict[str, Any]:
    return VISION_SERVICE.model_status()


@app.post("/analyse-images")
async def analyse_images(
    files: list[UploadFile] = File(...),
    location: str = Form(..., min_length=1, max_length=200),
    refine_masks: bool = Form(False),
    include_artifacts: bool = Form(True),
) -> dict[str, Any]:
    """Detect coral across one or more photos and select up to three close-ups."""

    if not files:
        raise HTTPException(status_code=400, detail="Upload at least one image.")
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="A maximum of 20 images is allowed.")

    decoded_uploads: list[tuple[str, bytes]] = []
    for index, upload in enumerate(files):
        payload = await _read_upload(
            upload,
            maximum_bytes=MAX_IMAGE_BYTES,
            allowed_types=ALLOWED_IMAGE_TYPES,
            kind="image",
        )
        decoded_uploads.append((upload.filename or f"image-{index}", payload))

    try:
        result = await run_in_threadpool(
            VISION_SERVICE.analyze_images,
            decoded_uploads,
            refine_masks,
            include_artifacts,
        )
    except Exception as exc:
        raise _model_error(exc) from exc
    return {"location": location, "visual_assessment": result}


app.add_api_route(
    "/analyze-images",
    analyse_images,
    methods=["POST"],
    include_in_schema=False,
)


@app.post("/analyse-video")
async def analyse_video(
    file: UploadFile = File(...),
    location: str = Form(..., min_length=1, max_length=200),
    include_artifacts: bool = Form(True),
) -> dict[str, Any]:
    """Sample a video, reject weak detections, and remove duplicate close-ups."""

    payload = await _read_upload(
        file,
        maximum_bytes=MAX_VIDEO_BYTES,
        allowed_types=ALLOWED_VIDEO_TYPES,
        kind="video",
    )
    try:
        result = await run_in_threadpool(
            VISION_SERVICE.analyze_video,
            payload,
            file.filename or "upload.mp4",
            include_artifacts,
        )
    except Exception as exc:
        raise _model_error(exc) from exc
    return {"location": location, "visual_assessment": result}


app.add_api_route(
    "/analyze-video",
    analyse_video,
    methods=["POST"],
    include_in_schema=False,
)


@app.post("/environment-risk")
def environment_risk(request: EnvironmentalRiskRequest) -> dict[str, Any]:
    return predict_14_day_bleaching_risk(
        latitude=request.latitude,
        longitude=request.longitude,
        depth=request.depth_m,
        sst_kelvin=request.resolved_sst_kelvin(),
        dhw=request.dhw,
        coral_health=request.coral_health,
    )


@app.post("/fuse")
def fuse(request: FusionRequest) -> dict[str, Any]:
    return fuse_assessments(
        visual=request.visual_assessment,
        environmental=request.environmental_assessment,
    )


@app.post("/recommendation")
async def recommendation(request: RecommendationRequest) -> dict[str, Any]:
    """Return deterministic guidance, or Gemma/Ollama guidance when requested."""

    normalized_visual = normalize_visual_assessment(request.visual_assessment)
    if normalized_visual["status"] != "ok":
        raise HTTPException(
            status_code=422,
            detail=(
                "Reliable coral detection is required before generating "
                "restoration recommendations."
            ),
        )

    sensor_data = request.sensor_data.model_dump(exclude_none=True)
    fallback = deterministic_recommendation(
        cv_output=request.visual_assessment,
        sensor_data=sensor_data,
        location_name=request.location_name,
    )
    if not request.use_gemma:
        return fallback

    try:
        try:
            from .gemma_orchestrator import analyze_reef
        except ImportError:
            from gemma_orchestrator import analyze_reef

        gemma_result = await run_in_threadpool(
            analyze_reef,
            normalized_visual,
            sensor_data,
            request.location_name,
        )
        if gemma_result.get("alert_level") == "ERROR":
            return {
                **fallback,
                "gemma_error": gemma_result.get("reasoning"),
                "recommendation_source": "deterministic_fallback_after_gemma_error",
            }
        gemma_result["recommendation_source"] = "gemma4_ollama"
        gemma_result["decision_support_disclaimer"] = (
            "Prototype prioritisation support only; not an ecological diagnosis."
        )
        return gemma_result
    except Exception as exc:
        return {
            **fallback,
            "gemma_error": str(exc),
            "recommendation_source": "deterministic_fallback_after_gemma_error",
        }


@app.get("/gemma/status")
def gemma_status() -> dict[str, Any]:
    """Report whether Ollama and the configured Gemma 4 model are ready."""

    try:
        try:
            from .gemma_orchestrator import get_gemma_status
        except ImportError:
            from gemma_orchestrator import get_gemma_status
        return get_gemma_status()
    except Exception as exc:
        return {
            "status": "unavailable",
            "model": os.getenv("REEFGUARDIAN_OLLAMA_MODEL", "gemma4"),
            "installed": False,
            "error": str(exc),
        }


@app.post("/public-brochure")
async def public_brochure(request: PublicBrochureRequest) -> dict[str, Any]:
    """Generate bilingual public-education copy for an active reef alert."""

    try:
        try:
            from .public_brochure import generate_public_brochure
        except ImportError:
            from public_brochure import generate_public_brochure

        return await run_in_threadpool(
            generate_public_brochure,
            request.model_dump(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Brochure generation failed: {exc}",
        ) from exc


@app.post("/audit/decisions", status_code=201)
def create_audit_decision(request: AuditDecisionRequest) -> dict[str, Any]:
    """Persist a human-confirmed intervention as an approved learning example."""

    try:
        try:
            from .audit_store import save_intervention_decision
        except ImportError:
            from audit_store import save_intervention_decision
        return save_intervention_decision(request.model_dump())
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not save the audit decision: {exc}",
        ) from exc


@app.get("/audit/decisions")
def get_audit_decisions(limit: int = 100) -> list[dict[str, Any]]:
    """Return the newest confirmed intervention decisions."""

    safe_limit = max(1, min(limit, 500))
    try:
        try:
            from .audit_store import list_intervention_decisions
        except ImportError:
            from audit_store import list_intervention_decisions
        return list_intervention_decisions(safe_limit)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not load the audit log: {exc}",
        ) from exc


@app.get("/audit/learning-summary")
def get_audit_learning_summary() -> dict[str, Any]:
    """Aggregate approved choices for a controlled future learning cycle."""

    try:
        try:
            from .audit_store import intervention_learning_summary
        except ImportError:
            from audit_store import intervention_learning_summary
        return intervention_learning_summary()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not build the learning summary: {exc}",
        ) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("REEFGUARDIAN_HOST", "0.0.0.0"),
        port=int(os.getenv("REEFGUARDIAN_PORT", "8000")),
        reload=False,
    )
