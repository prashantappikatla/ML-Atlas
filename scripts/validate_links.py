#!/usr/bin/env python3
"""
ML Atlas — Validate all links across MDX algorithm files.

Checks every markdown link in every MDX body and reports:
  - CRITICAL: 3-level internal URLs (/algorithms/cat/subcat/slug → 404 in Next.js App Router)
  - CRITICAL: Internal links pointing to a slug that has no MDX file
  - WARNING:  Duplicate links (same URL appearing more than once in one file)
  - WARNING:  External URLs that return non-200 HTTP responses (requires --http)
  - INFO:     related: frontmatter slugs that don't match any MDX file
  - OK:       Counts of valid links

Output
------
Prints a summary to stdout and writes documentation/validation-report.md.

Usage
-----
    python scripts/validate_links.py                        # full validation (no HTTP by default)
    python scripts/validate_links.py --http                 # include HTTP checks (slow)
    python scripts/validate_links.py --no-report            # stdout only, skip writing report file
    python scripts/validate_links.py --algorithm SLUG       # one file
    python scripts/validate_links.py --fix-internal --dry-run   # preview 3-level URL fixes
    python scripts/validate_links.py --fix-internal --apply     # auto-fix 3-level → 2-level URLs
"""

import argparse
import json
import re
import sys
from collections import defaultdict
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
REGISTRY_FILE = ROOT / "documentation" / "link-registry.json"
REPORT_FILE = ROOT / "documentation" / "validation-report.md"

# ---------------------------------------------------------------------------
# Registry helpers
# ---------------------------------------------------------------------------


def load_registry(registry_file: Path) -> dict:
    if not registry_file.exists():
        return {}
    return json.loads(registry_file.read_text(encoding="utf-8"))


def get_all_valid_slugs(content_dir: Path) -> dict[str, str]:
    """Returns {slug: category} for all MDX files."""
    slugs: dict[str, str] = {}
    for f in content_dir.rglob("*.mdx"):
        parts = f.relative_to(content_dir).parts
        category = parts[0]
        slugs[f.stem] = category
    return slugs


def load_registry_slug_to_url(registry: dict) -> dict[str, str]:
    """Returns {slug: url} from registry algorithms section."""
    result: dict[str, str] = {}
    for _name, info in registry.get("algorithms", {}).items():
        result[info["slug"]] = info["url"]
    return result


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_3LEVEL_INTERNAL = re.compile(r"^/algorithms/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+$", re.IGNORECASE)
_2LEVEL_INTERNAL = re.compile(r"^/algorithms/[a-zA-Z0-9-]+/[a-zA-Z0-9-]+$", re.IGNORECASE)
_ANY_INTERNAL = re.compile(r"^/algorithms/", re.IGNORECASE)


def get_frontmatter_end(text: str) -> int:
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
    return text[:pos].count("`") % 2 == 1


def parse_frontmatter_related(text: str) -> list[str]:
    """Extract the related: list from YAML frontmatter."""
    if not text.startswith("---"):
        return []
    try:
        end = text.index("---", 3)
    except ValueError:
        return []
    fm_raw = text[3:end].strip()
    try:
        fm = yaml.safe_load(fm_raw) or {}
        related = fm.get("related") or []
        return [str(s) for s in related if s]
    except yaml.YAMLError:
        return []


def extract_links_from_body(body: str) -> list[tuple[int, str, str]]:
    """
    Extract all markdown links from body text (skipping code blocks/inline code).
    Returns list of (pos, display_text, url).
    """
    results = []
    for m in _LINK_PATTERN.finditer(body):
        start = m.start()
        if in_fenced_code(body, start) or in_inline_code(body, start):
            continue
        results.append((start, m.group(1), m.group(2).strip()))
    return results


# ---------------------------------------------------------------------------
# Validation logic
# ---------------------------------------------------------------------------

Issue = dict  # typed for readability


