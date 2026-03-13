#!/usr/bin/env python3
"""
ML Atlas — Build the link registry.

Reads all 278 MDX algorithm files and existing documentation to produce
`documentation/link-registry.json` — the single source of truth for all
links used in MDX content.

Registry sections
-----------------
- algorithms : name → {slug, url, category, name}
               URL is always 2-level: /algorithms/{category}/{slug}
- wikipedia  : term → url
               Seeded from documentation/todo-links-wikipedia.md
- external   : display_text → url
               Discovered by scanning all MDX body content for https:// links
               (excluding /algorithms/ and wikipedia.org)
- app_pages  : label → path
               Static map of non-algorithm Next.js routes

Usage
-----
    python scripts/build_link_registry.py           # full rebuild (default)
    python scripts/build_link_registry.py --merge   # add new entries, keep manual edits
    python scripts/build_link_registry.py --dry-run # print what would be written
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install PyYAML")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
CONTENT_DIR = ROOT / "content" / "algorithms"
WIKI_FILE = ROOT / "documentation" / "todo-links-wikipedia.md"
REGISTRY_FILE = ROOT / "documentation" / "link-registry.json"

# ---------------------------------------------------------------------------
# Static data
# ---------------------------------------------------------------------------

APP_PAGES: dict[str, str] = {
    "Browse Algorithms": "/algorithms",
    "All Algorithms": "/algorithms",
    "Progress Dashboard": "/progress",
    "Progress": "/progress",
    "Search": "/search",
    "Labs": "/labs",
    "Home": "/",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter dict from MDX text. Returns {} on failure."""
    if not text.startswith("---"):
        return {}
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}
    fm_raw = text[3:end].strip()
    try:
        return yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError:
        return {}


def get_body(text: str) -> str:
    """Return the body (after frontmatter) of an MDX file."""
    if not text.startswith("---"):
        return text
    try:
        end = text.index("---", 3)
        return text[end + 3 :]
    except ValueError:
        return text


def extract_external_links(body: str) -> list[tuple[str, str]]:
    """
    Scan body for existing markdown links [text](https://...) that are not
    /algorithms/ internal links and not wikipedia.org links.

    Returns list of (display_text, url) tuples.
    """
    # Match [display text](https://...) — capture text and URL
    pattern = re.compile(r"\[([^\]]+)\]\((https://[^)]+)\)")
    results: list[tuple[str, str]] = []
    for m in pattern.finditer(body):
        text = m.group(1).strip()
        url = m.group(2).strip()
        # Skip internal /algorithms/ links
        if "/algorithms/" in url and not url.startswith("http"):
            continue
        # Skip wikipedia
        if "wikipedia.org" in url:
            continue
        # Skip bare /algorithms/ paths embedded as https?
        if re.match(r"https?://[^/]+/algorithms/", url):
            continue
        results.append((text, url))
    return results


# ---------------------------------------------------------------------------
# Build sections
# ---------------------------------------------------------------------------


def build_algorithms_section(content_dir: Path) -> dict[str, dict]:
    """
    Scan all MDX files, extract title: from frontmatter, compute the correct
    2-level URL, and build the algorithms registry section.

    Key: algorithm title (e.g. "Logistic Regression")
    Value: {slug, url, category, name}
    """
    algorithms: dict[str, dict] = {}
    for mdx_path in sorted(content_dir.rglob("*.mdx")):
        text = mdx_path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        if not fm:
            print(f"  WARN  no frontmatter: {mdx_path.relative_to(ROOT)}")
            continue

        # Derive category and slug from file path:
        #   content/algorithms/{category}/{subcategory}/{slug}.mdx
        #   content/algorithms/{category}/{slug}.mdx  (if no subcategory)
        parts = mdx_path.relative_to(content_dir).parts  # e.g. ("supervised", "classification", "logistic-regression.mdx")
        category = parts[0]  # e.g. "supervised"
        slug = mdx_path.stem  # e.g. "logistic-regression"
        url = f"/algorithms/{category}/{slug}"

        # Use title from frontmatter as canonical name; fall back to slug->title
        name: str = fm.get("title") or slug.replace("-", " ").title()

        algorithms[name] = {
            "slug": slug,
            "url": url,
            "category": category,
            "name": name,
        }

    return algorithms


