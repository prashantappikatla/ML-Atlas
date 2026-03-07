# ML Atlas

A machine learning documentation and experimentation platform. Documents, implements, and provides interactive labs for 278 ML algorithms across 10 major categories.

## Structure

```
ml-atlas/
├── frontend/nextjs-site/     # NextJS 15 App Router + MDX
├── backend/fastapi-server/   # FastAPI + SQLModel + Supabase
├── labs/                     # Streamlit/Gradio per-algorithm microservices
├── content/algorithms/       # MDX files (one per algorithm)
├── database/seeds/           # CSV → Supabase seed scripts
├── notebooks/experiments/    # Jupyter notebooks for exploration
└── datasets/                 # Raw and processed datasets
```

## Quick Start

See `CLAUDE.md` for full project instructions and conventions.

### Backend
```bash
cd backend/fastapi-server
uv sync
uv run alembic upgrade head
uv run python ../../database/seeds/seed_algorithms.py
uv run fastapi dev app/main.py
```

### Frontend
```bash
cd frontend/nextjs-site
pnpm install
pnpm dev
```

## Algorithm Coverage

| Category | Count |
|---|---|
| Supervised Learning | 64 |
| Unsupervised Learning | 50 |
| Deep Learning | 57 |
| Reinforcement Learning | 27 |
| Probabilistic & Bayesian | 18 |
| Time Series & Forecasting | 18 |
| Generative Models | 17 |
| Meta-Learning & AutoML | 15 |
| Graph Machine Learning | 12 |
| Evolutionary & Fuzzy Methods | 8 |
| **Total** | **278** |
