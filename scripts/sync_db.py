#!/usr/bin/env python3
"""
ML Atlas — MDX to Database Sync
================================
Reads all MDX files in content/algorithms/ and syncs their content to the
Supabase PostgreSQL database.

Fields updated:
  algorithm.description          ← ## Overview section text
  algorithm.compatibility_*      ← MDX frontmatter compatibility block
  implementation_status.status   ← promoted to >= "documented"
  implementation_status.documentation_complete  ← True when MDX has content
  implementation_status.last_updated            ← current UTC timestamp
  algorithm_parameters rows      ← parsed from ## Parameters table (idempotent)

Usage (run from ML-Atlas/ project root):
  python scripts/sync_db.py               # full sync
  python scripts/sync_db.py --dry-run     # preview without writing
  python scripts/sync_db.py --slug random-forest-classifier
  python scripts/sync_db.py --category supervised

Requirements:
  pip install -r scripts/requirements.txt
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ── Dependency check ──────────────────────────────────────────────────────────

def _check_deps() -> None:
    missing = []
    try:
        import psycopg2  # noqa: F401
    except ImportError:
        missing.append("psycopg2-binary")
    try:
        import yaml  # noqa: F401
    except ImportError:
        missing.append("PyYAML")
    try:
        from dotenv import load_dotenv  # noqa: F401
    except ImportError:
        missing.append("python-dotenv")
    if missing:
        print("Missing dependencies. Run:")
        print("  pip install -r scripts/requirements.txt")
        print(f"  Missing: {', '.join(missing)}")
        sys.exit(1)


_check_deps()

import psycopg2
import psycopg2.extras
import yaml
from dotenv import load_dotenv

# ── Config ────────────────────────────────────────────────────────────────────

REPO_ROOT    = Path(__file__).parent.parent
CONTENT_ROOT = REPO_ROOT / "content" / "algorithms"
BACKEND_ENV  = REPO_ROOT / "backend" / "fastapi-server" / ".env"
ROOT_ENV     = REPO_ROOT / ".env"

STATUS_ORDER: list[str] = [
    "planned", "in-progress", "documented", "implemented", "lab-ready"
]

# Known slug mismatches: MDX frontmatter slug → DB slug
# These arise where the DB was seeded from the original CSV before encoding fixes,
# producing slugs that differ from what generate_content.py wrote to MDX frontmatter.
SLUG_VARIANTS: dict[str, str] = {
    # Hand-crafted MDX uses "kmeans"; DB was seeded from CSV "K-Means" → "k-means"
    "kmeans":  "k-means",
    "k-means": "kmeans",
    # DB slugified from corrupted CSV before encoding fix
    "theil-sen-regressor":                     "theilsen-regressor",
    "dall-e-style-diffusion-decoder-models":   "dalle-style-diffusiondecoder-models",
}

# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class ParsedMdx:
    path: Path
    slug: str
    frontmatter_status: str | None
    overview: str | None
    has_content: bool
    parameters: list[dict]
    compat_tabular:    bool | None
    compat_image:      bool | None
    compat_text:       bool | None
    compat_timeseries: bool | None
    compat_graph:      bool | None


@dataclass
class SyncStats:
    total_mdx:        int = 0
    parsed_ok:        int = 0
    algo_updated:     int = 0
    status_updated:   int = 0
    params_inserted:  int = 0
    not_found:        list[str] = field(default_factory=list)
    parse_errors:     list[str] = field(default_factory=list)


# ── MDX parsing ───────────────────────────────────────────────────────────────

def parse_mdx_file(path: Path) -> ParsedMdx | None:
    """
    Parse a single MDX file. Returns None on unrecoverable parse failure.
    Logs warnings for soft failures.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        print(f"  ERROR reading {path.name}: {e}")
        return None

    if not text.strip().startswith("---"):
        print(f"  WARN no frontmatter: {path.relative_to(REPO_ROOT)}")
        return None

    parts = text.split("---", 2)
    if len(parts) < 3:
        print(f"  WARN malformed frontmatter: {path.relative_to(REPO_ROOT)}")
        return None

    try:
        fm: dict = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as e:
        print(f"  WARN YAML error in {path.name}: {e}")
        return None

    slug: str = str(fm.get("slug") or path.stem).strip()
    body: str = parts[2]

    # Compatibility flags
    compat = fm.get("compatibility") or {}

    def _bool_or_none(key: str) -> bool | None:
        return bool(compat[key]) if key in compat else None

    compat_tabular    = _bool_or_none("tabular")
    compat_image      = _bool_or_none("image")
    compat_text       = _bool_or_none("text")
    compat_timeseries = _bool_or_none("timeseries")
    compat_graph      = _bool_or_none("graph")

    # Status from frontmatter
    raw_status = str(fm.get("status", "")).strip().lower() or None
    if raw_status and raw_status not in STATUS_ORDER:
        raw_status = None

    overview    = _extract_overview(body)
    has_content = _mdx_has_content(body)
    parameters  = _parse_parameters_table(body)

    return ParsedMdx(
        path=path,
        slug=slug,
        frontmatter_status=raw_status,
        overview=overview,
        has_content=has_content,
        parameters=parameters,
        compat_tabular=compat_tabular,
        compat_image=compat_image,
        compat_text=compat_text,
        compat_timeseries=compat_timeseries,
        compat_graph=compat_graph,
    )


