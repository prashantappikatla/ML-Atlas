#!/usr/bin/env python3
"""
ML Atlas — Strip markdown links from MDX algorithm files.

Converts [text](url) → text throughout the body of each MDX file (skipping
frontmatter, fenced code blocks, and inline code).

When a stripped link is NOT already recorded in documentation/link-registry.json,
the script adds it to the registry under the appropriate section so it can be
re-applied correctly later using apply_links.py.

Typical use-cases
-----------------
1. Strip ALL links before a full re-apply from the registry:
       python scripts/strip_links.py --apply

2. Strip only the broken 3-level /algorithms/ internal links (leave Wikipedia
   and external links untouched):
       python scripts/strip_links.py --internal-only --apply

3. Preview without writing anything:
       python scripts/strip_links.py --dry-run                   # all links
       python scripts/strip_links.py --internal-only --dry-run   # internal only

4. Process one algorithm:
       python scripts/strip_links.py --algorithm logistic-regression --apply

Usage
-----
    python scripts/strip_links.py [--apply] [--internal-only] [--algorithm SLUG]
                                  [--category CAT] [--dry-run]
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
# Helpers
# ---------------------------------------------------------------------------


def load_registry(registry_file: Path) -> dict:
    """Load link-registry.json. Exits with error if not found."""
    if not registry_file.exists():
        print(f"ERROR: Registry not found at {registry_file.relative_to(ROOT)}")
        print("Run `python scripts/build_link_registry.py` first.")
        sys.exit(1)
    return json.loads(registry_file.read_text(encoding="utf-8"))


def save_registry(registry: dict, registry_file: Path) -> None:
    """Write registry back to disk."""
    registry_file.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def get_frontmatter_end(text: str) -> int:
    """Return the index in text where frontmatter ends (the char after closing ---)."""
    if not text.startswith("---"):
        return 0
    try:
        end = text.index("---", 3)
        return end + 3
    except ValueError:
        return 0


def in_fenced_code(text: str, pos: int) -> bool:
    """True if pos is inside a fenced code block (``` or ~~~)."""
    prefix = text[:pos]
    fence_count = len(re.findall(r"^```", prefix, re.MULTILINE))
    return fence_count % 2 == 1


def in_inline_code(text: str, pos: int) -> bool:
    """True if pos is inside inline code (`...`)."""
    prefix = text[:pos]
    return prefix.count("`") % 2 == 1


# ---------------------------------------------------------------------------
# Link classification
# ---------------------------------------------------------------------------

_INTERNAL_3LEVEL = re.compile(
    r"/algorithms/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+", re.IGNORECASE
)
_INTERNAL_2LEVEL = re.compile(
    r"/algorithms/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+", re.IGNORECASE
)
# Matches any /algorithms/ path (for --internal-only stripping)
_ANY_INTERNAL = re.compile(r"/algorithms/", re.IGNORECASE)


def classify_url(url: str) -> str:
    """
    Classify a link URL into one of:
    - 'internal_3level'  : /algorithms/cat/subcat/slug  (broken format)
    - 'internal_2level'  : /algorithms/cat/slug  (correct format)
    - 'wikipedia'        : https://en.wikipedia.org/...
    - 'external'         : any other https:// link
    - 'other'            : relative or mailto etc.
    """
    if _INTERNAL_3LEVEL.match(url):
        return "internal_3level"
    if _INTERNAL_2LEVEL.match(url):
        return "internal_2level"
    if url.startswith("https://en.wikipedia.org/"):
        return "wikipedia"
    if url.startswith("http"):
        return "external"
    return "other"


def canonicalize_3level(url: str, registry: dict) -> str | None:
    """
    Try to convert a 3-level internal URL to a 2-level URL using the registry.
    Returns the corrected URL or None if the slug is not in the registry.

    /algorithms/supervised/classification/logistic-regression
      → /algorithms/supervised/logistic-regression
    """
    # Extract slug (last path component)
    slug = url.rstrip("/").split("/")[-1]
    # Look up the slug in algorithms section
    for _name, info in registry.get("algorithms", {}).items():
        if info.get("slug") == slug:
            return info["url"]
    return None


# ---------------------------------------------------------------------------
# Core strip logic
# ---------------------------------------------------------------------------

# Matches [link text](url)
_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def strip_links_from_body(
    body: str,
    body_offset: int,
    internal_only: bool,
    registry: dict,
    new_external: list,
    new_wikipedia: list,
) -> tuple[str, int, int]:
    """
    Strip markdown links from body text.

    Returns (updated_body, n_stripped, n_skipped).
    Side-effects: appends new discoveries to new_external / new_wikipedia lists.
    Each element of those lists is a dict: {text, url, slug (if applicable)}.
    """
    stripped = 0
    skipped = 0
    result = body

    # We process in reverse order so that start/end indices remain valid
    matches = list(_LINK_PATTERN.finditer(body))
    for m in reversed(matches):
        start, end = m.start(), m.end()
        display_text = m.group(1)
        url = m.group(2).strip()

        # Skip if inside fenced code block or inline code
        # (positions are relative to body, not full file)
        if in_fenced_code(body, start):
            skipped += 1
            continue
        if in_inline_code(body, start):
            skipped += 1
            continue

        url_type = classify_url(url)

        if internal_only and not _ANY_INTERNAL.search(url):
            # Only stripping internal links — leave this one
            continue

        # Record in registry if not already there
        if url_type in ("internal_3level", "internal_2level"):
            # Check if in registry algorithms section
            already = any(
                info.get("url") == url or info.get("slug") == url.rstrip("/").split("/")[-1]
                for info in registry.get("algorithms", {}).values()
            )
            if not already:
                new_external.append({"text": display_text, "url": url, "type": url_type})
        elif url_type == "wikipedia":
            already = url in registry.get("wikipedia", {}).values()
            if not already:
                new_wikipedia.append({"text": display_text, "url": url})
        elif url_type == "external":
            already = (
                display_text in registry.get("external", {})
                and registry["external"][display_text] == url
            )
            if not already:
                new_external.append({"text": display_text, "url": url, "type": "external"})

        # Strip: replace [text](url) with text
        result = result[:start] + display_text + result[end:]
        stripped += 1

    return result, stripped, skipped


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Strip markdown links from MDX algorithm files"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to disk (default is dry-run)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing (default behaviour if --apply not given)",
    )
    parser.add_argument(
        "--internal-only",
        action="store_true",
        help="Only strip /algorithms/ internal links (leave Wikipedia and external links)",
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
    args = parser.parse_args()

    dry_run = not args.apply
    if dry_run:
        print("DRY-RUN — no files will be modified. Pass --apply to write changes.\n")

    registry = load_registry(REGISTRY_FILE)

    # Collect MDX files to process
    mdx_files: list[Path] = sorted(CONTENT_DIR.rglob("*.mdx"))

    if args.algorithm:
        mdx_files = [f for f in mdx_files if f.stem == args.algorithm]
        if not mdx_files:
            print(f"ERROR: No MDX file with slug {args.algorithm!r}")
            sys.exit(1)

    if args.category:
        mdx_files = [f for f in mdx_files if f.relative_to(CONTENT_DIR).parts[0] == args.category]
        if not mdx_files:
            print(f"ERROR: No MDX files found in category {args.category!r}")
            sys.exit(1)

    scope = "internal links only" if args.internal_only else "all links"
    print(f"Processing {len(mdx_files)} files — stripping {scope}\n")

    total_stripped = 0
    total_skipped = 0
    files_changed = 0
    all_new_external: list[dict] = []
    all_new_wikipedia: list[dict] = []

    for mdx_path in mdx_files:
        text = mdx_path.read_text(encoding="utf-8")
        body_start = get_frontmatter_end(text)
        body = text[body_start:]

        new_ext: list[dict] = []
        new_wiki: list[dict] = []

        new_body, n_stripped, n_skipped = strip_links_from_body(
            body=body,
            body_offset=body_start,
            internal_only=args.internal_only,
            registry=registry,
            new_external=new_ext,
            new_wikipedia=new_wiki,
        )

        total_stripped += n_stripped
        total_skipped += n_skipped

        if n_stripped > 0:
            files_changed += 1
            slug = mdx_path.stem
            print(f"  STRIP [{slug}] {n_stripped} link(s) removed")
            for item in new_ext:
                print(f"    + registry/external: {item['text']!r} → {item['url']}")
                all_new_external.append(item)
            for item in new_wiki:
                print(f"    + registry/wikipedia: {item['text']!r} → {item['url']}")
                all_new_wikipedia.append(item)

            if not dry_run:
                full_text = text[:body_start] + new_body
                mdx_path.write_text(full_text, encoding="utf-8")

    # Update registry with newly-discovered entries
    if not dry_run and (all_new_external or all_new_wikipedia):
        for item in all_new_wikipedia:
            term = item["text"]
            url = item["url"]
            if term not in registry["wikipedia"]:
                registry["wikipedia"][term] = url
        for item in all_new_external:
            text_key = item["text"]
            url = item["url"]
            if text_key not in registry.get("external", {}):
                registry.setdefault("external", {})[text_key] = url
        save_registry(registry, REGISTRY_FILE)
        print(f"\nRegistry updated: +{len(all_new_wikipedia)} wikipedia, +{len(all_new_external)} external entries")

    print()
    print("=" * 60)
    print(f"Files changed       : {files_changed}")
    print(f"Links stripped      : {total_stripped}")
    print(f"Links skipped       : {total_skipped}")
    if dry_run:
        print("\nRe-run with --apply to write changes.")
    else:
        print("\nChanges applied to disk.")


if __name__ == "__main__":
    main()
