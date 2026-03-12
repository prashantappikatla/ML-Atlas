#!/usr/bin/env python3
"""
ML Atlas — Apply Wikipedia links to MDX files.

Reads documentation/todo-links-wikipedia.md and patches the matching MDX
algorithm files to convert plain-text mentions into [Term](wikipedia_url) links.

Rules:
  - Only replaces the FIRST occurrence per (file, term) pair to avoid over-linking.
  - Skips occurrences already inside a markdown link [...](...).
  - Skips occurrences inside fenced code blocks (``` ... ```).
  - Skips occurrences inside inline code (`...`).
  - Skips the frontmatter block (--- ... ---).
  - Uses exact (case-sensitive) matching for proper names, case-insensitive for concepts.

Usage:
    python scripts/apply_wiki_links.py              # dry-run (default, no changes)
    python scripts/apply_wiki_links.py --apply      # apply changes to MDX files
    python scripts/apply_wiki_links.py --algorithm ridge-regression --apply
    python scripts/apply_wiki_links.py --apply --limit 50   # apply first 50 changes only
"""

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
CONTENT_DIR = ROOT / "content" / "algorithms"
WIKI_FILE = ROOT / "documentation" / "todo-links-wikipedia.md"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def find_mdx_file(slug: str) -> Path | None:
    """Find the MDX file for a given algorithm slug."""
    for f in CONTENT_DIR.rglob("*.mdx"):
        if f.stem == slug:
            return f
    # Try common slug aliases
    aliases: dict[str, str] = {
        "elastic-net": "elastic-net",
        "k-means": "k-means",
        "kmeans": "k-means",
    }
    canonical = aliases.get(slug, slug)
    if canonical != slug:
        for f in CONTENT_DIR.rglob("*.mdx"):
            if f.stem == canonical:
                return f
    return None


def strip_frontmatter(text: str) -> tuple[str, int]:
    """
    Split off the YAML frontmatter.
    Returns (body_text, body_start_index).
    """
    if not text.startswith("---"):
        return text, 0
    end = text.index("---", 3)
    body_start = end + 3
    return text[body_start:], body_start


def in_code_block(text: str, pos: int) -> bool:
    """Check if position pos is inside a fenced code block (``` or ~~~)."""
    prefix = text[:pos]
    # Count number of fenced code block openings vs closings
    # Simple heuristic: count ``` occurrences
    fence_count = len(re.findall(r"^```", prefix, re.MULTILINE))
    return fence_count % 2 == 1


def in_inline_code(text: str, pos: int) -> bool:
    """Check if position pos is inside inline code (`...`)."""
    prefix = text[:pos]
    backtick_count = prefix.count("`")
    return backtick_count % 2 == 1


def in_markdown_link(text: str, start: int, end: int) -> bool:
    """
    Check if the match at [start:end] is already inside a markdown link.
    Checks for:
    - [Term](url) — the term is the link text
    - [Something with Term inside](url) — term inside existing link text
    """
    # Look backward for '['
    prefix = text[:start]
    # Check if we're inside [...](...)
    # Find the most recent '[' before start
    last_open = prefix.rfind("[")
    if last_open == -1:
        return False
    # Check if there's a ']' before our match start that closes it
    last_close = prefix.rfind("]")
    if last_close > last_open:
        return False  # The most recent '[' was already closed before our match
    # There's an open '[' — check if what follows our match is '](url)'
    suffix = text[end:]
    if suffix.startswith("](") or "](" in text[end : end + 100]:
        return True
    # Also check if the word is already wrapped as link text
    if re.match(r"^\]\(", suffix):
        return True
    return False


def is_in_header_or_special(text: str, pos: int) -> bool:
    """Check if position is in an MDX heading (## ...) or special MDX syntax."""
    # Find the line containing pos
    line_start = text.rfind("\n", 0, pos) + 1
    line_end = text.find("\n", pos)
    if line_end == -1:
        line_end = len(text)
    line = text[line_start:line_end]
    # Skip lines that are headings (we don't want to link inside headings)
    if re.match(r"^#{1,6}\s", line):
        return True
    # Skip YAML-like lines (frontmatter fields)
    if re.match(r"^\s*\w[\w-]*:\s", line):
        return True
    return False