def validate_file(
    mdx_path: Path,
    valid_slugs: dict[str, str],
    registry_slug_to_url: dict[str, str],
    http_check: bool,
) -> list[Issue]:
    """
    Validate all links in one MDX file. Returns list of issue dicts.
    Issue keys: severity, file, message, link_text, url, suggestion
    """
    issues: list[Issue] = []
    slug = mdx_path.stem
    text = mdx_path.read_text(encoding="utf-8")

    # --- Check related: frontmatter slugs ---
    for related_slug in parse_frontmatter_related(text):
        if related_slug not in valid_slugs:
            issues.append({
                "severity": "INFO",
                "file": slug,
                "message": f"related: slug {related_slug!r} has no MDX file",
                "link_text": "",
                "url": related_slug,
                "suggestion": "",
            })

    # --- Check body links ---
    body_start = get_frontmatter_end(text)
    body = text[body_start:]
    links = extract_links_from_body(body)

    # Detect duplicates: count URL occurrences
    url_count: dict[str, int] = defaultdict(int)
    for _pos, _text, url in links:
        url_count[url] += 1

    seen_urls: set[str] = set()

    for pos, link_text, url in links:
        # --- Duplicate link check ---
        if url in seen_urls:
            issues.append({
                "severity": "WARNING",
                "file": slug,
                "message": f"Duplicate link: {link_text!r} → {url} (appears {url_count[url]}×)",
                "link_text": link_text,
                "url": url,
                "suggestion": "Keep only the first occurrence per page",
            })
        seen_urls.add(url)

        # --- Internal link checks ---
        if _3LEVEL_INTERNAL.match(url):
            # Broken 3-level internal link
            url_slug = url.rstrip("/").split("/")[-1]
            correct_url = registry_slug_to_url.get(url_slug)
            suggestion = f"Change to: {correct_url}" if correct_url else "Slug not in registry"
            issues.append({
                "severity": "CRITICAL",
                "file": slug,
                "message": f"3-level internal URL (404): {url}",
                "link_text": link_text,
                "url": url,
                "suggestion": suggestion,
            })

        elif _2LEVEL_INTERNAL.match(url):
            # Correct format — verify slug exists
            parts = url.strip("/").split("/")  # ["algorithms", cat, slug]
            if len(parts) == 3:
                link_slug = parts[2]
                link_cat = parts[1]
                if link_slug not in valid_slugs:
                    issues.append({
                        "severity": "CRITICAL",
                        "file": slug,
                        "message": f"Internal link points to non-existent slug: {url}",
                        "link_text": link_text,
                        "url": url,
                        "suggestion": "Add the MDX file or fix the slug",
                    })
                elif valid_slugs.get(link_slug) != link_cat:
                    issues.append({
                        "severity": "WARNING",
                        "file": slug,
                        "message": f"Internal link category mismatch: {url} (actual category: {valid_slugs[link_slug]!r})",
                        "link_text": link_text,
                        "url": url,
                        "suggestion": f"Change to /algorithms/{valid_slugs[link_slug]}/{link_slug}",
                    })

        elif url.startswith("http") and http_check:
            # External link — HTTP check
            import urllib.request
            import urllib.error

            try:
                req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "MLAtlas/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    if resp.status >= 400:
                        issues.append({
                            "severity": "WARNING",
                            "file": slug,
                            "message": f"External link returned HTTP {resp.status}: {url}",
                            "link_text": link_text,
                            "url": url,
                            "suggestion": "Verify URL or update/remove",
                        })
            except urllib.error.HTTPError as e:
                if e.code >= 400:
                    issues.append({
                        "severity": "WARNING",
                        "file": slug,
                        "message": f"External link HTTP error {e.code}: {url}",
                        "link_text": link_text,
                        "url": url,
                        "suggestion": "Verify URL or update/remove",
                    })
            except Exception as e:
                issues.append({
                    "severity": "WARNING",
                    "file": slug,
                    "message": f"External link unreachable ({type(e).__name__}): {url}",
                    "link_text": link_text,
                    "url": url,
                    "suggestion": "Verify URL or update/remove",
                })

    return issues


