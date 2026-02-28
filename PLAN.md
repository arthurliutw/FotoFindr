# FotoFindr — Hackathon MVP Plan

> **Tagline:** *AI that understands your camera roll*

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [MVP Feature Scope](#mvp-feature-scope)
3. [System Architecture](#system-architecture)
4. [Tech Stack](#tech-stack)
5. [Image Processing Pipeline](#image-processing-pipeline)
6. [Database Layer](#database-layer)
7. [Natural Language Search](#natural-language-search)
8. [People Profiles System](#people-profiles-system)
9. [ElevenLabs Voice Narration](#elevenlabs-voice-narration)
10. [4-Person Team Breakdown](#4-person-team-breakdown)
11. [Task Board](#task-board)
12. [Demo Plan](#demo-plan)
13. [Feasibility & Constraints](#feasibility--constraints)

---

## Project Overview

FotoFindr is an AI-powered mobile app that gives users semantic intelligence over their photo library. Instead of scrolling endlessly, users describe what they want in plain English and the app finds it — powered by vision models, vector search, face clustering, and AI voice narration.

**Goal:** Ship a clean, interactive, demo-ready MVP in 36–48 hours.

---

## MVP Feature Scope

### Must Ship ✅
| Feature | Description |
|---|---|
| Photo Upload | Upload from mobile Expo app |
| Auto-Tagging | AI-generated descriptive tags per photo |
| Natural Language Search | "Find photos of me with my dog" |
| Low-Value Detection | Flag screenshots, blurry, accidental, duplicate photos |
| People Profiles | Named face clusters across the photo library |
| Emotion Detection | Per-face emotional state (happy, angry, neutral, etc.) |
| AI Voice Narration | ElevenLabs reads back search results |

### Out of Scope ❌
- Custom trained CV models
- Full production-grade photo sync
- Complex duplicate merging UI
- Google Photos feature parity

---

## System Architecture

```
┌─────────────────────────────────┐
│         Expo Mobile App         │
│  (Upload · Search · Profiles)   │
└────────────────┬────────────────┘
                 │ HTTPS
┌────────────────▼────────────────┐
│      Cloudflare API Gateway     │
│      (Routing + Rate Limit)     │
└────────────────┬────────────────┘
                 │
┌────────────────▼────────────────┐
│    FastAPI Backend (DigitalOcean)│
│  /upload  /search  /profiles    │
└──────┬──────────────┬───────────┘
       │              │
┌──────▼──────┐ ┌─────▼──────────┐
│   Image     │ │  Search API    │
│  Processing │ │  (Embeddings + │
│  Workers    │ │   Vector DB)   │
│  (Modal)    │ └────────────────┘
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│  Vector DB + Metadata DB        │
│  (Supermemory / pgvector)       │
│  (Snowflake / Actian)           │
└─────────────────────────────────┘
```

---

## Tech Stack

### Frontend
| Tool | Purpose |
|---|---|
| **Expo React Native** | Cross-platform mobile app |
| **Cloudflare** | API gateway, routing, CDN |
| **ElevenLabs SDK** | Voice narration playback |

### Backend
| Tool | Purpose |
|---|---|
| **Python + FastAPI** | REST API server |
| **DigitalOcean** | Hosting (Droplet or App Platform) |
| **Modal** | Async image processing workers (optional but impressive) |

### AI / Vision
| Tool | Purpose |
|---|---|
| **OpenAI Vision API** or **Gemini Vision** | Image captioning + tagging |
| **YOLO** or **Gemini structured output** | Object detection |
| **Presage API** | Emotion detection |
| **MediaPipe** | Face detection + bounding boxes |
| **OpenAI Embeddings** | Text + face vector embeddings |

### Data
| Tool | Purpose |
|---|---|
| **Snowflake** or **Actian** | Structured metadata storage |
| **Supermemory** or **pgvector** | Vector similarity search |

---

## Image Processing Pipeline

Every uploaded photo runs through this 5-step pipeline (can be parallelized via Modal):

### Step 1 — Vision Caption
**API:** OpenAI Vision or Gemini Vision

**Input:** Raw image

**Output:**
```json
{
  "caption": "A person wearing an orange sweater standing next to a golden retriever at a park.",
  "tags": ["person", "dog", "golden retriever", "park", "orange sweater", "outdoors"]
}
```

**Stored:** `caption`, `tags[]`

---

### Step 2 — Object Detection *(optional, high impact)*
**API:** YOLO or Gemini structured extraction

**Output:**
```json
{
  "objects": [
    { "label": "dog", "confidence": 0.94 },
    { "label": "person", "confidence": 0.99 }
  ]
}
```

**Stored:** `detected_objects[]`

---

### Step 3 — Emotion Detection
**API:** Presage API

**Output:**
```json
{
  "emotions": [
    { "face_id": 1, "dominant": "happy", "scores": { "happy": 0.87, "neutral": 0.10 } }
  ]
}
```

**Stored:** `emotion[]` per face

---

### Step 4 — Face Detection + Embeddings
**Tools:** MediaPipe (detection) + OpenAI Embeddings (or local model)

**Logic:**
```
detect faces → generate embedding per face
  → compare to existing clusters
    → if match found: attach to existing person profile
    → if no match: create new anonymous profile (cluster)
  → if user assigns name: update cluster label
```

**Stored:** `face_embeddings[]`, `person_cluster_id`

---

### Step 5 — Low-Value Photo Scoring
**Logic (heuristics, no ML needed):**

| Signal | Method |
|---|---|
| Screenshot | Aspect ratio + resolution heuristic |
| Blurry | Laplacian variance threshold |
| Empty / accidental | No faces + no significant objects |
| Monochrome | Low color variance |
| Duplicate | Perceptual hash match |
| Dark | Low brightness variance |

**Output:**
```json
{ "importance_score": 0.12, "flags": ["blurry", "no_objects"] }
```

**Stored:** `importance_score`, `low_value_flags[]`

---

## Database Layer

### Structured Metadata (Snowflake / Actian)
```sql
photos (
  id              UUID,
  user_id         UUID,
  storage_url     TEXT,
  caption         TEXT,
  tags            TEXT[],
  detected_objects JSONB,
  emotion         JSONB,
  person_ids      UUID[],
  importance_score FLOAT,
  low_value_flags TEXT[],
  created_at      TIMESTAMP
)

people (
  id              UUID,
  user_id         UUID,
  name            TEXT,           -- null until user assigns
  embedding_centroid VECTOR(1536),
  photo_count     INT
)
```

### Vector Store (Supermemory / pgvector)
```
Each photo gets an embedding vector generated from its caption + tags.
Stored alongside photo_id for retrieval.

Each face gets an embedding stored with person_cluster_id.
```

---

## Natural Language Search

**Example query:** `"Find photos of Jake where he looks happy at the beach"`

**Pipeline:**
```
1. Convert query text → embedding vector  (OpenAI)
2. Vector similarity search              (Supermemory / pgvector)
3. Apply metadata filters:
     person_name = "Jake"
     emotion.dominant = "happy"
     tags contains "beach"
4. Rank + return results
5. Generate narration summary            (ElevenLabs)
```

**Why it feels magical:** Users don't select filters — they just describe what they remember.

---

## People Profiles System

```
Upload 50 photos
         ↓
MediaPipe detects N faces across photos
         ↓
Embeddings clustered into groups
  → Cluster A: appears in 12 photos
  → Cluster B: appears in 34 photos
         ↓
User opens "People" tab → sees unnamed face groups
         ↓
User taps Cluster B → types "Jake"
         ↓
All 34 photos now tagged  person: Jake
         ↓
Search "photos of Jake" → instant results
```

---

## ElevenLabs Voice Narration

Triggered after every search result:

**Template:**
```
"I found {count} photos of {person} {emotion} at {location}.
 The most recent one was taken {relative_date}."
```

**Example output:**
> *"I found 12 photos of Jake smiling at the beach. The most recent one was taken last July."*

This is the single highest-impact wow moment in the demo.

---

## 4-Person Team Breakdown

### Person 1 — Backend & API
**Stack:** Python, FastAPI, DigitalOcean

**Owns:**
- [ ] FastAPI project scaffold + routes
- [ ] Image upload endpoint + storage (S3-compatible)
- [ ] Metadata write/read to Snowflake/Actian
- [ ] Search endpoint (orchestrates vector + metadata query)
- [ ] REST API contract (shared with Person 3)

**Key files:**
```
backend/
  main.py
  routes/upload.py
  routes/search.py
  routes/profiles.py
  db/metadata.py
```

---

### Person 2 — Vision & AI Pipeline
**Stack:** OpenAI/Gemini, Presage, MediaPipe, YOLO

**Owns:**
- [ ] Vision caption + tag extraction
- [ ] Object detection integration
- [ ] Presage emotion detection
- [ ] Face detection + embedding generation
- [ ] Face clustering logic
- [ ] Low-value photo scoring
- [ ] Pipeline runner (called by upload endpoint)

**Key files:**
```
pipeline/
  caption.py
  objects.py
  emotion.py
  faces.py
  scoring.py
  runner.py
```

---

### Person 3 — Expo Mobile App
**Stack:** Expo React Native, TypeScript

**Owns:**
- [ ] Photo picker + upload flow
- [ ] Search bar + results gallery
- [ ] People tab (face cluster list + name assignment)
- [ ] ElevenLabs narration playback
- [ ] Loading states + basic error handling

**Key screens:**
```
app/
  (tabs)/
    index.tsx        ← Home / Upload
    search.tsx       ← Natural language search
    people.tsx       ← People profiles
    cleanup.tsx      ← Low-value photo review
```

---

### Person 4 — Search, Vector DB & Infra
**Stack:** pgvector/Supermemory, OpenAI Embeddings, Cloudflare, ElevenLabs

**Owns:**
- [ ] Embedding pipeline (text → vector)
- [ ] Vector DB setup + indexing
- [ ] Semantic search query logic
- [ ] Cloudflare Workers routing config
- [ ] ElevenLabs narration API integration (backend side)
- [ ] Modal worker setup (if used)

**Key files:**
```
search/
  embed.py
  vector_store.py
  query.py
infra/
  cloudflare/worker.js
  modal_worker.py
```

---

## Task Board

### Phase 1 — Setup (Hours 0–3)
- [ ] Repo structure agreed, branches created
- [ ] API contract defined (request/response shapes)
- [ ] All API keys shared and `.env` template committed
- [ ] DigitalOcean droplet running, FastAPI reachable
- [ ] Expo app boots on device/simulator
- [ ] Vector DB provisioned

### Phase 2 — Core Build (Hours 3–24)
- [ ] Upload endpoint working end-to-end
- [ ] Vision caption running on uploaded image
- [ ] Tags stored in metadata DB
- [ ] Basic search endpoint returning results
- [ ] Mobile upload flow functional
- [ ] Face detection running

### Phase 3 — Intelligence Layer (Hours 24–36)
- [ ] Emotion detection integrated
- [ ] Face clustering + people profiles
- [ ] Low-value photo scoring
- [ ] Vector semantic search working
- [ ] People tab in app
- [ ] Narration triggered on search

### Phase 4 — Demo Polish (Hours 36–48)
- [ ] Pre-load 50 demo photos
- [ ] Seed "Jake" and other named profiles
- [ ] All 3 demo search queries verified working
- [ ] ElevenLabs narration smooth
- [ ] Cleanup suggestions screen working
- [ ] Rehearse demo flow 2x

---

## Demo Plan

**Setup:** Pre-load 50 diverse photos. Name at least 2 people in the profiles system.

**Demo Script (5 minutes):**

1. **Open app** → show camera roll uploaded, auto-tagged
2. **Search:** `"Photos where I look angry"` → results appear + voice narrates
3. **Search:** `"Pictures of Jake with my dog"` → cross-reference works
4. **Search:** `"Unimportant screenshots"` → low-value detection shown
5. **People tab** → show Jake's face cluster with 34 photos
6. **Cleanup screen** → "23 likely accidental screenshots found, review?"

**Punchline for judges:**
> "Every Google Photos user has thousands of photos they can't find. We made search feel like talking to someone who's seen every photo you've ever taken."

---

## Feasibility & Constraints

| Area | Feasibility (36–48 hrs) | Notes |
|---|---|---|
| Core upload + tagging | 9/10 | Straightforward API calls |
| Natural language search | 8/10 | Well-understood stack |
| Face clustering | 7/10 | Hardest part — time-box it |
| Emotion detection | 9/10 | Single Presage API call |
| Low-value detection | 9/10 | Pure heuristics, no ML |
| Voice narration | 9/10 | Simple ElevenLabs call |
| Polished UI | 5/10 | Deprioritize — ship intelligence |

### Risk Mitigation
| Risk | Mitigation |
|---|---|
| Face clustering is slow/wrong | Hard-code 2–3 named people for demo |
| Presage API issues | Fall back to basic caption-only emotion extraction |
| Vector DB setup time | Use pgvector locally if Supermemory takes too long |
| Modal integration complex | Skip Modal — run pipeline synchronously for demo |
| Mobile upload slow | Pre-process demo photos server-side before demo |

---

## Smart Cleanup Feature *(Bonus — if time allows)*

After processing:
```
"We detected 23 likely accidental screenshots and 8 blurry duplicates.
 Would you like to review them before deleting?"
```

This makes FotoFindr feel like a product, not a demo.

---

*Last updated: 2026-02-27*
