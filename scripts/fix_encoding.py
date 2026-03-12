#!/usr/bin/env python3
"""
ML Atlas — MDX Encoding Fixer
==============================
Scans all MDX files in content/algorithms/ and replaces known Unicode
replacement character (U+FFFD) corruptions introduced when the source
CSV was read with a Latin-1/Windows-1252 vs UTF-8 encoding mismatch.

Run from the ML Atlas project root (ML-Atlas/):
    python scripts/fix_encoding.py

    # Dry run — preview changes without writing:
    python scripts/fix_encoding.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ── Correction map ────────────────────────────────────────────────────────────
# Keys are the corrupted strings (with U+FFFD), values are correct strings.
# Order matters: longer/more-specific patterns are applied first so shorter
# patterns don't partially match inside longer ones.

FIXES: dict[str, str] = {
    # Algorithm names in titles / comments / labels
    "Theil\ufffdSen Regressor":                   "Theil\u2013Sen Regressor",   # en-dash
    "Theil\ufffdSen":                              "Theil\u2013Sen",             # en-dash
    "DALL\ufffdE-style diffusion/decoder models":  "DALL-E-style diffusion/decoder models",
    "DALL\ufffdE":                                 "DALL-E",
    # Author / paper reference fields
    "Gauss \ufffd Method of Least Squares":        "Gauss \u2013 Method of Least Squares",
    "Breiman \ufffd CART":                         "Breiman \u2013 CART",        # en-dash
    "Sch\ufffdlkopf et al.":                       "Sch\u00f6lkopf et al.",      # ö
    "Sch\ufffdlkopf":                              "Sch\u00f6lkopf",             # ö
    "Eckart\ufffdYoung":                           "Eckart\u2013Young",          # en-dash
}

CONTENT_ROOT = Path("content/algorithms")


def fix_file(path: Path, dry_run: bool = False) -> list[str]:
    """
    Apply all FIXES to a single MDX file.
    Returns list of (old, new) replacement descriptions made; empty = no changes.
    """
    text = path.read_text(encoding="utf-8")
    original = text
    applied: list[str] = []

    for bad, good in FIXES.items():
        if bad in text:
            count = text.count(bad)
            text = text.replace(bad, good)
            applied.append(f"  '{bad}' → '{good}'  ({count}×)")

    if applied and not dry_run:
        path.write_text(text, encoding="utf-8")

    return applied


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix U+FFFD encoding corruption in ML Atlas MDX files."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without writing any files."
    )
    args = parser.parse_args()

    if not CONTENT_ROOT.exists():
        print(f"ERROR: {CONTENT_ROOT} not found.")
        print("Run this script from the ML Atlas project root (ML-Atlas/).")
        sys.exit(1)

    mdx_files = list(CONTENT_ROOT.rglob("*.mdx"))
    print(f"Scanning {len(mdx_files)} MDX files in {CONTENT_ROOT}/")
    if args.dry_run:
        print("DRY RUN — no files will be written.\n")

    total_files_changed = 0
    total_replacements  = 0

    for path in sorted(mdx_files):
        changes = fix_file(path, dry_run=args.dry_run)
        if changes:
            total_files_changed += 1
            total_replacements  += len(changes)
            rel = path.relative_to(CONTENT_ROOT)
            action = "Would fix" if args.dry_run else "Fixed"
            print(f"{action}: {rel}")
            for c in changes:
                print(c)

    print(f"\n{'─'*50}")
    if args.dry_run:
        print(f"Would fix {total_files_changed} file(s) with {total_replacements} replacement(s).")
    else:
        print(f"Fixed {total_files_changed} file(s) with {total_replacements} replacement(s).")

    # Final validation
    remaining = [
        str(f.relative_to(CONTENT_ROOT))
        for f in mdx_files
        if "\ufffd" in f.read_text(encoding="utf-8")
    ]
    if remaining:
        print(f"\n⚠️  {len(remaining)} file(s) still contain U+FFFD after fix:")
        for r in remaining:
            print(f"  {r}")
    else:
        print("✅ No U+FFFD characters remain in any MDX file.")


if __name__ == "__main__":
    main()