def _extract_overview(body: str) -> str | None:
    """
    Extract the ## Overview section body text.
    Strips MDX link syntax [text](/path) to plain text.
    Returns None if the section is absent or empty.
    """
    match = re.search(
        r"##\s+Overview\s*\n(.*?)(?=\n##\s|\Z)",
        body,
        re.DOTALL,
    )
    if not match:
        return None
    text = match.group(1).strip()
    if not text:
        return None
    # Strip MDX link syntax: [Display Text](/algorithms/...) → Display Text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text


def _mdx_has_content(body: str) -> bool:
    """
    Return True if the MDX body contains meaningful content beyond headings.
    Mirrors the heuristic in database/seeds/update_status_from_mdx.py.
    """
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
    for line in lines:
        if line.startswith("|") and "|" in line[1:]:
            return True
        if line.startswith("- ") and len(line) > 3:
            return True
        if line.startswith("```"):
            return True
        if re.match(r"^\d+\.\s+.+", line) and "..." not in line and len(line) > 6:
            return True
        if len(line) > 40 and not line.startswith("#") and not line.startswith("<"):
            return True
    return False


def _parse_parameters_table(body: str) -> list[dict]:
    """
    Parse the ## Parameters markdown table. Handles 4-column and 5-column layouts:
      4-col: Parameter | Type | Default | Description
      5-col: Parameter | Type | Default | Range/Options | Description

    Returns list of dicts: {parameter_name, parameter_type, default_value, description}
    """
    section_match = re.search(
        r"##\s+Parameters\s*\n(.*?)(?=\n##\s|\Z)",
        body,
        re.DOTALL,
    )
    if not section_match:
        return []

    rows: list[dict] = []
    header_seen = False
    num_cols: int | None = None

    for line in section_match.group(1).splitlines():
        line = line.strip()
        if not (line.startswith("|") and line.endswith("|")):
            continue

        cells = [c.strip() for c in line.strip("|").split("|")]

        # Separator row: all cells are dashes/colons only
        if all(re.fullmatch(r"[-:\s]+", c) for c in cells if c):
            if not header_seen:
                # Separator comes right after header
                header_seen = True
            num_cols = len(cells)
            continue

        # First non-separator row is the header
        if not header_seen:
            header_seen = True
            num_cols = len(cells)
            continue

        if not num_cols or len(cells) < 3:
            continue

        param_name = cells[0].strip("`").strip()
        if not param_name or re.fullmatch(r"[-:\s]+", param_name):
            continue

        param_type    = cells[1].strip("`").strip() if len(cells) > 1 else ""
        default_value = cells[2].strip("`").strip() if len(cells) > 2 else ""

        # 5-col: skip index 3 (Range/Options), use index 4 for description
        if num_cols >= 5 and len(cells) >= 5:
            description = cells[4].strip()
        elif len(cells) >= 4:
            description = cells[3].strip()
        else:
            description = ""

        rows.append({
            "parameter_name": param_name,
            "parameter_type": _normalize_param_type(param_type),
            "default_value":  default_value or None,
            "description":    description or None,
        })

    return rows


