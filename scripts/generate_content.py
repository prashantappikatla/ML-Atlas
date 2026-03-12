#!/usr/bin/env python3
"""
ML Atlas — Content Generation Orchestrator
===========================================
Autonomous pipeline that calls the Gemini API to generate MDX documentation
files for every ML algorithm in the master CSV. Runs unattended to completion,
resumes safely if interrupted, and logs everything.

SETUP
-----
1. Install dependencies (Python 3.10+):
       pip install -r scripts/requirements.txt

   Or with uv:
       uv add google-generativeai tqdm python-dotenv

2. Add your Gemini API key to .env (project root):
       GEMINI_API_KEY=your_key_here

USAGE (run from project root: ML-Atlas/)
-----
  # Dry run — preview queue, write nothing
  python scripts/generate_content.py --dry-run

  # Test on 3 algorithms before committing to a full run
  python scripts/generate_content.py --limit 3

  # Full run — all 'planned' algorithms
  python scripts/generate_content.py

  # Single algorithm
  python scripts/generate_content.py --algorithm "Random Forest Classifier"

  # All algorithms in one category
  python scripts/generate_content.py --category supervised

  # Force regenerate even if MDX already exists
  python scripts/generate_content.py --force

  # Print a status report from the log without running
  python scripts/generate_content.py --report

  # After a full run, check todo-links.md and resolve completed items
  python scripts/generate_content.py --resolve-todos

  # Re-queue only algorithms that failed (skeleton status) from last run
  python scripts/generate_content.py --retry-failed
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import signal
import sys
import time
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from textwrap import dedent

# ── Dependency check ──────────────────────────────────────────────────────────
# Give a clear error message if dependencies aren't installed yet.

def _check_deps():
    missing = []
    try:
        import google.generativeai  # noqa: F401
    except ImportError:
        missing.append("google-generativeai")
    try:
        from tqdm import tqdm  # noqa: F401
    except ImportError:
        missing.append("tqdm")
    try:
        from dotenv import load_dotenv  # noqa: F401
    except ImportError:
        missing.append("python-dotenv")
    if missing:
        print("Missing dependencies. Run:")
        print(f"  pip install -r scripts/requirements.txt")
        print("Or with uv:")
        print(f"  uv add {' '.join(missing)}")
        sys.exit(1)

_check_deps()

import google.generativeai as genai
from dotenv import load_dotenv
from tqdm import tqdm

# ── Config ────────────────────────────────────────────────────────────────────

CSV_PATH        = Path("Documentation/ml_algorithm_atlas_expanded.csv")
CONTENT_ROOT    = Path("content/algorithms")
TODO_PATH       = Path("Documentation/todo-links.md")
LOG_PATH        = Path("Documentation/generation-log.jsonl")

GEMINI_MODEL       = "gemini-2.5-flash"
RATE_LIMIT_DELAY   = 4      # seconds between API calls
MAX_RETRIES        = 4      # max retry attempts per algorithm
BACKOFF_BASE       = 2.0    # exponential backoff base (seconds)

CATEGORY_SLUG_MAP = {
    "Supervised Learning":        "supervised",
    "Unsupervised Learning":      "unsupervised",
    "Probabilistic & Bayesian":   "probabilistic",
    "Time Series & Forecasting":  "time-series",
    "Deep Learning":              "deep-learning",
    "Generative Models":          "generative",
    "Graph Machine Learning":     "graph",
    "Reinforcement Learning":     "reinforcement",
    "Meta-Learning & AutoML":     "meta-learning",
    "Evolutionary & Fuzzy Methods": "evolutionary",
}

# Curated sklearn module map for common algorithm slugs.
# Anything not listed falls back to generic inference.
SKLEARN_MODULE_MAP: dict[str, tuple[str, str]] = {
    # (module_path, ClassName)
    "random-forest-classifier":         ("ensemble", "RandomForestClassifier"),
    "random-forest-regression":         ("ensemble", "RandomForestRegressor"),
    "gradient-boosting-classifier":     ("ensemble", "GradientBoostingClassifier"),
    "gradient-boosting-regression":     ("ensemble", "GradientBoostingRegressor"),
    "extra-trees-classifier":           ("ensemble", "ExtraTreesClassifier"),
    "extra-trees-regressor":            ("ensemble", "ExtraTreesRegressor"),
    "adaboost-classifier":              ("ensemble", "AdaBoostClassifier"),
    "bagging-classifier":               ("ensemble", "BaggingClassifier"),
    "voting-classifier":                ("ensemble", "VotingClassifier"),
    "stacking-classifier":              ("ensemble", "StackingClassifier"),
    "decision-tree-classifier":         ("tree", "DecisionTreeClassifier"),
    "decision-tree-regressor":          ("tree", "DecisionTreeRegressor"),
    "logistic-regression":              ("linear_model", "LogisticRegression"),
    "linear-regression":                ("linear_model", "LinearRegression"),
    "ridge-regression":                 ("linear_model", "Ridge"),
    "lasso-regression":                 ("linear_model", "Lasso"),
    "elastic-net":                      ("linear_model", "ElasticNet"),
    "sgd-classifier":                   ("linear_model", "SGDClassifier"),
    "support-vector-machine":           ("svm", "SVC"),
    "support-vector-classifier":        ("svm", "SVC"),
    "support-vector-regression":        ("svm", "SVR"),
    "linear-svm":                       ("svm", "LinearSVC"),
    "k-nearest-neighbors":              ("neighbors", "KNeighborsClassifier"),
    "knn-classifier":                   ("neighbors", "KNeighborsClassifier"),
    "knn-regressor":                    ("neighbors", "KNeighborsRegressor"),
    "k-means-clustering":               ("cluster", "KMeans"),
    "dbscan":                           ("cluster", "DBSCAN"),
    "hierarchical-clustering":          ("cluster", "AgglomerativeClustering"),
    "gaussian-mixture-model":           ("mixture", "GaussianMixture"),
    "naive-bayes":                      ("naive_bayes", "GaussianNB"),
    "gaussian-naive-bayes":             ("naive_bayes", "GaussianNB"),
    "multinomial-naive-bayes":          ("naive_bayes", "MultinomialNB"),
    "principal-component-analysis":     ("decomposition", "PCA"),
    "pca":                              ("decomposition", "PCA"),
    "t-sne":                            ("manifold", "TSNE"),
    "umap":                             ("manifold", "TSNE"),  # note: umap-learn, not sklearn
    "isolation-forest":                 ("ensemble", "IsolationForest"),
    "one-class-svm":                    ("svm", "OneClassSVM"),
    "linear-discriminant-analysis":     ("discriminant_analysis", "LinearDiscriminantAnalysis"),
    "quadratic-discriminant-analysis":  ("discriminant_analysis", "QuadraticDiscriminantAnalysis"),
    "gaussian-process-classifier":      ("gaussian_process", "GaussianProcessClassifier"),
    "gaussian-process-regressor":       ("gaussian_process", "GaussianProcessRegressor"),
    "bayesian-ridge":                   ("linear_model", "BayesianRidge"),
    "mlp-classifier":                   ("neural_network", "MLPClassifier"),
    "mlp-regressor":                    ("neural_network", "MLPRegressor"),
    "mini-batch-k-means":               ("cluster", "MiniBatchKMeans"),
    "spectral-clustering":              ("cluster", "SpectralClustering"),
    "mean-shift":                       ("cluster", "MeanShift"),
    "birch":                            ("cluster", "Birch"),
    "optics":                           ("cluster", "OPTICS"),
    "truncated-svd":                    ("decomposition", "TruncatedSVD"),
    "non-negative-matrix-factorization":("decomposition", "NMF"),
    "independent-component-analysis":   ("decomposition", "FastICA"),
    "factor-analysis":                  ("decomposition", "FactorAnalysis"),
    "kernel-pca":                       ("decomposition", "KernelPCA"),
    "random-sample-consensus":          ("linear_model", "RANSACRegressor"),
}

REQUIRED_KEYS = {
    "overview", "history", "math_intuition", "use_cases",
    "algorithm_steps", "compatibility", "strengths", "weaknesses",
    "parameters", "tags", "related_names",
}

COMPATIBILITY_KEYS = {"tabular", "image", "text", "timeseries", "graph"}

# ── Graceful shutdown ─────────────────────────────────────────────────────────

_shutdown_requested = False

def _handle_sigint(sig, frame):
    global _shutdown_requested
    if not _shutdown_requested:
        print("\n\n⚠️  Interrupt received — finishing current algorithm then stopping.")
        print("   Press Ctrl+C again to force quit immediately.\n")
        _shutdown_requested = True
    else:
        print("\n🛑 Force quit.")
        sys.exit(1)

signal.signal(signal.SIGINT, _handle_sigint)

# ── Utilities ─────────────────────────────────────────────────────────────────

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def map_category(csv_category: str) -> str:
    return CATEGORY_SLUG_MAP.get(csv_category.strip(), slugify(csv_category))


def bool_yaml(v) -> str:
    """Convert truthy value to YAML boolean string."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return "true" if v.lower() in ("true", "1", "yes") else "false"
    return "true" if v else "false"


