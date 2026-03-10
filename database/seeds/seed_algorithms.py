"""
Seed script: Reads Documentation/ml_algorithm_atlas_expanded.csv and inserts
all 278 algorithms + implementation_status rows into the Supabase database.

Run from repo root:
    cd backend/fastapi-server
    uv run python ../../database/seeds/seed_algorithms.py

Or from database/seeds/:
    uv run python seed_algorithms.py

Idempotent: skips rows where slug already exists.
"""

import csv
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import Session, create_engine, select

# Ensure we can import backend models
BACKEND_PATH = Path(__file__).parent.parent.parent / "backend" / "fastapi-server"
sys.path.insert(0, str(BACKEND_PATH))

from app.models.algorithm import Algorithm
from app.models.status import ImplementationStatus

CSV_PATH = Path(__file__).parent.parent.parent / "Documentation" / "ml_algorithm_atlas_expanded.csv"

# Load environment variables from .env files (backend and repo root)
REPO_ROOT = Path(__file__).parent.parent.parent
BACKEND_ENV = BACKEND_PATH / ".env"
ROOT_ENV = REPO_ROOT / ".env"

if BACKEND_ENV.exists():
    load_dotenv(BACKEND_ENV, override=False)
if ROOT_ENV.exists():
    load_dotenv(ROOT_ENV, override=False)

# Map CSV category names to URL slugs
CATEGORY_MAP = {
    "Supervised Learning": "supervised",
    "Unsupervised Learning": "unsupervised",
    "Probabilistic & Bayesian": "probabilistic",
    "Time Series & Forecasting": "time-series",
    "Deep Learning": "deep-learning",
    "Generative Models": "generative",
    "Graph Machine Learning": "graph",
    "Reinforcement Learning": "reinforcement",
    "Meta-Learning & AutoML": "meta-learning",
    "Evolutionary & Fuzzy Methods": "evolutionary",
}


def to_slug(name: str) -> str:
    """Convert algorithm name to kebab-case URL slug."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9\s\-]", "", name)
    name = re.sub(r"[\s_]+", "-", name)
    name = re.sub(r"-+", "-", name)
    return name.strip("-")


def parse_year(value: str) -> int | None:
    """Parse year from CSV, return None if missing or invalid."""
    if not value or not value.strip():
        return None
    try:
        return int(value.strip().split("-")[0].split("s")[0][:4])
    except (ValueError, IndexError):
        return None


def parse_complexity(value: str) -> str:
    """Normalize complexity to low/medium/high."""
    if not value:
        return "medium"
    v = value.strip().lower()
    if v in ("low", "l"):
        return "low"
    if v in ("high", "h"):
        return "high"
    return "medium"


def seed(database_url: str | None = None) -> None:
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: Set DATABASE_URL environment variable or pass database_url argument.")
        sys.exit(1)

    engine = create_engine(url)

    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}")
        sys.exit(1)

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Found {len(rows)} rows in CSV.")
    inserted = 0
    skipped = 0

    with Session(engine) as session:
        for row in rows:
            # Column names taken from Documentation/ml_algorithm_atlas_expanded.csv
            name = row.get("Algorithm", "").strip()
            if not name:
                continue

            slug = to_slug(name)
            category_raw = row.get("Category", "").strip()
            subcategory = row.get("Subcategory", "").strip().lower().replace(" ", "-")
            category = CATEGORY_MAP.get(category_raw, category_raw.lower().replace(" ", "-"))

            # Skip if already exists
            existing = session.exec(select(Algorithm).where(Algorithm.slug == slug)).first()
            if existing:
                skipped += 1
                continue

            algorithm = Algorithm(
                name=name,
                slug=slug,
                category=category,
                subcategory=subcategory,
                year=parse_year(row.get("Year Introduced", "")),
                author=row.get("Original Paper / Author", "").strip() or None,
                paper_reference=row.get("Original Paper / Author", "").strip() or None,
                complexity=parse_complexity(row.get("Complexity (Low/Med/High)", "")),
                best_use_case=row.get("Best Use Case", "").strip() or None,
                description=None,
                compatibility_tabular=True,  # Default; update after research
                compatibility_image=False,
                compatibility_text=False,
                compatibility_graph=False,
                compatibility_timeseries=False,
            )
            session.add(algorithm)
            session.flush()  # Get the id

            status = ImplementationStatus(
                algorithm_id=algorithm.id,
                status="planned",
                implemented_from_scratch=False,
                implemented_library=False,
                lab_created=False,
                documentation_complete=False,
                notes_added=False,
                last_updated=datetime.now(timezone.utc).isoformat(),
            )
            session.add(status)
            inserted += 1

        session.commit()

    print(f"Done. Inserted: {inserted}, Skipped (already exist): {skipped}")


if __name__ == "__main__":
    seed()