def _normalize_param_type(raw: str) -> str:
    """Map MDX type strings to DB enum values: float | int | str | bool."""
    s = raw.lower().strip("`").strip()
    if "int" in s:
        return "int"
    if "float" in s or "double" in s:
        return "float"
    if "bool" in s:
        return "bool"
    return "str"


# ── Status logic ──────────────────────────────────────────────────────────────

def compute_new_status(frontmatter_status: str | None, has_content: bool) -> str | None:
    """
    Compute the target status for implementation_status.status.

    Rules:
    - If MDX has no content → no change (return None)
    - Otherwise → max(frontmatter_status, "documented") by STATUS_ORDER
    - This promotes "planned" / "in-progress" → "documented"
    - "implemented" and "lab-ready" are preserved as-is
    """
    if not has_content:
        return None
    fm = frontmatter_status if frontmatter_status in STATUS_ORDER else "planned"
    documented_idx = STATUS_ORDER.index("documented")
    fm_idx         = STATUS_ORDER.index(fm)
    return STATUS_ORDER[max(fm_idx, documented_idx)]


# ── DB sync ───────────────────────────────────────────────────────────────────

def _resolve_slug(slug: str, db_algorithms: dict[str, dict]) -> dict | None:
    """
    Look up a DB row by slug. If not found, try the known variant.
    Returns DB row dict or None.
    """
    row = db_algorithms.get(slug)
    if row:
        return row
    variant = SLUG_VARIANTS.get(slug)
    if variant:
        return db_algorithms.get(variant)
    return None


def _load_db_state(cur) -> tuple[dict, dict, dict]:
    """
    Load full DB state into memory with 3 queries.

    Returns:
      db_algorithms: slug → {id, description, compatibility_*}
      db_statuses:   algorithm_id → {id, status, documentation_complete}
      db_params:     algorithm_id → set of existing parameter_names
    """
    cur.execute(
        "SELECT id, slug, description, "
        "compatibility_tabular, compatibility_image, compatibility_text, "
        "compatibility_graph, compatibility_timeseries "
        "FROM algorithm"
    )
    db_algorithms = {row["slug"]: dict(row) for row in cur.fetchall()}

    cur.execute(
        "SELECT id, algorithm_id, status, documentation_complete "
        "FROM implementation_status"
    )
    db_statuses = {row["algorithm_id"]: dict(row) for row in cur.fetchall()}

    cur.execute("SELECT algorithm_id, parameter_name FROM algorithm_parameters")
    db_params: dict[int, set[str]] = {}
    for row in cur.fetchall():
        db_params.setdefault(row["algorithm_id"], set()).add(row["parameter_name"])

    return db_algorithms, db_statuses, db_params


