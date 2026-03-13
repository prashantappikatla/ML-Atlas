#!/usr/bin/env python3
"""
ML Atlas — Apply links from the registry to MDX algorithm files.

Iterates through each MDX algorithm file and inserts links from
documentation/link-registry.json at the FIRST plain-text occurrence of
each term in the body. No term is ever linked more than once per file.

Link types (applied in priority order — longest match wins within each type):
  1. Algorithm names  (internal /algorithms/{category}/{slug} links)
  2. Wikipedia terms  (https://en.wikipedia.org/...)
  3. External links   (scikit-learn, arxiv, GitHub, etc.)

Skipped positions:
  - Fenced code blocks (``` ... ```)
  - Inline code (`...`)
  - Headings (## ...)
  - Frontmatter (--- ... ---)
  - Already-linked text ([...](...)

Usage
-----
    python scripts/apply_links.py --dry-run               # preview all
    python scripts/apply_links.py --apply                 # apply to all files
    python scripts/apply_links.py --type internal --apply # internal links only
    python scripts/apply_links.py --type wikipedia --apply
    python scripts/apply_links.py --type external --apply
    python scripts/apply_links.py --algorithm SLUG --apply
    python scripts/apply_links.py --category CAT --apply
"""

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
CONTENT_DIR = ROOT / "content" / "algorithms"
REGISTRY_FILE = ROOT / "documentation" / "link-registry.json"

# ---------------------------------------------------------------------------
# Registry loading
# ---------------------------------------------------------------------------


def load_registry(registry_file: Path) -> dict:
    if not registry_file.exists():
        print(f"ERROR: Registry not found at {registry_file.relative_to(ROOT)}")
        print("Run `python scripts/build_link_registry.py` first.")
        sys.exit(1)
    return json.loads(registry_file.read_text(encoding="utf-8"))


def build_term_list(
    registry: dict, link_types: set[str]
) -> list[tuple[str, str, str]]:
    """
    Build a flat list of (term, url, type) sorted longest-first to ensure
    more-specific matches win (e.g. "Random Forest Classifier" before "Random Forest").

    link_types: subset of {"internal", "wikipedia", "external"}
    """
    items: list[tuple[str, str, str]] = []

    if "internal" in link_types:
        for name, info in registry.get("algorithms", {}).items():
            items.append((name, info["url"], "internal"))

    if "wikipedia" in link_types:
        for term, url in registry.get("wikipedia", {}).items():
            items.append((term, url, "wikipedia"))

    if "external" in link_types:
        for term, url in registry.get("external", {}).items():
            items.append((term, url, "external"))

    # Sort longest term first — prevents short terms from consuming long ones
    items.sort(key=lambda x: len(x[0]), reverse=True)
    return items


# ---------------------------------------------------------------------------
# Position helpers
# ---------------------------------------------------------------------------


def get_frontmatter_end(text: str) -> int:
    """Return the index where frontmatter ends."""
    if not text.startswith("---"):
        return 0
    try:
        end = text.index("---", 3)
        return end + 3
    except ValueError:
        return 0


def in_fenced_code(text: str, pos: int) -> bool:
    prefix = text[:pos]
    return len(re.findall(r"^```", prefix, re.MULTILINE)) % 2 == 1


def in_inline_code(text: str, pos: int) -> bool:
    prefix = text[:pos]
    return prefix.count("`") % 2 == 1


def in_markdown_link(text: str, start: int, end: int) -> bool:
    """True if the span [start:end] is already inside a markdown link."""
    prefix = text[:start]
    last_open = prefix.rfind("[")
    if last_open == -1:
        return False
    last_close = prefix.rfind("]")
    if last_close > last_open:
        return False
    suffix = text[end:]
    # Check for ]( immediately after or within a short window
    if suffix.startswith("](") or ("](" in text[end : end + 100]):
        return True
    return False


def in_heading(text: str, pos: int) -> bool:
    """True if pos is on a markdown heading line (## ...)."""
    line_start = text.rfind("\n", 0, pos) + 1
    line_end = text.find("\n", pos)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    return bool(re.match(r"^#{1,6}\s", line))


def in_frontmatter_field(text: str, pos: int) -> bool:
    """True if pos is on a YAML frontmatter key: value line."""
    line_start = text.rfind("\n", 0, pos) + 1
    line_end = text.find("\n", pos)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    return bool(re.match(r"^\s*\w[\w-]*:\s", line))


# ---------------------------------------------------------------------------
# Core link insertion
# ---------------------------------------------------------------------------


