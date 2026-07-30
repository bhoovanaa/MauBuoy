# MauBuoy frontend

Next.js dashboard for the ReefGuardian backend.

## Configure

Copy `.env.example` to `.env.local`. The default expects FastAPI at
`http://localhost:8000`.

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Run

```powershell
npm ci
npm run dev
```

Open `http://localhost:3000`. Both `npm run dev` and `npm run start` are fixed
to this port.

The buoy dashboard sends each upload through one typed workflow:

1. `/analyse-images` or `/analyse-video`
2. `/environment-risk`
3. `/fuse`
4. `/recommendation`

## Validate

```powershell
npm run lint
npm run build
```

Static site and buoy metadata remain in `src/lib/constants.ts`. Backend request
logic is kept in `src/lib/api/reefguardian.ts`, and response contracts are in
`src/components/shared/api/types.ts`.