def sync_to_db(
    conn,
    parsed_files: list[ParsedMdx],
    dry_run: bool,
    verbose: bool = True,
) -> SyncStats:
    """
    Sync all parsed MDX data to the database in a single transaction.
    Rolls back on --dry-run or on any exception.
    """
    stats = SyncStats(total_mdx=len(parsed_files))
    now_iso = datetime.now(timezone.utc).isoformat()

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        db_algorithms, db_statuses, db_params = _load_db_state(cur)

        for mdx in parsed_files:
            db_row = _resolve_slug(mdx.slug, db_algorithms)
            if db_row is None:
                if verbose:
                    print(f"  WARN slug not in DB: '{mdx.slug}' — skipping")
                stats.not_found.append(mdx.slug)
                continue

            algo_id: int = db_row["id"]

            # ── algorithm table ──────────────────────────────────────────────
            algo_updates: dict = {}

            if mdx.overview is not None and db_row.get("description") != mdx.overview:
                algo_updates["description"] = mdx.overview

            compat_map = {
                "compatibility_tabular":    mdx.compat_tabular,
                "compatibility_image":      mdx.compat_image,
                "compatibility_text":       mdx.compat_text,
                "compatibility_timeseries": mdx.compat_timeseries,
                "compatibility_graph":      mdx.compat_graph,
            }
            for col, val in compat_map.items():
                if val is not None and db_row.get(col) != val:
                    algo_updates[col] = val

            if algo_updates:
                cols = list(algo_updates.keys())
                set_clause = ", ".join(f"{c} = %({c})s" for c in cols)
                payload = {**algo_updates, "_id": algo_id}
                if verbose:
                    print(f"  UPDATE algorithm  {mdx.slug!r}  {cols}")
                if not dry_run:
                    cur.execute(
                        f"UPDATE algorithm SET {set_clause} WHERE id = %(_id)s",
                        payload,
                    )
                stats.algo_updated += 1

            # ── implementation_status table ──────────────────────────────────
            status_row = db_statuses.get(algo_id)
            if status_row:
                new_status = compute_new_status(mdx.frontmatter_status, mdx.has_content)
                current_idx = (STATUS_ORDER.index(status_row["status"])
                               if status_row["status"] in STATUS_ORDER else 0)

                status_updates: dict = {}
                if new_status is not None:
                    new_idx = STATUS_ORDER.index(new_status)
                    if new_idx > current_idx:
                        status_updates["status"] = new_status

                if not status_row["documentation_complete"] and mdx.has_content:
                    status_updates["documentation_complete"] = True

                if status_updates:
                    status_updates["last_updated"] = now_iso
                    cols = list(status_updates.keys())
                    set_clause = ", ".join(f"{c} = %({c})s" for c in cols)
                    payload = {**status_updates, "_id": status_row["id"]}

                    new_s = status_updates.get("status", status_row["status"])
                    if verbose:
                        print(
                            f"  UPDATE status     {mdx.slug!r}  "
                            f"{status_row['status']} → {new_s}  "
                            f"doc_complete={status_updates.get('documentation_complete', '(unchanged)')}"
                        )
                    if not dry_run:
                        cur.execute(
                            f"UPDATE implementation_status SET {set_clause} WHERE id = %(_id)s",
                            payload,
                        )
                    stats.status_updated += 1

            # ── algorithm_parameters inserts ─────────────────────────────────
            existing_names = db_params.get(algo_id, set())
            new_params = [p for p in mdx.parameters
                          if p["parameter_name"] not in existing_names]

            for param in new_params:
                if verbose:
                    print(
                        f"  INSERT param      {mdx.slug!r}  "
                        f"{param['parameter_name']!r} ({param['parameter_type']})"
                    )
                if not dry_run:
                    cur.execute(
                        """INSERT INTO algorithm_parameters
                               (algorithm_id, parameter_name, description,
                                default_value, parameter_type)
                           VALUES (%(algorithm_id)s, %(parameter_name)s,
                                   %(description)s, %(default_value)s,
                                   %(parameter_type)s)""",
                        {**param, "algorithm_id": algo_id},
                    )
                stats.params_inserted += 1

    if dry_run:
        conn.rollback()
    else:
        conn.commit()

    return stats


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync MDX content to the ML Atlas Supabase database.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without writing to the database.",
    )
    parser.add_argument(
        "--slug", metavar="SLUG",
        help="Process only the MDX file with this slug (e.g. random-forest-classifier).",
    )
    parser.add_argument(
        "--category", metavar="CATEGORY",
        help="Process only algorithms in this category (e.g. supervised).",
    )
    parser.add_argument(
        "--quiet", action="store_true",
        help="Suppress per-algorithm output; only print the summary.",
    )
    args = parser.parse_args()

    # Load environment variables
    if BACKEND_ENV.exists():
        load_dotenv(BACKEND_ENV, override=False)
    if ROOT_ENV.exists():
        load_dotenv(ROOT_ENV, override=False)

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in .env or environment.")
        print("Expected: postgresql://postgres:password@db.<project>.supabase.co:5432/postgres")
        sys.exit(1)

    if not CONTENT_ROOT.exists():
        print(f"ERROR: Content directory not found: {CONTENT_ROOT}")
        print("Run this script from the ML-Atlas/ project root.")
        sys.exit(1)

    # ── Discover MDX files ────────────────────────────────────────────────────
    all_paths = sorted(CONTENT_ROOT.rglob("*.mdx"))

    if args.slug:
        all_paths = [p for p in all_paths if p.stem == args.slug or
                     # also match if frontmatter slug would differ from filename
                     args.slug in p.name]
        if not all_paths:
            print(f"ERROR: No MDX file found matching slug '{args.slug}'.")
            sys.exit(1)

    if args.category:
        all_paths = [
            p for p in all_paths
            if p.relative_to(CONTENT_ROOT).parts[0] == args.category
        ]
        if not all_paths:
            print(f"ERROR: No MDX files found for category '{args.category}'.")
            sys.exit(1)

    print(f"ML Atlas DB Sync")
    print("=" * 50)
    print(f"MDX files found : {len(all_paths)}")
    if args.dry_run:
        print("Mode            : DRY RUN (no writes)\n")
    else:
        print("Mode            : LIVE\n")

    # ── Parse MDX files ───────────────────────────────────────────────────────
    parsed: list[ParsedMdx] = []
    parse_errors: list[str] = []

    for path in all_paths:
        result = parse_mdx_file(path)
        if result:
            parsed.append(result)
        else:
            parse_errors.append(str(path.relative_to(REPO_ROOT)))

    print(f"Parsed OK       : {len(parsed)} / {len(all_paths)}")
    if parse_errors:
        print(f"Parse failures  : {len(parse_errors)}")
        for e in parse_errors:
            print(f"  {e}")
    print()

    # ── Connect to DB ─────────────────────────────────────────────────────────
    try:
        conn = psycopg2.connect(database_url)
    except psycopg2.OperationalError as e:
        print(f"ERROR: Cannot connect to database: {e}")
        sys.exit(1)

    # ── Run sync ──────────────────────────────────────────────────────────────
    try:
        stats = sync_to_db(
            conn,
            parsed,
            dry_run=args.dry_run,
            verbose=not args.quiet,
        )
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"\nERROR: Sync failed — all changes rolled back.\n{e}")
        raise
    finally:
        conn.close()

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=" * 50)
    print("SYNC SUMMARY")
    print("=" * 50)
    print(f"  MDX files processed     : {stats.total_mdx}")
    print(f"  algorithm rows updated  : {stats.algo_updated}")
    print(f"  status rows updated     : {stats.status_updated}")
    print(f"  parameters inserted     : {stats.params_inserted}")
    print(f"  slugs not found in DB   : {len(stats.not_found)}")
    if stats.not_found:
        print(f"  Not-found slugs        : {stats.not_found}")
    if parse_errors:
        print(f"  MDX parse errors       : {len(parse_errors)}")
    if args.dry_run:
        print("\n  ** DRY RUN — no changes were committed **")
    else:
        print("\n  ✅ All changes committed to database.")


if __name__ == "__main__":
    main()