def bool_jsx(v) -> str:
    """Convert truthy value to JSX boolean string."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return "true" if v.lower() in ("true", "1", "yes") else "false"
    return "true" if v else "false"


def _parse_complexity(v: str) -> str:
    """Normalize CSV complexity values (Low/Med/High) to lowercase."""
    v = v.strip().lower()
    if v in ("low", "l"):
        return "low"
    if v in ("high", "h"):
        return "high"
    return "medium"


def infer_sklearn(slug: str, category: str, name: str) -> tuple[str, str] | None:
    """
    Returns (module_path, ClassName) for a scikit-learn import, or None if
    this algorithm doesn't have a sklearn equivalent.
    """
    if slug in SKLEARN_MODULE_MAP:
        return SKLEARN_MODULE_MAP[slug]

    # Algorithms outside sklearn scope
    non_sklearn = {
        "deep-learning", "generative", "reinforcement", "graph",
        "xgboost", "lightgbm", "catboost", "prophet", "arima",
    }
    if any(kw in slug for kw in non_sklearn):
        return None
    if category in ("deep-learning", "generative", "reinforcement", "graph"):
        return None

    # Fallback: try to construct a plausible class name
    class_name = "".join(w.capitalize() for w in slug.split("-"))
    module = {
        "supervised": "linear_model",
        "unsupervised": "cluster",
        "probabilistic": "naive_bayes",
        "time-series": None,
        "meta-learning": None,
        "evolutionary": None,
    }.get(category)

    if module:
        return (module, class_name)
    return None


# ── CSV ───────────────────────────────────────────────────────────────────────

def normalize_row(raw: dict) -> dict:
    """
    Map actual CSV column names to the internal keys the script uses.

    Actual CSV columns:
      Algorithm, Category, Subcategory, Year Introduced,
      Original Paper / Author, Complexity (Low/Med/High), Best Use Case,
      Implementation Done (Y/N), Lab Created (Y/N), Notes, Blog URL
    """
    return {
        "name":            raw.get("Algorithm", "").strip(),
        "category":        raw.get("Category", "").strip(),
        "subcategory":     raw.get("Subcategory", "").strip(),
        "year":            raw.get("Year Introduced", "").strip(),
        "author":          raw.get("Original Paper / Author", "").strip(),
        "paper_reference": raw.get("Original Paper / Author", "").strip(),
        "complexity":      _parse_complexity(raw.get("Complexity (Low/Med/High)", "medium")),
        "best_use_case":   raw.get("Best Use Case", "").strip(),
        "tags":            "",       # not in CSV; Gemini supplies tags
        "status":          "planned", # not in CSV; all seeded as planned
    }


def load_csv() -> list[dict]:
    if not CSV_PATH.exists():
        print(f"ERROR: CSV not found at {CSV_PATH}")
        print("Run this script from the ML Atlas project root (ML-Atlas/).")
        sys.exit(1)
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return [normalize_row(r) for r in csv.DictReader(f)]


def build_slug_index(rows: list[dict]) -> dict[str, dict]:
    """Lowercase-keyed index for O(1) algorithm name lookups."""
    index = {}
    for row in rows:
        name = row["name"].strip()
        if not name:
            continue
        index[name.lower()] = {
            "slug":        slugify(name),
            "category":    map_category(row.get("category", "")),
            "subcategory": row.get("subcategory", "").lower().replace(" ", "-"),
            "name":        name,
        }
    return index


def names_by_length_desc(slug_index: dict) -> list[str]:
    """Longest names first — prevents substring matches clobbering full names."""
    return sorted(slug_index.keys(), key=len, reverse=True)


# ── Gemini ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = dedent("""\
    You are a technical writer and machine learning expert creating documentation
    for ML Atlas, a public reference platform covering 278 ML algorithms.

    Your task is to generate structured content for a single algorithm. You will
    return a single JSON object and nothing else — no preamble, no explanation,
    no markdown code fences.

    STRICT RULES:
    1.  Return only valid JSON. No text before or after the JSON object.
    2.  All LaTeX math must use KaTeX syntax.
        - Inline math: $...$ (single dollar signs)
        - Block/display math: $$...$$ (double dollar signs, on its own line)
        - Do NOT use \\[...\\], \\(...\\), or backtick math.
    3.  All JSON string values must be plain text or KaTeX math only.
        No Markdown inside strings (no **bold**, no # headers, no bullet dashes).
    4.  history entries must be sorted by year ascending.
    5.  related_names must be exact proper algorithm names (e.g. "Decision Tree
        Classifier"). No descriptions, no vague phrases.
    6.  parameters must use scikit-learn API names where applicable
        (e.g. n_estimators, not num_trees).
    7.  math_intuition section titles must be 3-6 words.
    8.  Language: academic, precise. Audience: intermediate ML practitioners who
        understand calculus and linear algebra.
    9.  overview: 2-4 sentences. Do not start with "The [name] is/was...".
        Open with what problem it solves or what makes it distinctive.
    10. Do not hallucinate paper references. Only cite real, verifiable papers.
    11. algorithm_steps: plain numbered steps, no sub-bullets.
        Use $...$ for inline math within steps.
    12. strengths/weaknesses: each entry is one complete sentence, no leading dashes.
    13. compatibility: true only if this algorithm natively handles that data type
        without major transformation. When uncertain, default to false.
""")


def build_user_prompt(row: dict) -> str:
    name        = row["name"].strip()
    category    = map_category(row.get("category", ""))
    subcategory = row.get("subcategory", "")
    year        = row.get("year", "unknown")
    author      = row.get("author", "unknown")
    paper       = row.get("paper_reference", "")
    complexity  = row.get("complexity", "medium")

    return dedent(f"""\
        Generate complete documentation content for the ML algorithm: {name}

        Context from the ML Atlas registry:
        - Category: {category}
        - Subcategory: {subcategory}
        - Year introduced: {year}
        - Original author(s): {author}
        - Seminal paper: {paper}
        - Complexity rating: {complexity}

        Return a JSON object with exactly these keys:

        {{
          "overview": "2-4 sentence description of what the algorithm does and what makes it distinctive.",

          "history": [
            {{"year": <integer>, "event": "what happened, who did it, why it mattered"}}
          ],

          "math_intuition": [
            {{
              "title": "short section title (3-6 words)",
              "content": "explanation with $...$ inline and $$...$$ block math",
              "latex_expressions": ["standalone LaTeX expression strings"]
            }}
          ],

          "algorithm_steps": [
            "One complete step as a plain sentence. Use $...$ for inline math."
          ],

          "compatibility": {{
            "tabular": <boolean>,
            "image": <boolean>,
            "text": <boolean>,
            "timeseries": <boolean>,
            "graph": <boolean>
          }},

          "strengths": ["One concrete strength per entry (complete sentence)."],
          "weaknesses": ["One concrete weakness per entry (complete sentence)."],

          "use_cases": [
            {{"domain": "Industry or field", "description": "1-2 sentences on how it is applied."}}
          ],

          "parameters": [
            {{
              "name": "exact_param_name",
              "type": "Python type",
              "default": "default value as string",
              "description": "what this parameter controls",
              "range": "valid range or options, or empty string"
            }}
          ],

          "tags": ["lowercase-hyphenated-tag"],
          "related_names": ["Exact Proper Algorithm Name"]
        }}

        Requirements:
        - history:           3-6 milestone entries, sorted ascending by year
        - math_intuition:    2-4 sections covering core mathematical ideas
        - algorithm_steps:   4-8 steps covering the full training procedure in order
        - compatibility:     true only if natively supported without major preprocessing
        - strengths:         4-6 concrete, specific claims (not generic praise)
        - weaknesses:        3-5 concrete, specific limitations
        - use_cases:         4-6 domains with real-world applications
        - parameters:        all major hyperparameters (typically 5-10 for sklearn)
        - tags:              4-8 lowercase hyphenated tags (e.g. "ensemble", "decision-trees")
        - related_names:     4-8 exact algorithm names that are mathematically or practically related
    """)


def validate_response(data: dict) -> list[str]:
    """Returns a list of error strings. Empty list = response is valid."""
    errors: list[str] = []

    missing = REQUIRED_KEYS - set(data.keys())
    if missing:
        errors.append(f"Missing top-level keys: {sorted(missing)}")

    if not isinstance(data.get("history"), list) or len(data["history"]) == 0:
        errors.append("history must be a non-empty list")

    if not isinstance(data.get("math_intuition"), list) or len(data["math_intuition"]) < 2:
        errors.append("math_intuition must have at least 2 sections")

    if not isinstance(data.get("algorithm_steps"), list) or len(data["algorithm_steps"]) < 3:
        errors.append("algorithm_steps must have at least 3 steps")

    compat = data.get("compatibility")
    if not isinstance(compat, dict):
        errors.append("compatibility must be a dict")
    else:
        missing_compat = COMPATIBILITY_KEYS - set(compat.keys())
        if missing_compat:
            errors.append(f"compatibility missing keys: {sorted(missing_compat)}")
        bad_types = {k: v for k, v in compat.items() if not isinstance(v, bool)}
        if bad_types:
            errors.append(f"compatibility values must be booleans, got: {bad_types}")

    if not isinstance(data.get("strengths"), list) or len(data["strengths"]) < 3:
        errors.append("strengths must have at least 3 entries")

    if not isinstance(data.get("weaknesses"), list) or len(data["weaknesses"]) < 2:
        errors.append("weaknesses must have at least 2 entries")

    if not isinstance(data.get("use_cases"), list) or len(data["use_cases"]) < 3:
        errors.append("use_cases must have at least 3 entries")

    if not isinstance(data.get("parameters"), list) or len(data["parameters"]) == 0:
        errors.append("parameters must be a non-empty list")

    return errors


def call_gemini_with_backoff(model, prompt: str, algorithm_name: str) -> dict | None:
    """
    Calls Gemini with exponential backoff and MAX_RETRIES attempts.
    Returns parsed dict on success, None on total failure.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = model.generate_content(prompt)
            raw = response.text

            # Strip accidental code fences
            clean = re.sub(r"^```(?:json)?\s*", "", raw.strip())
            clean = re.sub(r"\s*```$", "", clean.strip())
            data = json.loads(clean)

            errors = validate_response(data)
            if not errors:
                return data

            wait = BACKOFF_BASE ** attempt
            print(f"     Attempt {attempt}/{MAX_RETRIES} — validation failed: {errors}")
            if attempt < MAX_RETRIES:
                print(f"     Retrying in {wait:.0f}s...")
                time.sleep(wait)

        except json.JSONDecodeError as e:
            wait = BACKOFF_BASE ** attempt
            print(f"     Attempt {attempt}/{MAX_RETRIES} — JSON parse error: {e}")
            if attempt < MAX_RETRIES:
                print(f"     Retrying in {wait:.0f}s...")
                time.sleep(wait)

        except Exception as e:
            wait = BACKOFF_BASE ** attempt
            err_str = str(e)
            # Surface rate limit errors clearly
            if "429" in err_str or "quota" in err_str.lower():
                wait = max(wait, 30)
                print(f"     Attempt {attempt}/{MAX_RETRIES} — Rate limited. Waiting {wait:.0f}s...")
            else:
                print(f"     Attempt {attempt}/{MAX_RETRIES} — API error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(wait)

    print(f"     ❌ All {MAX_RETRIES} attempts failed for: {algorithm_name}")
    return None


# ── Link Resolution ───────────────────────────────────────────────────────────

def resolve_links(
    text: str,
    slug_index: dict,
    sorted_names: list[str],
    current_slug: str,
) -> tuple[str, list[str], list[str]]:
    """
    Replaces every known algorithm name mention in `text` with an MDX link.
    Returns (modified_text, resolved_slugs, unresolved_candidates).
    """
    resolved: list[str] = []

    for name_key in sorted_names:
        if slug_index[name_key]["slug"] == current_slug:
            continue  # never link to self
        # Skip very short names (≤4 chars) to avoid matching substrings inside words
        if len(name_key) <= 4:
            continue
        meta = slug_index[name_key]
        path = f"/algorithms/{meta['category']}/{meta['subcategory']}/{meta['slug']}"
        mdx_link = f"[{meta['name']}]({path})"
        # Use word boundaries to avoid matching inside other words
        pattern = re.compile(r"\b" + re.escape(name_key) + r"\b", re.IGNORECASE)
        if pattern.search(text):
            text = pattern.sub(mdx_link, text)
            resolved.append(meta["slug"])

    # Detect potentially unresolved TitleCase multi-word phrases (candidates)
    already_resolved_names = {
        slug_index[n]["name"].lower()
        for n in slug_index
        if slug_index[n]["slug"] in resolved
    }
    title_re = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b")
    candidates = set(title_re.findall(text))
    unresolved = [
        c for c in candidates
        if c.lower() not in slug_index and c.lower() not in already_resolved_names
    ]

    return text, list(set(resolved)), unresolved


def resolve_all_fields(
    data: dict,
    slug_index: dict,
    sorted_names: list[str],
    current_slug: str,
) -> tuple[list[str], list[str]]:
    """Apply link resolution to all prose fields. Mutates data in place."""
    all_resolved: list[str] = []
    all_unresolved: list[str] = []

    def _resolve(text: str) -> str:
        t, res, unres = resolve_links(text, slug_index, sorted_names, current_slug)
        all_resolved.extend(res)
        all_unresolved.extend(unres)
        return t

    data["overview"] = _resolve(data["overview"])

    for entry in data.get("history", []):
        entry["event"] = _resolve(entry["event"])

    for section in data.get("math_intuition", []):
        section["content"] = _resolve(section["content"])

    for case in data.get("use_cases", []):
        case["description"] = _resolve(case["description"])

    return list(set(all_resolved)), list(set(all_unresolved))


def build_related(
    resolved: list[str],
    gemini_names: list[str],
    slug_index: dict,
    limit: int = 8,
) -> list[str]:
    """Combine resolved prose links + Gemini suggestions into a deduplicated list."""
    combined: set[str] = set(resolved)
    for name in gemini_names:
        key = name.lower().strip()
        if key in slug_index:
            combined.add(slug_index[key]["slug"])
    return sorted(combined)[:limit]


# ── MDX Assembly ──────────────────────────────────────────────────────────────

def build_sklearn_snippet(slug: str, category: str, name: str, subcategory: str) -> str:
    sklearn = infer_sklearn(slug, category, name)

    if sklearn is None:
        return f"# {name} does not have a direct scikit-learn implementation.\n# See the References section for relevant libraries."

    module, class_name = sklearn
    is_classifier     = "classifier" in slug or subcategory in ("classification",)
    is_regressor      = "regressor" in slug or "regression" in slug or subcategory in ("regression",)
    is_clusterer      = category == "unsupervised" or "clustering" in subcategory
    is_transformer    = any(k in slug for k in ("pca", "svd", "ica", "nmf", "tsne"))

    if is_transformer:
        return dedent(f"""\
            from sklearn.{module} import {class_name}

            model = {class_name}()
            X_transformed = model.fit_transform(X)""")

    if is_clusterer:
        return dedent(f"""\
            from sklearn.{module} import {class_name}

            model = {class_name}()
            labels = model.fit_predict(X)""")

    if is_regressor:
        return dedent(f"""\
            from sklearn.{module} import {class_name}
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import mean_squared_error, r2_score

            X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

            model = {class_name}()
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)

            print(f"MSE: {{mean_squared_error(y_test, y_pred):.4f}}")
            print(f"R²:  {{r2_score(y_test, y_pred):.4f}}")""")

    # Default: classifier
    return dedent(f"""\
        from sklearn.{module} import {class_name}
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import classification_report

        X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

        model = {class_name}()
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        print(classification_report(y_test, y_pred))""")


def assemble_mdx(row: dict, data: dict, related: list[str]) -> str:
    name        = row["name"].strip()
    slug        = slugify(name)
    category    = map_category(row.get("category", ""))
    subcategory = row.get("subcategory", "").lower().replace(" ", "-")
    year        = row.get("year", "").strip()
    author      = row.get("author", "").strip()
    paper       = row.get("paper_reference", "").strip()
    complexity  = row.get("complexity", "medium").strip()

    # Compatibility — use Gemini's output (CSV has no compatibility columns)
    gemini_compat = data.get("compatibility", {})
    compat = {
        k: gemini_compat.get(k, k == "tabular")
        for k in ("tabular", "image", "text", "timeseries", "graph")
    }

    # Tags: merge CSV (empty) + Gemini, deduplicate, lowercase, hyphenated
    csv_tags    = [t.strip().lower().replace(" ", "-") for t in row.get("tags", "").split(",") if t.strip()]
    gemini_tags = [t.strip().lower().replace(" ", "-") for t in data.get("tags", [])]
    tags        = sorted(set(csv_tags + gemini_tags))
    tags_yaml   = "[" + ", ".join(f'"{t}"' for t in tags) + "]"

    year_val = int(year) if year.isdigit() else '""'

    related_yaml = (
        "\n".join(f'  - "{s}"' for s in related) if related else "[]"
    )

    # ── Frontmatter ───────────────────────────────────────────────────────────
    frontmatter = f"""\
---
title: "{name}"
slug: "{slug}"
category: "{category}"
subcategory: "{subcategory}"
year: {year_val}
author: "{author}"
paper: "{paper}"
complexity: "{complexity}"
status: "in-progress"
compatibility:
  tabular: {bool_yaml(compat['tabular'])}
  image: {bool_yaml(compat['image'])}
  text: {bool_yaml(compat['text'])}
  timeseries: {bool_yaml(compat['timeseries'])}
  graph: {bool_yaml(compat['graph'])}
tags: {tags_yaml}
lab_url: ""
lab_framework: ""
related:
{related_yaml}
---"""

    # ── History ───────────────────────────────────────────────────────────────
    history_lines = [
        f"**{e['year']}** — {e['event']}"
        for e in data.get("history", [])
    ]
    history_section = "\n\n".join(history_lines)

    # ── Math Intuition ────────────────────────────────────────────────────────
    math_parts = []
    for section in data.get("math_intuition", []):
        part = f"### {section['title']}\n\n{section['content']}"
        for expr in section.get("latex_expressions", []):
            if expr.strip():
                part += f"\n\n$$\n{expr.strip()}\n$$"
        math_parts.append(part)
    math_section = "\n\n".join(math_parts)

    # ── Algorithm Steps ───────────────────────────────────────────────────────
    steps = data.get("algorithm_steps", [])
    steps_section = "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))

    # ── Parameters Table ──────────────────────────────────────────────────────
    params    = data.get("parameters", [])
    has_range = any(p.get("range", "").strip() for p in params)
    if has_range:
        header = "| Parameter | Type | Default | Range / Options | Description |\n|---|---|---|---|---|"
        rows_str = "\n".join(
            f"| `{p['name']}` | `{p['type']}` | `{p['default']}` | {p.get('range', '')} | {p['description']} |"
            for p in params
        )
    else:
        header = "| Parameter | Type | Default | Description |\n|---|---|---|---|"
        rows_str = "\n".join(
            f"| `{p['name']}` | `{p['type']}` | `{p['default']}` | {p['description']} |"
            for p in params
        )
    params_table = f"{header}\n{rows_str}"

    # ── Strengths / Weaknesses ────────────────────────────────────────────────
    strengths_section  = "\n".join(f"- {s}" for s in data.get("strengths", []))
    weaknesses_section = "\n".join(f"- {w}" for w in data.get("weaknesses", []))

    # ── Use Cases ─────────────────────────────────────────────────────────────
    use_case_parts = [
        f"### {c['domain']}\n\n{c['description']}"
        for c in data.get("use_cases", [])
    ]
    use_cases_section = "\n\n".join(use_case_parts)

    # ── Implementation ────────────────────────────────────────────────────────
    sklearn_snippet = build_sklearn_snippet(slug, category, name, subcategory)

    # ── References ────────────────────────────────────────────────────────────
    ref_lines = []
    if author and year_val and paper:
        ref_lines.append(f"- {author} ({year_val}). {paper}.")
    sklearn_info = infer_sklearn(slug, category, name)
    if sklearn_info:
        module, class_name = sklearn_info
        sklearn_url = (
            f"https://scikit-learn.org/stable/modules/generated/"
            f"sklearn.{module}.{class_name}.html"
        )
        ref_lines.append(f"- [scikit-learn: {class_name}]({sklearn_url})")
    references_section = "\n".join(ref_lines) if ref_lines else "<!-- TODO: Add references -->"

    # ── Compatibility JSX ─────────────────────────────────────────────────────
    compat_jsx = (
        f"<CompatibilityMatrix\n"
        f"  tabular={{{bool_jsx(compat['tabular'])}}}\n"
        f"  image={{{bool_jsx(compat['image'])}}}\n"
        f"  text={{{bool_jsx(compat['text'])}}}\n"
        f"  timeseries={{{bool_jsx(compat['timeseries'])}}}\n"
        f"  graph={{{bool_jsx(compat['graph'])}}}\n"
        f"/>"
    )

    # ── Final Assembly ────────────────────────────────────────────────────────
    return f"""{frontmatter}

## Overview

{data['overview']}

## History

{history_section}

## Mathematical Intuition

{math_section}

## Algorithm Steps

{steps_section}

## Parameters

{params_table}

## Compatibility

{compat_jsx}

## Strengths

{strengths_section}

## Weaknesses

{weaknesses_section}

## Use Cases

{use_cases_section}

## Implementation

### From Scratch

```python
# TODO: Implement {name} from scratch
```

### Using scikit-learn

```python
{sklearn_snippet}
```

## Lab

<LabEmbed url={{""}} title="{name} Lab" />

## References

{references_section}
"""


def build_skeleton(row: dict) -> str:
    """Minimal MDX skeleton written when Gemini completely fails."""
    name        = row["name"].strip()
    slug        = slugify(name)
    category    = map_category(row.get("category", ""))
    subcategory = row.get("subcategory", "").lower().replace(" ", "-")
    year        = row.get("year", "").strip()
    year_val    = int(year) if year.isdigit() else '""'

    return f"""\
---
title: "{name}"
slug: "{slug}"
category: "{category}"
subcategory: "{subcategory}"
year: {year_val}
author: "{row.get('author', '').strip()}"
paper: "{row.get('paper_reference', '').strip()}"
complexity: "{row.get('complexity', 'medium').strip()}"
status: "in-progress"
compatibility:
  tabular: false
  image: false
  text: false
  timeseries: false
  graph: false
tags: []
lab_url: ""
lab_framework: ""
related: []
---

<!-- TODO: Gemini generation failed. All sections need manual completion. -->

## Overview

## History

## Mathematical Intuition

## Algorithm Steps

## Parameters

## Compatibility

## Strengths

## Weaknesses

## Use Cases

## Implementation

### From Scratch

```python
# TODO: Implement {name} from scratch
```

### Using scikit-learn

```python
# TODO
```

## Lab

<LabEmbed url={{""}} title="{name} Lab" />

## References
"""


# ── File I/O ──────────────────────────────────────────────────────────────────

def mdx_output_path(category: str, subcategory: str, slug: str) -> Path:
    return CONTENT_ROOT / category / subcategory / f"{slug}.mdx"


def write_file(path: Path, content: str, dry_run: bool = False):
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_todos(algorithm_name: str, unresolved: list[str]):
    if not unresolved:
        return
    TODO_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(TODO_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n### {algorithm_name} ({date.today()})\n")
        for term in sorted(set(unresolved)):
            f.write(f"- [ ] `{term}` — appears in prose but has no MDX page\n")


def append_log(entry: dict):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def read_log() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    entries = []
    with open(LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return entries


# ── Single Algorithm Pipeline ─────────────────────────────────────────────────

def process_algorithm(
    row: dict,
    model,
    slug_index: dict,
    sorted_names: list[str],
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    name        = row["name"].strip()
    slug        = slugify(name)
    category    = map_category(row.get("category", ""))
    subcategory = row.get("subcategory", "").lower().replace(" ", "-")
    out_path    = mdx_output_path(category, subcategory, slug)

    result = {
        "algorithm":       name,
        "slug":            slug,
        "path":            str(out_path),
        "status":          None,
        "resolved_links":  [],
        "unresolved_terms":[],
        "errors":          [],
        "timestamp":       datetime.utcnow().isoformat(),
    }

    # ── Skip check ────────────────────────────────────────────────────────────
    if out_path.exists() and not force:
        result["status"] = "skipped"
        return result

    # ── Gemini call ───────────────────────────────────────────────────────────
    prompt      = build_user_prompt(row)
    full_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
    gemini_data = call_gemini_with_backoff(model, full_prompt, name)

    # ── Skeleton fallback ─────────────────────────────────────────────────────
    if gemini_data is None:
        result["status"] = "skeleton"
        result["errors"].append("Gemini failed after all retries")
        write_file(out_path, build_skeleton(row), dry_run)
        append_log(result)
        return result

    # ── Link resolution ───────────────────────────────────────────────────────
    resolved, unresolved = resolve_all_fields(gemini_data, slug_index, sorted_names, slug)
    result["resolved_links"]   = resolved
    result["unresolved_terms"] = unresolved

    # ── Build related array ───────────────────────────────────────────────────
    related = build_related(resolved, gemini_data.get("related_names", []), slug_index)

    # ── Assemble and write ────────────────────────────────────────────────────
    mdx_content = assemble_mdx(row, gemini_data, related)
    write_file(out_path, mdx_content, dry_run)
    append_todos(name, unresolved)

    result["status"] = "generated"
    append_log(result)
    return result


# ── Report Mode ───────────────────────────────────────────────────────────────

def print_report():
    entries = read_log()
    if not entries:
        print("No generation log found at", LOG_PATH)
        return

    by_status: dict[str, list] = defaultdict(list)
    for e in entries:
        by_status[e.get("status", "unknown")].append(e)

    print(f"\nML Atlas — Generation Report")
    print(f"{'='*50}")
    print(f"Log entries:   {len(entries)}")
    print(f"  ✅ Generated:  {len(by_status.get('generated', []))}")
    print(f"  ⏭  Skipped:    {len(by_status.get('skipped', []))}")
    print(f"  ⚠️  Skeleton:   {len(by_status.get('skeleton', []))}")
    print()

    skeletons = by_status.get("skeleton", [])
    if skeletons:
        print(f"Algorithms needing manual attention ({len(skeletons)}):")
        for e in skeletons:
            print(f"  → {e['algorithm']}  ({e.get('path', '')})")
        print()

    all_unresolved: dict[str, int] = defaultdict(int)
    for e in by_status.get("generated", []):
        for term in e.get("unresolved_terms", []):
            all_unresolved[term] += 1

    if all_unresolved:
        top = sorted(all_unresolved.items(), key=lambda x: -x[1])[:20]
        print(f"Top unresolved terms across all runs:")
        for term, count in top:
            print(f"  {count:3d}x  {term}")
        print()
        print(f"💡 Run with --resolve-todos to update todo-links.md")


# ── Todo Resolution ───────────────────────────────────────────────────────────

def resolve_todos(slug_index: dict, dry_run: bool = False):
    if not TODO_PATH.exists():
        print("No todo-links.md found.")
        return

    content = TODO_PATH.read_text(encoding="utf-8")
    updated = content
    resolved_count = 0

    for name_lower, meta in slug_index.items():
        path = mdx_output_path(meta["category"], meta["subcategory"], meta["slug"])
        if path.exists():
            pattern = re.compile(
                r"- \[ \] `" + re.escape(meta["name"]) + r"`",
                re.IGNORECASE
            )
            new_content, n = pattern.subn(f"- [x] `{meta['name']}`", updated)
            if n > 0:
                updated = new_content
                resolved_count += n

    if resolved_count > 0:
        if not dry_run:
            TODO_PATH.write_text(updated, encoding="utf-8")
        print(f"✅ Marked {resolved_count} todo items as resolved")
    else:
        print("No new todos to resolve.")

    open_items = re.findall(r"- \[ \] `(.+?)`", updated)
    if open_items:
        print(f"\n📋 Remaining open todos ({len(open_items)}):")
        for item in open_items[:25]:
            print(f"   → {item}")
        if len(open_items) > 25:
            print(f"   ... and {len(open_items) - 25} more. See {TODO_PATH}")
    else:
        print("🎉 All todos resolved!")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="ML Atlas Content Generator — Autonomous MDX pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""\
            Examples:
              python scripts/generate_content.py --dry-run
              python scripts/generate_content.py --limit 5
              python scripts/generate_content.py --algorithm "K-Means Clustering"
              python scripts/generate_content.py --category supervised
              python scripts/generate_content.py
              python scripts/generate_content.py --report
              python scripts/generate_content.py --resolve-todos
              python scripts/generate_content.py --retry-failed
        """),
    )
    parser.add_argument("--algorithm",      type=str,  help="Generate one specific algorithm")
    parser.add_argument("--category",       type=str,  help="Generate all algorithms in a category slug")
    parser.add_argument("--status",         type=str,  default="planned",
                                                       help="Filter by status field (default: planned)")
    parser.add_argument("--limit",          type=int,  help="Cap the number of algorithms to process")
    parser.add_argument("--dry-run",        action="store_true", help="Preview queue, write nothing")
    parser.add_argument("--force",          action="store_true", help="Overwrite existing MDX files")
    parser.add_argument("--report",         action="store_true", help="Print status report from log")
    parser.add_argument("--resolve-todos",  action="store_true", help="Update todo-links.md checkboxes")
    parser.add_argument("--retry-failed",   action="store_true", help="Re-run only skeleton/failed algorithms")
    args = parser.parse_args()

    # ── Report / todo mode (no API needed) ───────────────────────────────────
    if args.report:
        print_report()
        return

    load_dotenv()
    rows         = load_csv()
    slug_index   = build_slug_index(rows)
    sorted_names = names_by_length_desc(slug_index)

    if args.resolve_todos:
        resolve_todos(slug_index, args.dry_run)
        return

    # ── API key check ─────────────────────────────────────────────────────────
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key and not args.dry_run:
        print("ERROR: GEMINI_API_KEY not set.")
        print("Add it to your .env file:  GEMINI_API_KEY=your_key_here")
        sys.exit(1)

    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
    else:
        model = None  # dry-run only

    # ── Build queue ───────────────────────────────────────────────────────────
    if args.retry_failed:
        log_entries  = read_log()
        failed_slugs = {
            slugify(e["algorithm"])
            for e in log_entries
            if e.get("status") in ("skeleton", "error")
        }
        queue = [r for r in rows if slugify(r["name"].strip()) in failed_slugs]
        print(f"Retry mode: {len(queue)} failed algorithms queued")

    elif args.algorithm:
        queue = [r for r in rows if r["name"].lower() == args.algorithm.lower()]
        if not queue:
            print(f"ERROR: '{args.algorithm}' not found in CSV. Check spelling.")
            sys.exit(1)

    elif args.category:
        queue = [r for r in rows if map_category(r.get("category", "")) == args.category]
        if not queue:
            print(f"ERROR: No algorithms found for category '{args.category}'")
            sys.exit(1)

    else:
        # Default: all algorithms not yet documented (no existing MDX file)
        queue = [
            r for r in rows
            if not mdx_output_path(
                map_category(r.get("category", "")),
                r.get("subcategory", "").lower().replace(" ", "-"),
                slugify(r["name"].strip()),
            ).exists()
        ]

    if args.limit:
        queue = queue[:args.limit]

    if not queue:
        print("Nothing to process. All algorithms already have MDX files.")
        print("Use --force to regenerate, or --retry-failed for failed runs.")
        sys.exit(0)

    # ── Header ────────────────────────────────────────────────────────────────
    print(f"\nML Atlas Content Generator")
    print(f"{'='*50}")
    print(f"Algorithms in queue : {len(queue)}")
    print(f"Mode                : {'DRY RUN — no files written' if args.dry_run else 'LIVE'}")
    print(f"Force overwrite     : {args.force}")
    print(f"Model               : {GEMINI_MODEL}")
    print()

    if args.dry_run:
        print("Queue preview:")
        for i, row in enumerate(queue, 1):
            slug = slugify(row["name"].strip())
            cat  = map_category(row.get("category", ""))
            sub  = row.get("subcategory", "").lower().replace(" ", "-")
            path = mdx_output_path(cat, sub, slug)
            exists = "EXISTS" if path.exists() else "new"
            print(f"  [{i:3d}] {row['name']:<45} {exists}")
        print()
        print("Run without --dry-run to generate.")
        return

    # ── Run ───────────────────────────────────────────────────────────────────
    stats: dict[str, int] = defaultdict(int)

    with tqdm(total=len(queue), unit="algo", ncols=80) as pbar:
        for i, row in enumerate(queue):
            if _shutdown_requested:
                pbar.write("Stopping cleanly after interrupt.")
                break

            name = row["name"].strip()
            pbar.set_description(f"{name[:35]:<35}")

            result = process_algorithm(
                row, model, slug_index, sorted_names,
                dry_run=args.dry_run, force=args.force,
            )

            status = result["status"]
            stats[status] += 1

            icons = {"generated": "✅", "skipped": "⏭ ", "skeleton": "⚠️ "}
            icon  = icons.get(status, "❓")

            if status == "skipped":
                pbar.write(f"  {icon} Skipped:   {name}")
            elif status == "generated":
                n_links = len(result["resolved_links"])
                n_todo  = len(result["unresolved_terms"])
                pbar.write(
                    f"  {icon} Generated: {name}"
                    + (f"  [{n_links} links]" if n_links else "")
                    + (f"  [{n_todo} todos]" if n_todo else "")
                )
            elif status == "skeleton":
                pbar.write(f"  {icon} Skeleton:  {name}  (Gemini failed — manual fill needed)")

            pbar.update(1)

            # Rate limit delay (skip after last item)
            if i < len(queue) - 1 and not args.dry_run and status != "skipped":
                time.sleep(RATE_LIMIT_DELAY)

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("="*50)
    print("Run complete")
    print(f"  ✅ Generated : {stats['generated']}")
    print(f"  ⏭  Skipped   : {stats['skipped']}")
    print(f"  ⚠️  Skeletons : {stats['skeleton']}")
    print()

    if TODO_PATH.exists():
        open_count = TODO_PATH.read_text().count("- [ ]")
        if open_count:
            print(f"📋 Open todos in {TODO_PATH}: {open_count}")
            print(f"   Run: python scripts/generate_content.py --resolve-todos")
            print()

    if stats["skeleton"] > 0:
        print(f"⚠️  {stats['skeleton']} algorithms need manual attention.")
        print(f"   Run: python scripts/generate_content.py --retry-failed")
        print()

    print(f"📊 Full log: {LOG_PATH}")
    print(f"   Run: python scripts/generate_content.py --report")


if __name__ == "__main__":
    main()