def build_wikipedia_section(wiki_file: Path) -> dict[str, str]:
    """
    Parse documentation/todo-links-wikipedia.md.
    Format per line:  - `algo-slug` | `Term` | https://...
    Returns {term: url} map (deduplicated — last url wins for a given term).
    """
    wikipedia: dict[str, str] = {}
    if not wiki_file.exists():
        print(f"  WARN  Wikipedia file not found: {wiki_file.relative_to(ROOT)}")
        return wikipedia

    for line in wiki_file.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^- `([^`]+)` \| `([^`]+)` \| (https?://\S+)", line)
        if m:
            term = m.group(2)
            url = m.group(3)
            wikipedia[term] = url

    return wikipedia


def build_external_section(content_dir: Path, wikipedia: dict[str, str]) -> dict[str, str]:
    """
    Scan MDX body content for existing [text](https://...) links that are
    not internal /algorithms/ links and not already in the wikipedia section.
    Returns {display_text: url} map.
    """
    external: dict[str, str] = {}
    wiki_urls = set(wikipedia.values())

    for mdx_path in sorted(content_dir.rglob("*.mdx")):
        text = mdx_path.read_text(encoding="utf-8")
        body = get_body(text)
        for display_text, url in extract_external_links(body):
            # Skip if URL is already covered by wikipedia
            if url in wiki_urls:
                continue
            if "wikipedia.org" in url:
                continue
            # Use display text as key; don't overwrite existing entries
            if display_text not in external:
                external[display_text] = url

    return external


# ---------------------------------------------------------------------------
# Registry I/O
# ---------------------------------------------------------------------------


def load_existing_registry(registry_file: Path) -> dict:
    """Load existing registry JSON or return empty skeleton."""
    if registry_file.exists():
        try:
            return json.loads(registry_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  WARN  Could not parse existing registry ({e}); starting fresh.")
    return {}


def build_registry(merge: bool, content_dir: Path, wiki_file: Path) -> dict:
    """Build (or merge into) the link registry."""
    existing = load_existing_registry(REGISTRY_FILE) if merge else {}

    print("Building algorithms section...")
    algorithms = build_algorithms_section(content_dir)
    print(f"  → {len(algorithms)} algorithms found")

    print("Building wikipedia section...")
    wikipedia = build_wikipedia_section(wiki_file)
    print(f"  → {len(wikipedia)} Wikipedia terms")

    print("Building external section...")
    external = build_external_section(content_dir, wikipedia)
    print(f"  → {len(external)} external link entries")

    # Merge strategy: new data wins for algorithms/wikipedia; preserve manual
    # external entries that aren't in the fresh scan
    if merge:
        merged_algorithms = {**existing.get("algorithms", {}), **algorithms}
        merged_wikipedia = {**existing.get("wikipedia", {}), **wikipedia}
        merged_external = {**existing.get("external", {}), **external}
        merged_app_pages = {**APP_PAGES, **existing.get("app_pages", {})}
    else:
        merged_algorithms = algorithms
        merged_wikipedia = wikipedia
        merged_external = external
        merged_app_pages = APP_PAGES

    return {
        "version": "1.0",
        "generated": "2026-03-12",
        "algorithms": dict(sorted(merged_algorithms.items())),
        "wikipedia": dict(sorted(merged_wikipedia.items())),
        "external": dict(sorted(merged_external.items())),
        "app_pages": merged_app_pages,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build documentation/link-registry.json from MDX files and existing docs"
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge new entries into existing registry (preserve manual edits). Default: full rebuild.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be written without saving.",
    )
    args = parser.parse_args()

    if not CONTENT_DIR.exists():
        print(f"ERROR: Content directory not found: {CONTENT_DIR}")
        sys.exit(1)

    mode = "MERGE" if args.merge else "FULL REBUILD"
    print(f"\n{'='*60}")
    print(f"ML Atlas — Link Registry Builder ({mode})")
    print(f"{'='*60}\n")

    registry = build_registry(
        merge=args.merge,
        content_dir=CONTENT_DIR,
        wiki_file=WIKI_FILE,
    )

    print(f"\n{'='*60}")
    print(f"Registry summary:")
    print(f"  algorithms : {len(registry['algorithms'])} entries")
    print(f"  wikipedia  : {len(registry['wikipedia'])} entries")
    print(f"  external   : {len(registry['external'])} entries")
    print(f"  app_pages  : {len(registry['app_pages'])} entries")

    output_json = json.dumps(registry, indent=2, ensure_ascii=False)

    if args.dry_run:
        print(f"\nDRY-RUN — would write {len(output_json):,} bytes to:")
        print(f"  {REGISTRY_FILE.relative_to(ROOT)}")
        print("\nFirst 10 algorithm entries:")
        for name, info in list(registry["algorithms"].items())[:10]:
            print(f"  {name!r:45s} → {info['url']}")
    else:
        REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        REGISTRY_FILE.write_text(output_json + "\n", encoding="utf-8")
        print(f"\nWritten to: {REGISTRY_FILE.relative_to(ROOT)}")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
