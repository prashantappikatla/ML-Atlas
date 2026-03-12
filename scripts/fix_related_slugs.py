#!/usr/bin/env python3
"""
ML Atlas — Fix invalid slugs in MDX `related:` frontmatter.

Scans all 278 MDX algorithm files, validates every slug listed in the `related:`
frontmatter field against the set of real MDX files, and either:
  - Fixes known slug typos (via SLUG_FIXES map)
  - Removes slugs that are not real algorithm pages (concept terms, garbled text, etc.)

Usage:
    python scripts/fix_related_slugs.py              # dry-run (default, no changes)
    python scripts/fix_related_slugs.py --apply      # apply changes to MDX files
    python scripts/fix_related_slugs.py --slug k-means  # process one file only
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

import yaml  # PyYAML

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
CONTENT_DIR = ROOT / "content" / "algorithms"

# ---------------------------------------------------------------------------
# Known slug fixes: wrong slug → correct slug
# Add more here as new typos are discovered.
# ---------------------------------------------------------------------------

SLUG_FIXES: dict[str, str] = {
    "elastic-net-regression":   "elastic-net",
    "minibatch-kmeans":         "minibatch-k-means",
    "gmm":                      "gaussian-mixture-model",
    "actor":                    "actor-critic",
    "critic":                   "actor-critic",
    "gaussian-mixture-models":  "gaussian-mixture-model",
    "k-nearest-neighbor":       "k-nearest-neighbors",
    "knn":                      "k-nearest-neighbors",
    "pca":                      "principal-component-analysis",
    "svd":                      "singular-value-decomposition",
    "svm":                      "support-vector-machine",
    "cnn":                      "convolutional-neural-network",
    "rnn":                      "recurrent-neural-network",
    "lstm":                     "long-short-term-memory",
    "gru":                      "gated-recurrent-unit",
    "gbm":                      "gradient-boosting-classifier",
    "rf":                       "random-forest-classifier",
    "xgb":                      "xgboost",
    "lgbm":                     "lightgbm",
    "adaboost-classifier":      "adaboost",
    "gradient-boosted-trees":   "gradient-boosting-classifier",
    "gradient-boosting":        "gradient-boosting-classifier",
    "random-forest":            "random-forest-classifier",
    "decision-tree":            "decision-tree-classifier",
    "neural-network":           "multilayer-perceptron",
    "feedforward-neural-network": "multilayer-perceptron",
    "feedforward-network":      "multilayer-perceptron",
    "autoencoder-vae":          "variational-autoencoder",
    "vae":                      "variational-autoencoder",
    "gan":                      "generative-adversarial-network",
    "bert-model":               "bert",
    "gpt-model":                "gpt",
    "t5-model":                 "t5",
    "q-learning-algorithm":     "q-learning",
    "dqn-algorithm":            "dqn",
    "policy-gradient-method":   "policy-gradient",
    "monte-carlo-tree":         "monte-carlo-tree-search",
    "mcts":                     "monte-carlo-tree-search",
    "isolation-forest-algorithm": "isolation-forest",
    "one-class-svm":            "one-class-support-vector-machine",
    "hierarchical-agglomerative-clustering": "agglomerative-clustering",
    "spectral-clustering-algorithm": "spectral-clustering",
    "mean-shift-clustering":    "mean-shift",
    "dbscan-clustering":        "dbscan",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_all_valid_slugs() -> set[str]:
    """Return the set of all real MDX slugs from content/algorithms/."""
    slugs: set[str] = set()
    for f in CONTENT_DIR.rglob("*.mdx"):
        slugs.add(f.stem)
    return slugs


def parse_frontmatter(text: str) -> tuple[dict, str, str]:
    """
    Split MDX into (frontmatter_dict, raw_frontmatter_block, body).
    Returns (fm_dict, fm_raw, body) or raises ValueError if no frontmatter.
    """
    if not text.startswith("---"):
        raise ValueError("No frontmatter found")
    end = text.index("---", 3)
    fm_raw = text[3:end].strip()
    body = text[end + 3:]
    fm_dict = yaml.safe_load(fm_raw) or {}
    return fm_dict, fm_raw, body


def rebuild_mdx(fm_dict: dict, body: str) -> str:
    """Serialize frontmatter dict back to YAML and rebuild the MDX string."""
    fm_yaml = yaml.dump(
        fm_dict,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    )
    return f"---\n{fm_yaml}---{body}"


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def fix_file(
    mdx_path: Path,
    valid_slugs: set[str],
    dry_run: bool,
) -> tuple[int, int, int]:
    """
    Process one MDX file.
    Returns (kept, fixed, removed) counts.
    """
    text = mdx_path.read_text(encoding="utf-8")
    try:
        fm, _fm_raw, body = parse_frontmatter(text)
    except (ValueError, yaml.YAMLError) as e:
        print(f"  SKIP {mdx_path.name}: cannot parse frontmatter ({e})")
        return 0, 0, 0

    original_related: list[str] = fm.get("related") or []
    if not original_related:
        return 0, 0, 0

    kept, fixed, removed = 0, 0, 0
    new_related: list[str] = []
    changed = False

    for slug in original_related:
        if slug in valid_slugs:
            # Already valid
            new_related.append(slug)
            kept += 1
        elif slug in SLUG_FIXES and SLUG_FIXES[slug] in valid_slugs:
            # Known typo — fix it
            corrected = SLUG_FIXES[slug]
            print(f"  FIX    {mdx_path.name}: {slug!r} → {corrected!r}")
            new_related.append(corrected)
            fixed += 1
            changed = True
        else:
            # No matching MDX file and no known fix → remove
            print(f"  REMOVE {mdx_path.name}: {slug!r} (no matching algorithm page)")
            removed += 1
            changed = True

    if changed:
        # Deduplicate while preserving order
        seen: set[str] = set()
        deduped: list[str] = []
        for s in new_related:
            if s not in seen:
                seen.add(s)
                deduped.append(s)
        new_related = deduped

        fm["related"] = new_related
        if not dry_run:
            updated_text = rebuild_mdx(fm, body)
            mdx_path.write_text(updated_text, encoding="utf-8")

    return kept, fixed, removed


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fix invalid slugs in MDX related: frontmatter"
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write changes to disk (default is dry-run)",
    )
    parser.add_argument(
        "--slug",
        metavar="SLUG",
        help="Process only the MDX file whose stem matches SLUG",
    )
    args = parser.parse_args()

    dry_run = not args.apply
    if dry_run:
        print("DRY-RUN mode — no files will be modified. Pass --apply to write changes.\n")

    valid_slugs = get_all_valid_slugs()
    print(f"Loaded {len(valid_slugs)} valid algorithm slugs.\n")

    mdx_files: list[Path] = sorted(CONTENT_DIR.rglob("*.mdx"))
    if args.slug:
        mdx_files = [f for f in mdx_files if f.stem == args.slug]
        if not mdx_files:
            print(f"ERROR: No MDX file found with slug {args.slug!r}")
            sys.exit(1)

    total_kept = total_fixed = total_removed = total_changed_files = 0

    for mdx_path in mdx_files:
        kept, fixed, removed = fix_file(mdx_path, valid_slugs, dry_run)
        total_kept += kept
        total_fixed += fixed
        total_removed += removed
        if fixed > 0 or removed > 0:
            total_changed_files += 1

    print()
    print("=" * 60)
    print(f"Files with changes : {total_changed_files}")
    print(f"Slugs kept         : {total_kept}")
    print(f"Slugs fixed (typo) : {total_fixed}")
    print(f"Slugs removed      : {total_removed}")
    if dry_run:
        print("\nRe-run with --apply to write these changes.")
    else:
        print("\nChanges applied to disk.")


if __name__ == "__main__":
    main()