def apply_link_to_body(body: str, term: str, url: str) -> tuple[str, bool]:
    """
    Replace the FIRST valid plain-text occurrence of `term` in `body` with
    [term](url). Returns (updated_body, did_replace).
    """
    escaped = re.escape(term)
    pattern = re.compile(r"\b" + escaped + r"\b")

    for m in pattern.finditer(body):
        start, end = m.start(), m.end()

        if in_fenced_code(body, start):
            continue
        if in_inline_code(body, start):
            continue
        if in_markdown_link(body, start, end):
            continue
        if in_heading(body, start):
            continue
        if in_frontmatter_field(body, start):
            continue

        replacement = f"[{m.group()}]({url})"
        return body[:start] + replacement + body[end:], True

    return body, False


def apply_links_to_file(
    mdx_path: Path,
    term_list: list[tuple[str, str, str]],
    dry_run: bool,
) -> tuple[int, int]:
    """
    Apply first-occurrence-only links from term_list to one MDX file.
    Returns (n_applied, n_skipped).
    """
    text = mdx_path.read_text(encoding="utf-8")
    body_start = get_frontmatter_end(text)
    body = text[body_start:]
    original_body = body

    linked_terms: set[str] = set()  # Terms already linked in this file
    linked_urls: set[str] = set()   # URLs already linked (prevents same-URL duplicates via synonyms)
    n_applied = 0
    n_skipped = 0

    for term, url, link_type in term_list:
        # Skip if this exact term is already linked in this file
        if term in linked_terms:
            n_skipped += 1
            continue
        # Skip if the same URL was already linked by a synonym term
        if url in linked_urls:
            n_skipped += 1
            continue

        new_body, replaced = apply_link_to_body(body, term, url)
        if replaced:
            body = new_body
            linked_terms.add(term)
            linked_urls.add(url)
            n_applied += 1
        else:
            n_skipped += 1

    if body != original_body and not dry_run:
        full_text = text[:body_start] + body
        mdx_path.write_text(full_text, encoding="utf-8")

    return n_applied, n_skipped


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply first-occurrence-only links from registry to MDX files"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to disk (default is dry-run)",
    )
    parser.add_argument(
        "--type",
        choices=["internal", "wikipedia", "external", "all"],
        default="all",
        help="Link types to apply (default: all)",
    )
    parser.add_argument(
        "--algorithm",
        metavar="SLUG",
        help="Process only this algorithm slug",
    )
    parser.add_argument(
        "--category",
        metavar="CAT",
        help="Process only algorithms in this category",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="Stop after applying N links total (0 = no limit)",
    )
    args = parser.parse_args()

    dry_run = not args.apply
    if dry_run:
        print("DRY-RUN — no files will be modified. Pass --apply to write changes.\n")

    registry = load_registry(REGISTRY_FILE)

    # Determine which link types to apply
    if args.type == "all":
        link_types = {"internal", "wikipedia", "external"}
    else:
        link_types = {args.type}

    term_list = build_term_list(registry, link_types)
    print(f"Registry terms loaded: {len(term_list)} ({', '.join(sorted(link_types))})\n")

    # Collect MDX files
    mdx_files: list[Path] = sorted(CONTENT_DIR.rglob("*.mdx"))

    if args.algorithm:
        mdx_files = [f for f in mdx_files if f.stem == args.algorithm]
        if not mdx_files:
            print(f"ERROR: No MDX file with slug {args.algorithm!r}")
            sys.exit(1)

    if args.category:
        mdx_files = [f for f in mdx_files if f.relative_to(CONTENT_DIR).parts[0] == args.category]
        if not mdx_files:
            print(f"ERROR: No MDX files in category {args.category!r}")
            sys.exit(1)

    total_applied = 0
    total_skipped = 0
    files_changed = 0
    limit = args.limit

    for mdx_path in mdx_files:
        if limit > 0 and total_applied >= limit:
            print(f"\nLimit of {limit} reached.")
            break

        n_applied, n_skipped = apply_links_to_file(mdx_path, term_list, dry_run)
        total_applied += n_applied
        total_skipped += n_skipped

        if n_applied > 0:
            files_changed += 1
            print(f"  LINK  [{mdx_path.stem}] {n_applied} link(s) applied")

    print()
    print("=" * 60)
    print(f"Files changed       : {files_changed}")
    print(f"Links applied       : {total_applied}")
    print(f"Terms not found     : {total_skipped}")
    if dry_run:
        print("\nRe-run with --apply to write changes.")
    else:
        print("\nChanges applied to disk.")


if __name__ == "__main__":
    main()
