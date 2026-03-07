# ML Atlas - Claude Code Instructions

## Project Overview

ML Atlas is a machine learning documentation and experimentation platform.
It documents, implements, and provides interactive labs for 278 ML algorithms
across 10 major categories. It serves as both a personal knowledge system
and a public portfolio.

**Phase:** Currently in Phase 1 (Foundation setup).
**Total Algorithms:** 278 (see `Documentation/ml_algorithm_atlas_expanded.csv`).
**Content Status:** Tracked per algorithm in the `implementation_status` DB table
and in each MDX frontmatter `status` field.

---

## Repository Structure

```
ml-atlas/
├── frontend/nextjs-site/     # NextJS App Router site
├── backend/fastapi-server/   # FastAPI Python backend
├── labs/                     # Streamlit/Gradio microservices per algorithm
│   ├── _shared/              # Shared Python helpers (dataset_loader, plot_utils)
│   ├── supervised/
│   ├── unsupervised/
│   ├── deep_learning/
│   └── reinforcement_learning/
├── database/
│   └── seeds/                # Seed scripts to populate algorithms from CSV
├── content/
│   ├── algorithms/           # MDX files (one per algorithm, created incrementally)
│   └── categories/           # Category overview MDX files
├── notebooks/experiments/    # Jupyter exploration notebooks
├── datasets/                 # Raw and processed datasets
└── Documentation/            # PRD and algorithm CSV source of truth
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | NextJS 15 (App Router), TypeScript, Tailwind CSS, MDX |
| Backend | Python 3.12, FastAPI, SQLModel, Alembic |
| Database | Supabase (Postgres) |
| Labs | Streamlit or Gradio (per-algorithm microservices) |
| Package Manager (Python) | uv |
| Package Manager (JS) | pnpm |
| Python Linting/Formatting | ruff |
| JS Linting | ESLint |
| JS Formatting | Prettier |
| Python Testing | pytest |
| JS Testing | Vitest |

---

## Environment Variables

All secrets live in `.env` files that are gitignored. Never commit `.env`.
See `.env.example` for required variables.

Required variables:
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_ANON_KEY` — Public anon key
- `SUPABASE_SERVICE_ROLE_KEY` — Server-side key (backend only, never frontend)
- `DATABASE_URL` — Postgres connection string for Alembic
- `NEXT_PUBLIC_API_URL` — FastAPI base URL (exposed to browser)
- `NEXT_PUBLIC_SUPABASE_URL` — Supabase URL (exposed to browser)
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` — Supabase anon key (exposed to browser)
- `LAB_BASE_URL` — Base URL for lab microservices

---

## Common Commands

### Frontend (run from `frontend/nextjs-site/`)
```bash
pnpm dev              # Start dev server (localhost:3000)
pnpm build            # Production build
pnpm lint             # ESLint
pnpm format           # Prettier
pnpm test             # Vitest
pnpm type-check       # tsc --noEmit
```

### Backend (run from `backend/fastapi-server/`)
```bash
uv sync                                               # Install all dependencies
uv run fastapi dev app/main.py                        # Dev server with hot reload (localhost:8000)
uv run alembic upgrade head                           # Run pending migrations
uv run alembic revision --autogenerate -m "desc"      # Create migration from model changes
uv run pytest                                         # Run tests
uv run ruff check .                                   # Lint
uv run ruff format .                                  # Format
```

### Labs (run from individual lab directory, e.g., `labs/unsupervised/kmeans/`)
```bash
# Streamlit lab
pip install -r requirements.txt
streamlit run app.py --server.port 8501

# Gradio lab
pip install -r requirements.txt
python app.py
```

### Database Seeds (run from `database/seeds/`)
```bash
uv run python seed_algorithms.py    # Populate algorithms + implementation_status from CSV
```

### Docker (for labs)
```bash
docker build -t ml-atlas-kmeans-lab ./labs/unsupervised/kmeans/
docker run -p 8501:8501 ml-atlas-kmeans-lab
```

---

## MDX Content Schema

Every algorithm MDX file **must** have this frontmatter:

```yaml
---
title: "Random Forest Classifier"
slug: "random-forest-classifier"
category: "supervised"
subcategory: "classification"
year: 2001
author: "Leo Breiman"
paper: "Random Forests (2001)"
complexity: "medium"          # low | medium | high
status: "planned"             # planned | in-progress | documented | implemented | lab-ready
compatibility:
  tabular: true
  image: false
  text: false
  timeseries: false
  graph: false
tags: ["ensemble", "bagging", "trees", "classification"]
lab_url: ""                   # Leave empty until lab is built
lab_framework: ""             # streamlit | gradio
related:
  - "decision-tree-classifier"
  - "extra-trees-classifier"
  - "gradient-boosting-classifier"
