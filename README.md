# MauBuoy ReefGuardian

MauBuoy ReefGuardian is a full-stack decision-support prototype for coral
conservation in Mauritius.

## Project structure

```text
MauBuoy-2/
├── backend/        FastAPI, YOLO/SAM inference, fusion and recommendations
├── frontend/       Next.js monitoring and media-analysis dashboard
├── data/           Environmental training and validation datasets
├── requirements.txt
└── README.md
```

The system combines:

- YOLO11n coral detection and Healthy/Bleached/Dead classification.
- A conservative reliability gate that can return `Uncertain`.
- Sampled video analysis with near-duplicate close-up removal.
- Environmental bleaching-risk prediction.
- Explicit visual/environmental fusion and restoration recommendations.

The API keeps visual health and environmental risk as independent evidence. It
does not manufacture a visual `Stressed` class, and it preserves review flags
when the two model layers disagree.

## Backend setup

Python is not bundled with the repository. Python 3.11 is recommended for the
pinned scientific packages.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The integrated local checkpoints are expected at:

```text
backend/models/reefguardian_yolo11n_best.pt
backend/models/vit_b_coralscop.pth
```

They are ignored by Git because together they are about 370 MB. Their expected
checksums and roles are recorded in `backend/models/README.md`.

## Run

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000/docs` for the interactive API.

Run the lightweight integration contract checks with:

```powershell
.\.venv\Scripts\python.exe -m unittest backend.test_integration_contract
```

## Frontend setup

In a second terminal:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Open `http://localhost:3000`. Both frontend commands are fixed to port 3000,
and the backend accepts requests from that frontend origin only. The frontend
calls the backend URL configured by `NEXT_PUBLIC_API_BASE_URL`.

## Integrated API flow

1. `POST /analyse-images` accepts one or more images plus a mandatory
   `location`. Set `refine_masks=true` to run CoralSCOP SAM on the selected
   YOLO boxes.
2. `POST /analyse-video` samples about one frame per second, up to 240 frames,
   then removes near-duplicate crops.
3. `POST /environment-risk` runs the existing bleaching-risk model.
4. `POST /fuse` combines the visual and environmental responses without
   concealing disagreement.
5. `POST /recommendation` returns auditable threshold-based guidance. Set
   `use_gemma=true` (the default) to run the Gemma 4 tool-calling analysis
   through local Ollama; the endpoint falls back safely if Ollama is unavailable.

## Gemma 4 setup

Install Ollama for Windows, then pull the configured Gemma 4 model:

```powershell
ollama pull gemma4
ollama run gemma4
```

Ollama serves its local API at `http://localhost:11434`. Check integration
readiness at `http://localhost:8000/gemma/status`. The model and host can be
changed with `REEFGUARDIAN_OLLAMA_MODEL` and `REEFGUARDIAN_OLLAMA_HOST`.

US-spelling aliases `/analyze-images` and `/analyze-video` are also accepted.

### Image request

```powershell
curl.exe -X POST "http://localhost:8000/analyse-images" `
  -F "location=Blue Bay Marine Park" `
  -F "refine_masks=false" `
  -F "include_artifacts=true" `
  -F "files=@C:\path\reef-1.jpg" `
  -F "files=@C:\path\reef-2.jpg"
```

`include_artifacts=false` omits base64 JPEG/PNG payloads for a smaller response.
SAM refinement is optional because ViT-B is substantially heavier than YOLO,
especially on CPU.

### Environmental request

```json
{
  "latitude": -20.4,
  "longitude": 57.7,
  "depth_m": 5,
  "water_temp_c": 29.8,
  "dhw": 4.5,
  "coral_health": "bleached"
}
```

## Reliability controls

Accepted YOLO detections must satisfy all recorded report thresholds:

- Confidence at least 0.50.
- Box area ratio from 0.015 through 0.80.
- Crop Laplacian sharpness at least 25.

Accepted detections are ranked with confidence as the dominant term, followed
by target area, sharpness, and boundary clearance. No accepted detection means
`status=no_reliable_coral_detected` and `overall_condition=Uncertain`.

This is a hackathon decision-support prototype, not a substitute for field
assessment by marine scientists.

## Contributors

MauBuoy ReefGuardian was developed as a collaborative project.

- [bhoovanaa](https://github.com/bhoovanaa)
- [alexandra-leung](https://github.com/alexandra-leung)