# ---------------------------------------------------------------------------
# Fix 3-level internal URLs
# ---------------------------------------------------------------------------


def fix_3level_urls_in_file(
    mdx_path: Path,
    registry_slug_to_url: dict[str, str],
    dry_run: bool,
) -> int:
    """
    Auto-fix all 3-level internal URLs in one MDX file to 2-level using the registry.
    Returns the number of links fixed.
    """
    text = mdx_path.read_text(encoding="utf-8")
    body_start = get_frontmatter_end(text)
    body = text[body_start:]

    n_fixed = 0

    def replacer(m: re.Match) -> str:
        nonlocal n_fixed
        link_text_val = m.group(1)
        url = m.group(2).strip()
        # Handle both 3-level internal links (any case) and nested/malformed ones
        if _ANY_INTERNAL.match(url):
            parts = url.strip("/").split("/")
            if len(parts) >= 3:  # 3-level or deeper
                url_slug = parts[-1].lower()  # normalize case
                # Try exact slug first, then case-insensitive scan
                correct_url = registry_slug_to_url.get(url_slug)
                if not correct_url:
                    for slug, cand_url in registry_slug_to_url.items():
                        if slug.lower() == url_slug:
                            correct_url = cand_url
                            break
                if correct_url:
                    n_fixed += 1
                    return f"[{link_text_val}]({correct_url})"
        return m.group(0)

    new_body = _LINK_PATTERN.sub(replacer, body)

    if n_fixed > 0 and not dry_run:
        full_text = text[:body_start] + new_body
        mdx_path.write_text(full_text, encoding="utf-8")

    return n_fixed


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------