---
```

**MDX section order** — every algorithm should follow this order:

1. `## Overview` — One-paragraph description
2. `## History` — When and who invented it
3. `## Mathematical Intuition` — Core math (use KaTeX `$$...$$`)
4. `## Algorithm Steps` — Numbered procedural steps
5. `## Parameters` — Table of parameters with defaults and ranges
6. `## Compatibility` — Data type compatibility (use `<CompatibilityMatrix />` component)
7. `## Strengths` — Bullet list
8. `## Weaknesses` — Bullet list
9. `## Use Cases` — Domain examples
10. `## Implementation` — Code blocks (from scratch, then library usage)
11. `## Lab` — Link/embed to interactive lab
12. `## References` — Paper links

MDX files live at: `content/algorithms/{category}/{subcategory}/{slug}.mdx`

Example: `content/algorithms/supervised/classification/random-forest-classifier.mdx`

---

## NextJS Routing Strategy

```
/                                    → Home page
/algorithms                          → Browse all 278 algorithms
/algorithms/[category]               → Category index (e.g., /algorithms/supervised)
/algorithms/[category]/[slug]        → Individual algorithm page
/labs                                → Labs index
/labs/[slug]                         → Lab embed page
/search                              → Search/filter algorithms
/progress                            → Implementation progress dashboard
```

**URL slug convention:** `kebab-case` matching MDX filename without `.mdx` extension.

**Category slugs:**

| CSV Category | URL Slug | Count |
|---|---|---|
| Supervised Learning | `supervised` | 64 |
| Unsupervised Learning | `unsupervised` | 50 |
| Probabilistic & Bayesian | `probabilistic` | 18 |
| Time Series & Forecasting | `time-series` | 18 |
| Deep Learning | `deep-learning` | 57 |
| Generative Models | `generative` | 17 |
| Graph Machine Learning | `graph` | 12 |
| Reinforcement Learning | `reinforcement` | 27 |
| Meta-Learning & AutoML | `meta-learning` | 15 |
| Evolutionary & Fuzzy Methods | `evolutionary` | 8 |

**Static generation strategy:**
- All `/algorithms/*` routes are statically generated at build time using `generateStaticParams()` reading MDX files from disk.
- The `/progress` and `/search` pages fetch from the FastAPI backend at request time (dynamic).

---

## FastAPI Endpoint Design

Base URL: `http://localhost:8000/api/v1`

```
GET  /algorithms                   # List all; supports ?category=&subcategory=&status=&complexity=
GET  /algorithms/{id}              # Single algorithm by DB id
GET  /algorithms/by-slug/{slug}    # Single algorithm by slug
GET  /categories                   # All categories with counts
GET  /categories/{slug}            # Category detail with algorithm list
GET  /labs                         # All labs
GET  /labs/{algorithm_slug}        # Lab for a specific algorithm
GET  /notes/{algorithm_id}         # Notes for an algorithm
POST /notes                        # Create a note
PUT  /notes/{note_id}              # Update a note
GET  /status                       # All implementation statuses (progress dashboard)
GET  /status/{algorithm_id}        # Status for one algorithm
PUT  /status/{algorithm_id}        # Update status fields
GET  /search?q=                    # Text search (Phase 4: pgvector semantic search)
```

All list responses follow this envelope:
```json
{ "data": [...], "meta": { "total": 278, "page": 1 } }
```

---

## Database Models (SQLModel)

Located at `backend/fastapi-server/app/models/`.

**Five tables:** `algorithms`, `algorithm_parameters`, `algorithm_notes`, `labs`, `implementation_status`

Key model pattern:
```python
class AlgorithmBase(SQLModel):
    name: str
    slug: str          # kebab-case, unique
    category: str      # URL slug (e.g., "supervised")
    subcategory: str
    year: Optional[int]
    author: Optional[str]
    paper_reference: Optional[str]
    complexity: str    # "low" | "medium" | "high"
    best_use_case: Optional[str]
    description: Optional[str]
    compatibility_tabular: bool = False
    compatibility_image: bool = False
    compatibility_text: bool = False
    compatibility_graph: bool = False
    compatibility_timeseries: bool = False

class Algorithm(AlgorithmBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    # Relationships to parameters, notes, lab, status
```

**Migration strategy:**
- Alembic manages all schema changes.
- Migration files: `backend/fastapi-server/alembic/versions/`.
- Never edit a migration file after it has been applied.
- Naming: `{NNN}_{snake_case_description}.py` (e.g., `001_initial_schema.py`).

---

## Lab Organization Pattern

Each lab is a self-contained Python microservice.
Path: `labs/{category}/{algorithm_slug}/`

Every lab directory contains:
- `app.py` — Main entry point (Streamlit or Gradio)
- `requirements.txt` — Lab-specific Python dependencies
- `Dockerfile` — Container definition