def apply_link(body: str, term: str, url: str) -> tuple[str, bool]:
    """
    Replace the FIRST plain-text occurrence of `term` in `body` with
    [term](url), skipping code blocks, inline code, and existing links.

    Returns (updated_body, did_replace).
    """
    # Use word boundary matching; proper names are case-sensitive,
    # concepts are slightly flexible but we default to exact match
    # to avoid false positives.
    # Escape special regex chars in the term
    escaped = re.escape(term)
    # Build pattern with word boundaries
    pattern = re.compile(r"\b" + escaped + r"\b")

    for m in pattern.finditer(body):
        start, end = m.start(), m.end()

        # Skip if in code block
        if in_code_block(body, start):
            continue

        # Skip if in inline code
        if in_inline_code(body, start):
            continue

        # Skip if already inside a markdown link
        if in_markdown_link(body, start, end):
            continue

        # Skip if in a heading or frontmatter field
        if is_in_header_or_special(body, start):
            continue

        # Do the replacement (first valid occurrence only)
        replacement = f"[{term}]({url})"
        new_body = body[:start] + replacement + body[end:]
        return new_body, True

    return body, False


# ---------------------------------------------------------------------------
# Parse the wikipedia list file
# ---------------------------------------------------------------------------


def parse_wiki_file(path: Path) -> list[tuple[str, str, str]]:
    """
    Parse todo-links-wikipedia.md.
    Returns list of (algo_slug, term, url).
    """
    items: list[tuple[str, str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        # Format: - `algo-slug` | `Term` | https://...
        m = re.match(r"^- `([^`]+)` \| `([^`]+)` \| (https?://\S+)", line)
        if m:
            items.append((m.group(1), m.group(2), m.group(3)))
    return items


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply Wikipedia links to MDX algorithm files"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to disk (default is dry-run)",
    )
    parser.add_argument(
        "--algorithm",
        metavar="SLUG",
        help="Only process entries for this algorithm slug",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        metavar="N",
        help="Stop after applying N changes (0 = no limit)",
    )
    args = parser.parse_args()

    dry_run = not args.apply
    if dry_run:
        print("DRY-RUN mode — no files will be modified. Pass --apply to write changes.\n")

    if not WIKI_FILE.exists():
        print(f"ERROR: {WIKI_FILE} not found. Run triage_todo_links.py first.")
        sys.exit(1)

    items = parse_wiki_file(WIKI_FILE)
    print(f"Loaded {len(items)} Wikipedia link targets.\n")

    if args.algorithm:
        items = [(s, t, u) for s, t, u in items if s == args.algorithm]
        if not items:
            print(f"No entries found for algorithm {args.algorithm!r}")
            sys.exit(0)

    # Group by algorithm slug to avoid re-reading files repeatedly
    from collections import defaultdict
    by_algo: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for slug, term, url in items:
        by_algo[slug].append((term, url))

    total_applied = 0
    total_skipped = 0
    files_changed = 0
    limit = args.limit

    for slug, term_url_pairs in sorted(by_algo.items()):
        mdx_path = find_mdx_file(slug)
        if mdx_path is None:
            print(f"  SKIP  [{slug}] — MDX file not found")
            total_skipped += len(term_url_pairs)
            continue

        text = mdx_path.read_text(encoding="utf-8")
        body, body_start = strip_frontmatter(text)
        original_body = body
        file_applied = 0

        for term, url in term_url_pairs:
            if limit > 0 and total_applied >= limit:
                break

            new_body, replaced = apply_link(body, term, url)
            if replaced:
                body = new_body
                total_applied += 1
                file_applied += 1
                print(f"  LINK  [{slug}] {term!r} → {url}")
            else:
                total_skipped += 1
                # Only show skipped in verbose mode or if really unexpected
                # (Not printing to keep output readable)

        if file_applied > 0:
            files_changed += 1
            if not dry_run:
                # Reconstruct full file: frontmatter unchanged + updated body
                full_text = text[:body_start] + body
                mdx_path.write_text(full_text, encoding="utf-8")

        if limit > 0 and total_applied >= limit:
            print(f"\nLimit of {limit} reached, stopping.")
            break

    print()
    print("=" * 60)
    print(f"Files with changes : {files_changed}")
    print(f"Links applied      : {total_applied}")
    print(f"Terms not found    : {total_skipped}")
    if dry_run:
        print("\nRe-run with --apply to write these changes.")
    else:
        print("\nChanges applied to disk.")


if __name__ == "__main__":
    main()
