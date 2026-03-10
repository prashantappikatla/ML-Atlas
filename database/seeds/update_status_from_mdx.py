"""
Update implementation_status in the database for algorithms that have MDX content
(in progress). Scans content/algorithms for MDX files, detects which have meaningful
content, and sets status to "in-progress" when the current DB status is "planned".

Run from repo root:
    cd backend/fastapi-server
    uv run python ../../database/seeds/update_status_from_mdx.py

Or from database/seeds/:
    uv run python update_status_from_mdx.py
"""

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

CONTENT_ALGORITHMS = Path(__file__).parent.parent.parent / "content" / "algorithms"

REPO_ROOT = Path(__file__).parent.parent.parent
BACKEND_ENV = BACKEND_PATH / ".env"
ROOT_ENV = REPO_ROOT / ".env"

if BACKEND_ENV.exists():
    load_dotenv(BACKEND_ENV, override=False)
if ROOT_ENV.exists():
    load_dotenv(ROOT_ENV, override=False)


STATUS_ORDER = ("planned", "in-progress", "documented", "implemented", "lab-ready")


def get_frontmatter_status(path: Path) -> tuple[str | None, str | None]:
    """Parse frontmatter and return (slug, status). Status is normalized or None."""
    text = path.read_text(encoding="utf-8")
    if not text.strip().startswith("---"):
        return None, None
    parts = text.split("---", 2)
    if len(parts) < 2:
        return None, None
    front = parts[1]
    slug_m = re.search(r"slug:\s*[\"']?([-\w]+)[\"']?", front)
    status_m = re.search(r"status:\s*[\"']?(\w[-\w]*)[\"']?", front)
    slug = slug_m.group(1) if slug_m else None
    status = status_m.group(1).strip().lower() if status_m else None
    if status and status not in STATUS_ORDER:
        status = None
    return slug, status


def mdx_has_content(path: Path) -> bool:
    """
    Return True if the MDX file has meaningful body content (not just frontmatter
    and empty sections). Uses heuristics: body after frontmatter has tables,
    list items, code blocks, or substantial text.
    """
    text = path.read_text(encoding="utf-8")
    if "---" not in text:
        return False
    parts = text.split("---", 2)
    if len(parts) < 3:
        return False
    body = parts[2]
    # Skip empty lines and section headers only
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    if not lines:
        return False
    # Meaningful content: table row, list item, code fence, or a line with real content
    for line in lines:
        if line.startswith("|") and "|" in line[1:]:  # table
            return True
        if line.startswith("- ") and len(line) > 3:  # list
            return True
        if line.startswith("```"):  # code block
            return True
        if re.match(r"^\d+\.\s+.+", line) and "..." not in line and len(line) > 6:  # numbered step
            return True
        if len(line) > 40 and not line.startswith("#") and not line.startswith("<"):  # paragraph
            return True
    return False


def run(database_url: str | None = None) -> None:
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: Set DATABASE_URL environment variable or pass database_url argument.")
        sys.exit(1)

    if not CONTENT_ALGORITHMS.exists():
        print(f"ERROR: Content path not found: {CONTENT_ALGORITHMS}")
        sys.exit(1)

    mdx_files = list(CONTENT_ALGORITHMS.rglob("*.mdx"))
    # List of (slug, target_status). target_status from frontmatter or "in-progress".
    to_update: list[tuple[str, str]] = []
    for path in mdx_files:
        slug, mdx_status = get_frontmatter_status(path)
        if not slug:
            print(f"  Skip (no slug): {path.relative_to(CONTENT_ALGORITHMS)}")
            continue
        if not mdx_has_content(path):
            continue
        # Use frontmatter status if it's ahead of in-progress; otherwise set in-progress
        if mdx_status and STATUS_ORDER.index(mdx_status) > STATUS_ORDER.index("in-progress"):
            target = mdx_status
        else:
            target = "in-progress"
        to_update.append((slug, target))
        print(f"  Has content: {slug} -> {target}")

    if not to_update:
        print("No MDX files with content found. Exiting.")
        return

    print(f"\nUpdating DB for {len(to_update)} algorithm(s) (only when current status is 'planned')...")
    engine = create_engine(url)
    updated = 0
    skipped_not_planned = 0
    not_found = []

    # Slug variants (e.g. MDX "kmeans" vs CSV-seeded "k-means")
    def slug_variants(s: str) -> list[str]:
        variants = [s]
        if s == "kmeans":
            variants.append("k-means")
        elif s == "k-means":
            variants.append("kmeans")
        return variants

    with Session(engine) as session:
        for slug, target_status in to_update:
            algo = None
            for variant in slug_variants(slug):
                algo = session.exec(select(Algorithm).where(Algorithm.slug == variant)).first()
                if algo:
                    break
            if not algo:
                not_found.append(slug)
                continue
            status_row = session.exec(
                select(ImplementationStatus).where(ImplementationStatus.algorithm_id == algo.id)
            ).first()
            if not status_row:
                not_found.append(slug)
                continue
            current_idx = STATUS_ORDER.index(status_row.status) if status_row.status in STATUS_ORDER else 0
            target_idx = STATUS_ORDER.index(target_status)
            if current_idx >= target_idx:
                skipped_not_planned += 1
                print(f"  Skip {slug}: already '{status_row.status}' (target {target_status})")
                continue
            status_row.status = target_status
            status_row.last_updated = datetime.now(timezone.utc).isoformat()
            session.add(status_row)
            updated += 1
            print(f"  Updated {slug} -> {target_status}")
        session.commit()

    if not_found:
        print(f"\nWARNING: Algorithm(s) not found in DB (by slug): {not_found}")
    print(f"\nDone. Updated: {updated}, Skipped (not 'planned'): {skipped_not_planned}")


if __name__ == "__main__":
    run()