def write_report(issues: list[Issue], report_file: Path, stats: dict) -> None:
    lines: list[str] = []
    lines.append("# Link Validation Report — 2026-03-12")
    lines.append("")
    lines.append("Generated by `scripts/validate_links.py`")
    lines.append("")

    criticals = [i for i in issues if i["severity"] == "CRITICAL"]
    warnings = [i for i in issues if i["severity"] == "WARNING"]
    infos = [i for i in issues if i["severity"] == "INFO"]

    # Stats
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| MDX files scanned | {stats['files']} |")
    lines.append(f"| Total links found | {stats['total_links']} |")
    lines.append(f"| CRITICAL issues | {len(criticals)} |")
    lines.append(f"| WARNING issues | {len(warnings)} |")
    lines.append(f"| INFO notices | {len(infos)} |")
    lines.append("")

    if criticals:
        lines.append("## CRITICAL — Must Fix")
        lines.append("")
        by_file: dict[str, list[Issue]] = defaultdict(list)
        for issue in criticals:
            by_file[issue["file"]].append(issue)
        for file_slug, file_issues in sorted(by_file.items()):
            lines.append(f"### [{file_slug}]")
            for i in file_issues:
                lines.append(f"- {i['message']}")
                if i["suggestion"]:
                    lines.append(f"  - ✓ {i['suggestion']}")
            lines.append("")

    if warnings:
        lines.append("## WARNING")
        lines.append("")
        by_file = defaultdict(list)
        for issue in warnings:
            by_file[issue["file"]].append(issue)
        for file_slug, file_issues in sorted(by_file.items()):
            lines.append(f"### [{file_slug}]")
            for i in file_issues:
                lines.append(f"- {i['message']}")
                if i["suggestion"]:
                    lines.append(f"  - ✓ {i['suggestion']}")
            lines.append("")

    if infos:
        lines.append("## INFO — Related Frontmatter Issues")
        lines.append("")
        for issue in sorted(infos, key=lambda x: x["file"]):
            lines.append(f"- `{issue['file']}`: {issue['message']}")
        lines.append("")

    if not criticals and not warnings:
        lines.append("## ✅ All Clear")
        lines.append("")
        lines.append("No critical or warning issues found.")
        lines.append("")

    report_file.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate all links in MDX algorithm files"
    )
    parser.add_argument(
        "--http",
        action="store_true",
        help="Perform HTTP HEAD checks on external URLs (slow — makes network requests)",
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Do not write documentation/validation-report.md",
    )
    parser.add_argument(
        "--algorithm",
        metavar="SLUG",
        help="Validate only this algorithm slug",
    )
    parser.add_argument(
        "--category",
        metavar="CAT",
        help="Validate only algorithms in this category",
    )
    parser.add_argument(
        "--fix-internal",
        action="store_true",
        help="Auto-fix 3-level internal URLs → 2-level using registry",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="With --fix-internal: write changes to disk (default is dry-run)",
    )
    args = parser.parse_args()

    registry = load_registry(REGISTRY_FILE)
    valid_slugs = get_all_valid_slugs(CONTENT_DIR)
    registry_slug_to_url = load_registry_slug_to_url(registry)

    mdx_files: list[Path] = sorted(CONTENT_DIR.rglob("*.mdx"))
    if args.algorithm:
        mdx_files = [f for f in mdx_files if f.stem == args.algorithm]
    if args.category:
        mdx_files = [f for f in mdx_files if f.relative_to(CONTENT_DIR).parts[0] == args.category]

    # --- Fix mode ---
    if args.fix_internal:
        dry_run = not args.apply
        if dry_run:
            print("DRY-RUN: --fix-internal (no files modified). Pass --apply to write.\n")
        total_fixed = 0
        for mdx_path in mdx_files:
            n = fix_3level_urls_in_file(mdx_path, registry_slug_to_url, dry_run)
            if n > 0:
                total_fixed += n
                print(f"  {'WOULD FIX' if dry_run else 'FIXED'} [{mdx_path.stem}] {n} URL(s)")
        print(f"\n{'Would fix' if dry_run else 'Fixed'} {total_fixed} 3-level URL(s).")
        return

    # --- Validation mode ---
    if args.http:
        print("HTTP checks ENABLED (this may be slow)\n")
    else:
        print("HTTP checks DISABLED (pass --http to enable)\n")

    all_issues: list[Issue] = []
    total_links = 0

    for mdx_path in mdx_files:
        body_start = get_frontmatter_end(mdx_path.read_text(encoding="utf-8"))
        body = mdx_path.read_text(encoding="utf-8")[body_start:]
        total_links += len(extract_links_from_body(body))

        file_issues = validate_file(mdx_path, valid_slugs, registry_slug_to_url, args.http)
        all_issues.extend(file_issues)

    criticals = [i for i in all_issues if i["severity"] == "CRITICAL"]
    warnings = [i for i in all_issues if i["severity"] == "WARNING"]
    infos = [i for i in all_issues if i["severity"] == "INFO"]

    # Print summary
    print("=" * 60)
    print(f"Files scanned  : {len(mdx_files)}")
    print(f"Links found    : {total_links}")
    print(f"CRITICAL       : {len(criticals)}")
    print(f"WARNING        : {len(warnings)}")
    print(f"INFO           : {len(infos)}")
    print("=" * 60)

    if criticals:
        print(f"\n--- CRITICAL ({len(criticals)}) ---")
        for i in criticals[:20]:
            print(f"  [{i['file']}] {i['message']}")
            if i["suggestion"]:
                print(f"    → {i['suggestion']}")
        if len(criticals) > 20:
            print(f"  ... and {len(criticals) - 20} more (see validation-report.md)")

    if warnings:
        print(f"\n--- WARNING ({len(warnings)}) ---")
        for i in warnings[:20]:
            print(f"  [{i['file']}] {i['message']}")
        if len(warnings) > 20:
            print(f"  ... and {len(warnings) - 20} more (see validation-report.md)")

    stats = {
        "files": len(mdx_files),
        "total_links": total_links,
    }

    if not args.no_report:
        write_report(all_issues, REPORT_FILE, stats)
        print(f"\nReport written to: {REPORT_FILE.relative_to(ROOT)}")

    if criticals:
        print("\nRun with --fix-internal --apply to auto-fix 3-level URL issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()