**Streamlit lab `app.py` structure:**
```python
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "_shared"))
from dataset_loader import load_dataset, AVAILABLE_DATASETS
from plot_utils import create_scatter_plot

st.set_page_config(page_title="Algorithm Name Lab | ML Atlas", layout="wide")
st.title("Algorithm Name")
st.markdown("[← Back to ML Atlas](http://localhost:3000/algorithms/{category}/{slug})")

# Sidebar: dataset selector + algorithm parameters
# Main area: visualization + metrics
```

When a lab is complete, register it in the DB via `POST /api/v1/labs`.

---

## Content Workflow (Adding a New Algorithm)

Follow this order every time:

1. **Check the CSV** — `Documentation/ml_algorithm_atlas_expanded.csv` is the source of truth. Find the algorithm row.
2. **Create the MDX file** — At `content/algorithms/{category}/{subcategory}/{slug}.mdx`. Copy the frontmatter template. Set `status: "in-progress"`.
3. **Fill MDX sections** — Research and fill each section in order. Set `status: "documented"` when complete.
4. **Update the DB record** — The algorithm already exists (seeded from CSV). Update `description`, `best_use_case`, and compatibility fields.
5. **Add notes** — Use `POST /api/v1/notes` to save research findings.
6. **Build the lab** — Create `labs/{category}/{slug}/app.py`. Set `status: "implemented"` after from-scratch code is in the MDX. Set `status: "lab-ready"` after lab runs.
7. **Register the lab** — `POST /api/v1/labs` to register the lab URL.
8. **Update MDX `lab_url`** — Add the running lab URL to frontmatter.

---

## Implementation Status Values

| Value | Meaning |
|---|---|
| `planned` | Listed in CSV, not started |
| `in-progress` | MDX file created, being written |
| `documented` | All MDX sections filled |
| `implemented` | From-scratch code added to MDX |
| `lab-ready` | Interactive lab built and running |

---

## Code Style Conventions

### TypeScript / NextJS
- Use **named exports** for all components (no `default export`).
- Use React Server Components by default; add `"use client"` only when needed.
- Fetch data in Server Components using `async/await` directly.
- All API calls to FastAPI go through `src/lib/api-client.ts`.
- Component props must be typed with explicit interfaces.
- File naming: PascalCase for components, camelCase for utilities.

### Python / FastAPI
- All endpoints return typed Pydantic response models.
- Use `async def` for all route handlers.
- CRUD logic lives in `crud/` files, never in route files.
- Route files only handle HTTP concerns (validation, response codes).
- All DB operations use SQLModel sessions via dependency injection.
- Use `ruff` for both linting and formatting.

### MDX
- Every MDX file must have complete frontmatter (all required fields).
- Math equations use KaTeX: inline `$...$`, block `$$...$$`.
- Code blocks must specify the language: ` ```python `.
- Use the custom `<Callout type="info">` component for notes/tips.

---

## Important Paths Reference

| Purpose | Path |
|---|---|
| Algorithm CSV source | `Documentation/ml_algorithm_atlas_expanded.csv` |
| MDX algorithm content | `content/algorithms/{category}/{subcategory}/{slug}.mdx` |
| Category overviews | `content/categories/{slug}.mdx` |
| FastAPI app entry | `backend/fastapi-server/app/main.py` |
| FastAPI models | `backend/fastapi-server/app/models/` |
| FastAPI routes | `backend/fastapi-server/app/api/v1/` |
| FastAPI CRUD | `backend/fastapi-server/app/crud/` |
| Alembic migrations | `backend/fastapi-server/alembic/versions/` |
| Seed scripts | `database/seeds/` |
| Lab apps | `labs/{category}/{slug}/app.py` |
| Shared lab utils | `labs/_shared/` |
| Jupyter notebooks | `notebooks/experiments/{category}/` |
| NextJS app routes | `frontend/nextjs-site/src/app/` |
| NextJS components | `frontend/nextjs-site/src/components/` |
| NextJS MDX lib | `frontend/nextjs-site/src/lib/mdx.ts` |
| NextJS API client | `frontend/nextjs-site/src/lib/api-client.ts` |
| TypeScript types | `frontend/nextjs-site/src/types/` |

---

## Do Not

- Do not commit `.env` files.
- Do not edit Alembic migration files after applying them.
- Do not put business logic in FastAPI route files (use `crud/`).
- Do not use `default export` in TypeScript components.
- Do not add `"use client"` to components that do not need it.
- Do not store large datasets in the repo. Use `datasets/raw/` (gitignored).
- Do not hardcode API URLs outside of `src/lib/api-client.ts`.
- Do not create an MDX file without complete frontmatter.
- Do not skip the content workflow order — always seed first, then document, then implement, then lab.
