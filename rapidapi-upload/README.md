# RapidAPI Upload Folder

This folder exists so you have a clear, dedicated location to navigate to when uploading the OpenAPI spec to RapidAPI.

## How to Upload

1. Open **RapidAPI Studio** → your API → **Hub Listing** tab → **Import Requests**
2. Click **"Upload a File"** (do NOT drag-and-drop — it currently fails)
3. In the file picker, navigate to: `ContentForge/deploy/openapi.json`
4. Select it and confirm

The spec lives at `deploy/openapi.json` in the repo root.

## Why drag-and-drop fails

RapidAPI's import dialog drops the file reference when you release it over the wrong target area. The **Upload a File** button opens a proper file picker which works reliably.

## Current Spec Status

- **27 endpoints** documented (15 instant heuristic scorers + 11 AI generators + 1 health)
- All tags correct: `Content Analysis`, `AI Content Generation`, `System`
- Server: `https://contentforge-api-lpp9.onrender.com`
- Version: `1.0.0`
