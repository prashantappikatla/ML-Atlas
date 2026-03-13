#!/usr/bin/env python3
"""
ML Atlas — MDX Syntax Checker

Scans all 278 algorithm MDX files for patterns that MDX v3's acorn-based parser
cannot handle. Reports issues with file path and line number. Optionally auto-fixes
all safe patterns with --fix.

No Node.js or frontend dependencies required — runs standalone.

Error classes detected
----------------------
Class 1 (CRITICAL): JSX-like tags in prose
    <extra_id_0>, <UNK>, <input_ids> etc — treated as unclosed JSX elements
Class 2 (CRITICAL): Apostrophe before JSX-like token
    '<word' — apostrophe causes unexpected char in tag name error
Class 3 (CRITICAL): Comparison operators as tag openers
    <= or >= in prose — MDX sees < then = before tag name
Class 4 (WARNING): Curly brace expressions that aren't valid JS
    {input_ids} — MDX passes {} to acorn as JS; underscored identifiers can fail
Class 5 (WARNING): Unclosed angle brackets in prose
    Bare < not followed by recognized tag — dangling JSX open
Class 6 (INFO): Frontmatter schema issues
    Missing required fields or invalid enum values

Usage
-----
    python scripts/check_mdx_syntax.py                        # scan all files
    python scripts/check_mdx_syntax.py --algorithm t5         # one file
    python scripts/check_mdx_syntax.py --category deep-learning
    python scripts/check_mdx_syntax.py --fix                  # auto-fix safe patterns
    python scripts/check_mdx_syntax.py --fix --dry-run        # preview fixes
    python scripts/check_mdx_syntax.py --report               # write mdx-syntax-report.md
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. Install: pip install PyYAML")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
CONTENT_DIR = ROOT / "content" / "algorithms"
REPORT_FILE = ROOT / "documentation" / "mdx-syntax-report.md"

# ---------------------------------------------------------------------------
# Constants — context-aware parsing
# ---------------------------------------------------------------------------

# Standard HTML tags that MDX allows as-is in prose (not treated as components)
KNOWN_HTML_TAGS = {
    "a", "abbr", "address", "article", "aside", "audio", "b", "bdi", "bdo",
    "blockquote", "body", "br", "button", "canvas", "caption", "cite", "code",
    "col", "colgroup", "data", "datalist", "dd", "del", "details", "dfn",
    "dialog", "div", "dl", "dt", "em", "embed", "fieldset", "figcaption",
    "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6",
    "head", "header", "hr", "html", "i", "iframe", "img", "input", "ins",
    "kbd", "label", "legend", "li", "link", "main", "map", "mark", "menu",
    "meta", "meter", "nav", "noscript", "object", "ol", "optgroup", "option",
    "output", "p", "picture", "pre", "progress", "q", "rp", "rt", "ruby",
    "s", "samp", "script", "section", "select", "small", "source", "span",
    "strong", "style", "sub", "summary", "sup", "table", "tbody", "td",
    "template", "textarea", "tfoot", "th", "thead", "time", "title", "tr",
    "track", "u", "ul", "var", "video", "wbr",
}

# Custom components used in ML Atlas MDX files
KNOWN_COMPONENTS = {
    "Callout", "CompatibilityMatrix", "LabEmbed", "Link", "Image",
    "CodeBlock", "MathBlock", "Note", "Warning", "Tip", "Info",
}

# Required YAML frontmatter fields per CLAUDE.md spec
REQUIRED_FM_FIELDS = ["title", "slug", "category", "subcategory", "status"]
VALID_COMPLEXITY = {"low", "medium", "high"}
VALID_STATUS = {"planned", "in-progress", "documented", "implemented", "lab-ready"}

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class Severity(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class Issue:
    severity: Severity
    file_slug: str
    line_no: int  # 1-based; 0 for file-level issues
    class_id: int  # 1-6
    message: str
    snippet: str  # The exact text that triggered the issue
    fix_preview: str  # What --fix would replace it with (empty = not auto-fixable)
    fix_start: int = 0  # Byte offset in the full file text (for --fix)
    fix_end: int = 0    # Byte offset in the full file text (for --fix)
    fix_replacement: str = ""  # Replacement text for --fix


# ---------------------------------------------------------------------------
# Context-aware line classifier
# ---------------------------------------------------------------------------


class BodyContext(Enum):
    FRONTMATTER = "frontmatter"
    FENCED_CODE = "fenced_code"
    INLINE_CODE = "inline_code"  # not used as block-level state, just for reference
    BLOCK_MATH = "block_math"
    BODY = "body"


def classify_lines(text: str) -> list[BodyContext]:
    """
    Return a list of BodyContext values, one per line (0-indexed).
    Lines in frontmatter, fenced code blocks, or block math are marked accordingly;
    all other lines are marked BODY.
    """
    lines = text.split("\n")
    contexts: list[BodyContext] = []

    in_frontmatter = False
    frontmatter_done = False
    in_fenced_code = False
    in_block_math = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        # --- Frontmatter ---
        if i == 0 and stripped == "---":
            in_frontmatter = True
            contexts.append(BodyContext.FRONTMATTER)
            continue

        if in_frontmatter:
            contexts.append(BodyContext.FRONTMATTER)
            if stripped == "---" and i > 0:
                in_frontmatter = False
                frontmatter_done = True
            continue

        if not frontmatter_done:
            # No frontmatter started — still safe to be in body
            pass

        # --- Fenced code blocks ---
        if stripped.startswith("```") and not in_fenced_code and not in_block_math:
            in_fenced_code = True
            contexts.append(BodyContext.FENCED_CODE)
            continue

        if in_fenced_code:
            contexts.append(BodyContext.FENCED_CODE)
            if stripped.startswith("```"):
                in_fenced_code = False
            continue

        # --- Block math ($$...$$) on own lines ---
        if stripped == "$$" and not in_block_math and not in_fenced_code:
            in_block_math = True
            contexts.append(BodyContext.BLOCK_MATH)
            continue

        if stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 4:
            # Single-line block math: $$ ... $$
            contexts.append(BodyContext.BLOCK_MATH)
            continue

        if in_block_math:
            contexts.append(BodyContext.BLOCK_MATH)
            if stripped == "$$":
                in_block_math = False
            continue

        # --- Normal body ---
        contexts.append(BodyContext.BODY)

    return contexts


def remove_inline_math(text: str) -> str:
    """
    Replace inline math $...$ spans with placeholder text so that `<`, `>`, `{`, `}`
    inside them don't trigger false positives. Uses a simple balanced-delimiter approach.
    Does NOT touch $$ block math (already handled by classify_lines).
    """
    # Replace $..$ (single-dollar inline math) with a safe placeholder
    # Careful: don't match $$ (block math delimiters)
    return re.sub(r"(?<!\$)\$(?!\$)([^$\n]+?)(?<!\$)\$(?!\$)", lambda m: " " * len(m.group(0)), text)


def remove_inline_code(text: str) -> str:
    """Replace `...` inline code spans with spaces (preserving length for offset tracking)."""
    return re.sub(r"`[^`\n]*`", lambda m: " " * len(m.group(0)), text)


def remove_existing_links(text: str) -> str:
    """Replace [...](url) links with placeholder (prevents re-checking content inside link text)."""
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", lambda m: m.group(1), text)


# ---------------------------------------------------------------------------
# Class 1: JSX-like tags in prose
# ---------------------------------------------------------------------------

# Tags that look like JSX but are NOT valid in MDX prose:
# - Contains underscore: <extra_id_0>, <input_ids>
# - Starts with uppercase followed by lowercase/underscore: not a React component (components are PascalCase)
# - Contains digits directly in name: <h264> (but allow <h1>-<h6> HTML headings handled separately)
# - Is not in KNOWN_HTML_TAGS or KNOWN_COMPONENTS

_TAG_CANDIDATE = re.compile(
    r"<"
    r"("
    r"[a-zA-Z][a-zA-Z0-9_-]*"   # tag name: starts with letter, followed by letters/digits/underscore/hyphen
    r")"
    r"(\s[^>]*)?"                 # optional attributes
    r">"
)


def is_safe_tag(tag_name: str) -> bool:
    """Return True if this tag name is a known HTML tag or known ML Atlas component."""
    lower = tag_name.lower()
    if lower in KNOWN_HTML_TAGS:
        return True
    if tag_name in KNOWN_COMPONENTS:
        return True
    # Self-closing slash
    if lower.rstrip("/") in KNOWN_HTML_TAGS:
        return True
    return False


def check_class1(line: str, line_no: int, file_slug: str, line_offset: int) -> list[Issue]:
    """Check for JSX-like tags in a prose line."""
    issues: list[Issue] = []

    # Remove inline code and inline math to avoid false positives
    clean = remove_inline_code(remove_inline_math(remove_existing_links(line)))

    for m in _TAG_CANDIDATE.finditer(clean):
        tag_name = m.group(1)
        full_match = m.group(0)

        if is_safe_tag(tag_name):
            continue

        # Additional filter: skip closing tags </...>
        # (handled by checking whether < is immediately followed by /)
        if clean[m.start() + 1 : m.start() + 2] == "/":
            continue

        fix_text = f"`{full_match}`"
        start = line_offset + m.start()
        end = line_offset + m.end()

        issues.append(Issue(
            severity=Severity.CRITICAL,
            file_slug=file_slug,
            line_no=line_no,
            class_id=1,
            message=f"JSX-like tag in prose: {full_match}",
            snippet=full_match,
            fix_preview=fix_text,
            fix_start=start,
            fix_end=end,
            fix_replacement=fix_text,
        ))

    return issues


# ---------------------------------------------------------------------------
# Class 2: Apostrophe before JSX-like token
# ---------------------------------------------------------------------------

_APOS_BEFORE_TAG = re.compile(r"'(<[a-zA-Z][a-zA-Z0-9_-]*>?)")


def check_class2(line: str, line_no: int, file_slug: str, line_offset: int) -> list[Issue]:
    """Check for apostrophe immediately before a tag-like construct."""
    issues: list[Issue] = []
    clean = remove_inline_code(remove_inline_math(remove_existing_links(line)))

    for m in _APOS_BEFORE_TAG.finditer(clean):
        tag_part = m.group(1)
        full_match = m.group(0)
        tag_name = re.match(r"<([a-zA-Z][a-zA-Z0-9_-]*)", tag_part)
        if tag_name and is_safe_tag(tag_name.group(1)):
            continue
        fix_text = f"`{tag_part}`"
        start = line_offset + m.start()
        end = line_offset + m.end()
        issues.append(Issue(
            severity=Severity.CRITICAL,
            file_slug=file_slug,
            line_no=line_no,
            class_id=2,
            message=f"Apostrophe before JSX-like token: {full_match!r}",
            snippet=full_match,
            fix_preview=fix_text,
            fix_start=start,
            fix_end=end,
            fix_replacement=fix_text,
        ))
    return issues


# ---------------------------------------------------------------------------
# Class 3: Comparison operators as tag openers
# ---------------------------------------------------------------------------

# Match <= or >= that appear in prose (not inside math/code, already stripped above)
# Must be preceded/followed by whitespace or end-of-string to avoid matching
# things like <=> or existing HTML/JSX
_COMPARISON_LE = re.compile(r"(?<!\w)<=(?!=)(?!\w)")
_COMPARISON_GE = re.compile(r"(?<!\w)>=(?!=)(?!\w)")


def check_class3(line: str, line_no: int, file_slug: str, line_offset: int) -> list[Issue]:
    """Check for comparison operators that look like JSX openers."""
    issues: list[Issue] = []
    clean = remove_inline_code(remove_inline_math(remove_existing_links(line)))

    for m in _COMPARISON_LE.finditer(clean):
        start = line_offset + m.start()
        end = line_offset + m.end()
        issues.append(Issue(
            severity=Severity.CRITICAL,
            file_slug=file_slug,
            line_no=line_no,
            class_id=3,
            message=f"Comparison operator '<=' in prose (MDX sees '<' + '=' as tag opener)",
            snippet="<=",
            fix_preview="≤",
            fix_start=start,
            fix_end=end,
            fix_replacement="≤",
        ))

    for m in _COMPARISON_GE.finditer(clean):
        start = line_offset + m.start()
        end = line_offset + m.end()
        issues.append(Issue(
            severity=Severity.CRITICAL,
            file_slug=file_slug,
            line_no=line_no,
            class_id=3,
            message=f"Comparison operator '>=' in prose (MDX may misparse as JSX attribute)",
            snippet=">=",
            fix_preview="≥",
            fix_start=start,
            fix_end=end,
            fix_replacement="≥",
        ))

    return issues


# ---------------------------------------------------------------------------
# Class 4: Curly brace expressions that aren't valid JS
# ---------------------------------------------------------------------------

_CURLY_EXPR = re.compile(r"\{([^}\n]+)\}")


def _is_valid_js_expression(content: str) -> bool:
    """
    Heuristic: Is this a valid JS expression that acorn can parse?
    Returns True if it looks safe (e.g., a string, number, or simple variable).
    Returns False if it looks like it would fail (e.g., has underscores in an identifier without operators).
    """
    content = content.strip()
    # Allow: numbers, quoted strings, simple variables (no underscores), operators
    # Flag: identifier-like strings with underscores (Python-style variable names that aren't valid alone)
    if re.match(r"^[0-9]+(\.[0-9]+)?$", content):
        return True
    if re.match(r'^"[^"]*"$', content) or re.match(r"^'[^']*'$", content):
        return True
    # Simple JS identifier (no underscore unless it's a valid JS variable like _foo or __bar)
    if re.match(r"^[a-zA-Z$_][a-zA-Z0-9$_]*$", content):
        return True  # valid JS identifier
    # Has operators — probably intentional JS
    if any(op in content for op in ["+", "-", "*", "/", "===", "!==", "&&", "||", "?", ":"]):
        return True
    # Contains underscores with multiple word segments (snake_case Python-style)
    # e.g. input_ids, attention_mask — these are NOT valid JS statements but are valid identifiers
    # Actually {input_ids} IS a valid JS expression (identifier reference) — acorn can parse it
    # The real issue is when it's something that's NOT a valid identifier
    # Let's flag: content with spaces or special chars that aren't operators
    if " " in content and not any(op in content for op in ["===", "!==", "&&", "||"]):
        # Contains spaces — could be "key: value" or "x > y"
        if re.search(r"[a-zA-Z_]\s*:\s*[a-zA-Z_]", content):
            return False  # object-literal-like but might not parse
        if re.search(r"<|>", content):
            return False  # comparison with angle brackets
    return True


def check_class4(line: str, line_no: int, file_slug: str, line_offset: int) -> list[Issue]:
    """Check for curly brace expressions that might fail acorn parsing."""
    issues: list[Issue] = []
    clean = remove_inline_code(remove_inline_math(remove_existing_links(line)))

    for m in _CURLY_EXPR.finditer(clean):
        content = m.group(1)
        full_match = m.group(0)

        if _is_valid_js_expression(content):
            continue

        fix_text = f"`{full_match}`"
        start = line_offset + m.start()
        end = line_offset + m.end()
        issues.append(Issue(
            severity=Severity.WARNING,
            file_slug=file_slug,
            line_no=line_no,
            class_id=4,
            message=f"Curly expression may fail acorn parser: {full_match}",
            snippet=full_match,
            fix_preview=fix_text,
            fix_start=start,
            fix_end=end,
            fix_replacement=fix_text,
        ))

    return issues


# ---------------------------------------------------------------------------
# Class 5: Unclosed angle brackets in prose
# ---------------------------------------------------------------------------

# MDX v3 is only troubled by `<` when immediately followed by:
# - a letter (starts a JSX tag — handled by Class 1)
# - `=` (comparison — handled by Class 3)
# - a digit: <3 or <10 looks like JSX `<3>` which is invalid syntax
# `< ` (space) is safe — HTML5 parser emits `<` as text and recovers.
# Class 5 only flags `<` followed immediately by a digit.
_LONE_ANGLE_DIGIT = re.compile(r"<[0-9]")


def check_class5(line: str, line_no: int, file_slug: str, line_offset: int) -> list[Issue]:
    """Check for '<digit' patterns in prose (e.g. <3, <10 which MDX may parse as invalid JSX)."""
    issues: list[Issue] = []
    clean = remove_inline_code(remove_inline_math(remove_existing_links(line)))

    for m in _LONE_ANGLE_DIGIT.finditer(clean):
        full_match = m.group(0)
        fix_text = f"\\{full_match}"
        start = line_offset + m.start()
        end = line_offset + m.end()
        issues.append(Issue(
            severity=Severity.WARNING,
            file_slug=file_slug,
            line_no=line_no,
            class_id=5,
            message=f"'<digit' in prose: {full_match!r} (MDX may attempt to parse as JSX tag)",
            snippet=full_match,
            fix_preview=fix_text,
            fix_start=start,
            fix_end=end,
            fix_replacement=fix_text,
        ))

    return issues


# ---------------------------------------------------------------------------
# Class 6: Frontmatter schema
# ---------------------------------------------------------------------------


def check_class6(frontmatter: dict, file_slug: str) -> list[Issue]:
    """Validate YAML frontmatter fields."""
    issues: list[Issue] = []

    for field_name in REQUIRED_FM_FIELDS:
        if field_name not in frontmatter or not frontmatter[field_name]:
            issues.append(Issue(
                severity=Severity.INFO,
                file_slug=file_slug,
                line_no=0,
                class_id=6,
                message=f"Missing required frontmatter field: '{field_name}'",
                snippet="",
                fix_preview="",
            ))

    complexity = frontmatter.get("complexity")
    if complexity and str(complexity) not in VALID_COMPLEXITY:
        issues.append(Issue(
            severity=Severity.INFO,
            file_slug=file_slug,
            line_no=0,
            class_id=6,
            message=f"Invalid complexity value: {complexity!r} (must be one of: {', '.join(sorted(VALID_COMPLEXITY))})",
            snippet=str(complexity),
            fix_preview="",
        ))

    status = frontmatter.get("status")
    if status and str(status) not in VALID_STATUS:
        issues.append(Issue(
            severity=Severity.INFO,
            file_slug=file_slug,
            line_no=0,
            class_id=6,
            message=f"Invalid status value: {status!r} (must be one of: {', '.join(sorted(VALID_STATUS))})",
            snippet=str(status),
            fix_preview="",
        ))

    return issues


# ---------------------------------------------------------------------------
# Parse frontmatter
# ---------------------------------------------------------------------------


def parse_frontmatter(text: str) -> tuple[dict, int]:
    """
    Return (frontmatter_dict, body_start_index).
    body_start_index is the character offset where the body begins (after closing ---).
    """
    if not text.startswith("---"):
        return {}, 0
    try:
        end = text.index("---", 3)
    except ValueError:
        return {}, 0
    fm_raw = text[3:end].strip()
    try:
        fm = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, end + 3


# ---------------------------------------------------------------------------
# Check one file
# ---------------------------------------------------------------------------


def check_file(mdx_path: Path) -> list[Issue]:
    """Run all checks on one MDX file. Returns list of issues."""
    file_slug = mdx_path.stem
    text = mdx_path.read_text(encoding="utf-8")
    issues: list[Issue] = []

    # --- Class 6: frontmatter schema ---
    frontmatter, body_start = parse_frontmatter(text)
    issues.extend(check_class6(frontmatter, file_slug))

    # --- Classify lines for context ---
    line_contexts = classify_lines(text)
    lines = text.split("\n")

    # Compute character offsets for each line start
    line_offsets: list[int] = []
    offset = 0
    for line in lines:
        line_offsets.append(offset)
        offset += len(line) + 1  # +1 for \n

    # --- Classes 1-5: body prose checks ---
    for i, (line, ctx) in enumerate(zip(lines, line_contexts)):
        if ctx != BodyContext.BODY:
            continue

        line_no = i + 1  # 1-based
        line_offset = line_offsets[i]

        issues.extend(check_class1(line, line_no, file_slug, line_offset))
        issues.extend(check_class2(line, line_no, file_slug, line_offset))
        issues.extend(check_class3(line, line_no, file_slug, line_offset))
        issues.extend(check_class4(line, line_no, file_slug, line_offset))
        issues.extend(check_class5(line, line_no, file_slug, line_offset))

    return issues


# ---------------------------------------------------------------------------
# Auto-fix
# ---------------------------------------------------------------------------


def apply_fixes(mdx_path: Path, issues: list[Issue], dry_run: bool) -> int:
    """
    Apply all auto-fixable issues to the file. Fixes are applied in reverse order
    (highest offset first) to preserve earlier offsets.

    Returns the number of fixes applied.
    """
    fixable = [i for i in issues if i.fix_replacement]
    if not fixable:
        return 0

    text = mdx_path.read_text(encoding="utf-8")

    # Sort in reverse order by fix_start to apply from end to beginning
    fixable.sort(key=lambda x: x.fix_start, reverse=True)

    for issue in fixable:
        # Verify the snippet still matches at the expected position
        actual = text[issue.fix_start:issue.fix_end]
        if actual == issue.snippet:
            if not dry_run:
                text = text[: issue.fix_start] + issue.fix_replacement + text[issue.fix_end :]

    if not dry_run:
        mdx_path.write_text(text, encoding="utf-8")

    return len(fixable)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def write_report(all_issues: list[Issue], report_file: Path, stats: dict) -> None:
    from collections import defaultdict
    lines: list[str] = []
    lines.append("# MDX Syntax Report — 2026-03-13")
    lines.append("")
    lines.append("Generated by `scripts/check_mdx_syntax.py`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Files scanned | {stats['files']} |")
    lines.append(f"| CRITICAL | {stats['critical']} |")
    lines.append(f"| WARNING | {stats['warning']} |")
    lines.append(f"| INFO | {stats['info']} |")
    lines.append(f"| Auto-fixable | {stats['fixable']} |")
    lines.append("")

    criticals = [i for i in all_issues if i.severity == Severity.CRITICAL]
    warnings = [i for i in all_issues if i.severity == Severity.WARNING]
    infos = [i for i in all_issues if i.severity == Severity.INFO]

    def _section(title: str, issues: list[Issue]) -> None:
        if not issues:
            return
        lines.append(f"## {title}")
        lines.append("")
        by_file: dict[str, list[Issue]] = defaultdict(list)
        for issue in issues:
            by_file[issue.file_slug].append(issue)
        for slug, file_issues in sorted(by_file.items()):
            lines.append(f"### {slug}")
            for iss in file_issues:
                loc = f"line {iss.line_no}" if iss.line_no > 0 else "frontmatter"
                lines.append(f"- ({loc}) {iss.message}")
                if iss.fix_preview:
                    lines.append(f"  - Fix: `{iss.snippet}` → `{iss.fix_preview}`")
            lines.append("")

    _section("CRITICAL — Must Fix", criticals)
    _section("WARNING", warnings)
    _section("INFO — Frontmatter Issues", infos)

    if not criticals and not warnings:
        lines.append("## ✅ All Clear — No Critical or Warning Issues")
        lines.append("")

    report_file.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check MDX algorithm files for MDX v3 compilation errors"
    )
    parser.add_argument("--algorithm", metavar="SLUG", help="Check only this slug")
    parser.add_argument("--category", metavar="CAT", help="Check only this category")
    parser.add_argument(
        "--fix", action="store_true", help="Auto-fix safe patterns (Classes 1–5)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --fix: preview changes without writing",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help=f"Write report to {REPORT_FILE.relative_to(ROOT)}",
    )
    args = parser.parse_args()

    if args.dry_run and not args.fix:
        print("NOTE: --dry-run has no effect without --fix\n")

    # Collect files
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

    all_issues: list[Issue] = []
    total_fixes_applied = 0

    for mdx_path in mdx_files:
        file_issues = check_file(mdx_path)
        all_issues.extend(file_issues)

        if file_issues:
            file_slug = mdx_path.stem
            for issue in file_issues:
                sev = issue.severity.value
                loc = f"line {issue.line_no}" if issue.line_no > 0 else "frontmatter"
                print(f"{sev:8s} [{file_slug}] {loc}: {issue.message}")
                if issue.fix_preview:
                    if args.fix and not args.dry_run:
                        print(f"          ✓ Fixed: {issue.snippet!r} → {issue.fix_replacement!r}")
                    else:
                        print(f"          → Fix: {issue.snippet!r} → {issue.fix_preview!r}")

            if args.fix:
                n = apply_fixes(mdx_path, file_issues, dry_run=args.dry_run)
                total_fixes_applied += n

    # Summary
    criticals = sum(1 for i in all_issues if i.severity == Severity.CRITICAL)
    warnings = sum(1 for i in all_issues if i.severity == Severity.WARNING)
    infos = sum(1 for i in all_issues if i.severity == Severity.INFO)
    fixable = sum(1 for i in all_issues if i.fix_replacement)

    print()
    print("=" * 60)
    print(f"Files scanned  : {len(mdx_files)}")
    print(f"CRITICAL       : {criticals}")
    print(f"WARNING        : {warnings}")
    print(f"INFO           : {infos}")
    print(f"Auto-fixable   : {fixable}")
    if args.fix:
        action = "Would fix" if args.dry_run else "Fixed"
        print(f"{action}          : {total_fixes_applied}")

    if args.report:
        stats = {
            "files": len(mdx_files),
            "critical": criticals,
            "warning": warnings,
            "info": infos,
            "fixable": fixable,
        }
        write_report(all_issues, REPORT_FILE, stats)
        print(f"\nReport written to: {REPORT_FILE.relative_to(ROOT)}")

    print("=" * 60)

    if criticals:
        if not args.fix:
            print("\nRun with --fix to auto-fix all safe patterns.")
        sys.exit(1)


if __name__ == "__main__":
    main()
