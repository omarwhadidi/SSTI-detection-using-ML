"""
ssti_features.py
------------------------------------------------------------------
Feature-engineering module for SSTI (Server-Side Template Injection)
detection. Turns a raw injectable string into a fixed vector of
numeric, hand-crafted features for CLASSICAL ML baselines
(Logistic Regression, Random Forest, XGBoost).

Design notes:
  - This is for the TABULAR / classical-baseline track only.
    Your CNN / RNN models consume the RAW strings, not these features.
    Same labels, two views of the data (see build plan).
  - Every feature below is here because it reflects something about
    how SSTI actually looks, not because it happened to help accuracy.
    The comments explain the *why* so the feature set is defensible
    in the paper.
  - No fitting/state here: these are deterministic per-string features,
    so there is NO train/test leakage risk from this file. (Leakage
    risk lives in any vectorizer/scaler you add later -> fit on train
    only.)
------------------------------------------------------------------
"""

import re
import math
from collections import Counter

import pandas as pd


# ==================================================================
# 1. Domain keyword lists
#    These encode expert knowledge about SSTI. Grouped by *why* they
#    matter so you can cite the reasoning, not just dump a wordlist.
# ==================================================================

# Python-object-traversal sinks: the backbone of Jinja2/Python SSTI
# escalation (sandbox escape via the object graph).
PY_SANDBOX_SINKS = [
    "__class__", "__mro__", "__base__", "__bases__", "__subclasses__",
    "__globals__", "__builtins__", "__init__", "__import__", "__dict__",
]

# Flask/Jinja2 context objects an attacker probes for.
JINJA_CONTEXT = [
    "config", "self", "request", "cycler", "joiner", "namespace",
    "lipsum", "url_for", "get_flashed_messages",
]

# Command / code execution callables that indicate the payload is
# reaching for RCE, regardless of engine.
EXEC_SINKS = [
    "popen", "system", "subprocess", "os.", "eval", "exec",
    "commands", "Runtime", "getRuntime", "ProcessBuilder",  # Java/Freemarker
    "freemarker", "execute",
]

# Non-Python engine markers (Twig, Ruby/ERB, FreeMarker, Velocity, etc.)
# Presence signals template syntax even when the Python dunders are absent.
ENGINE_KEYWORDS = [
    "_self", "registerUndefinedFilterCallback",  # Twig
    "getClass", "forName",                        # Java reflection
    "new Executable", "assign",                   # FreeMarker
    "class.inspect", "instance_eval",             # Ruby/ERB
]

# All template DELIMITER pairs across the engines you're covering.
# Each entry: (open, close). Counting these is the single strongest
# structural signal that a string is template-shaped at all.
DELIMITERS = [
    ("{{", "}}"),   # Jinja2, Twig, Handlebars, Angular
    ("{%", "%}"),   # Jinja2 / Twig statements
    ("${", "}"),    # FreeMarker, JSP EL, Velocity, JS template literals
    ("#{", "}"),    # Ruby interpolation, Thymeleaf
    ("<%", "%>"),   # ERB, JSP scriptlet
    ("{#", "#}"),   # Jinja2 comments
    ("@{", "}"),    # Razor-ish
]

# Characters that dominate injection payloads but are rare in benign
# natural-language input. Used for a ratio feature.
SPECIAL_CHARS = set("{}[]()<>$#%|&;=*/\\'\"`._")


# ==================================================================
# 2. Small stateless helpers
# ==================================================================

def shannon_entropy(s: str) -> float:
    """
    Shannon entropy of the character distribution.
    Why: obfuscated / encoded payloads and dense special-char strings
    tend to have different entropy than plain prose. It's a cheap,
    engine-agnostic 'weirdness' signal.
    """
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _count_substr(s: str, sub: str) -> int:
    """Non-overlapping occurrences of `sub` in `s`."""
    return s.count(sub)


def _ratio(numerator: int, denominator: int) -> float:
    """Safe division that returns 0.0 instead of raising on empty input."""
    return numerator / denominator if denominator else 0.0


# ==================================================================
# 3. The core feature extractor
#    One string in -> one flat dict of numeric features out.
# ==================================================================

def extract_features(text: str) -> dict:
    """
    Extract all hand-crafted SSTI features from a single raw string.

    Returns a flat dict {feature_name: value}. Keeping it a dict (not a
    bare list) means column names travel with the values, so your
    feature-importance plots stay readable.
    """
    if not isinstance(text, str):
        text = "" if text is None else str(text)

    length = len(text)
    lowered = text.lower()
    features = {}

    # ---- 3a. Length & basic composition -------------------------
    # Attacks are often either very short probes ({{7*7}}) or long
    # escalation chains; length alone is weak but cheap.
    features["len"] = length
    features["num_digits"] = sum(ch.isdigit() for ch in text)
    features["num_letters"] = sum(ch.isalpha() for ch in text)
    features["num_special"] = sum(ch in SPECIAL_CHARS for ch in text)
    features["special_ratio"] = _ratio(features["num_special"], length)
    features["digit_ratio"] = _ratio(features["num_digits"], length)
    features["entropy"] = shannon_entropy(text)

    # ---- 3b. Delimiter structure --------------------------------
    # THE key structural block. Count each delimiter pair and how many
    # DISTINCT engines' delimiters appear (polyglot payloads light up
    # several at once).
    #
    # IMPORTANT: several engines share the SAME closing brace `}`
    # ({{...}}, ${...}, #{...}, @{...} all close with `}`). If we count
    # opens and closes independently, a single `}` gets credited to
    # every delimiter type and the feature becomes meaningless. So we
    # key each pair on its DISTINCTIVE OPENING token only, which is
    # unique per engine ("${" only ever matches ${, never {{ or #{).
    distinct_delims = 0
    for open_d, close_d in DELIMITERS:
        # sanitize name for a column: {{ -> delim_{{_}}
        key = f"delim_{open_d}_{close_d}"
        cnt = _count_substr(text, open_d)   # opening token only -> unambiguous
        features[key] = cnt
        if cnt > 0:
            distinct_delims += 1
    features["distinct_delimiter_types"] = distinct_delims

    # Total closing-brace pressure kept as its OWN feature (unbalanced
    # braces can itself be a signal) instead of being smeared across the
    # per-engine counts above.
    features["num_close_brace"] = text.count("}")

    # ---- 3c. Arithmetic-in-braces probe -------------------------
    # The classic detection payload: a math expression inside template
    # delimiters, e.g. {{7*7}}, ${7*7}, <%= 7*7 %>. Very high-signal.
    # Regex: an opening delimiter, then digits, an operator, digits,
    # before a closing delimiter.
    arith_pattern = re.compile(
        r"(\{\{|\$\{|\{%|#\{|<%=?)\s*\d+\s*[\*\+\-/]\s*\d+"
    )
    features["has_arithmetic_probe"] = int(bool(arith_pattern.search(text)))

    # ---- 3d. Attribute / dunder traversal -----------------------
    # Python SSTI escalation chains dot-walk the object graph and hammer
    # dunders: config.__class__.__mro__[1].__subclasses__() ...
    features["num_dots"] = text.count(".")
    features["num_double_underscore"] = text.count("__")

    # ---- 3e. Keyword-group hit counts ---------------------------
    # Count hits per *group* (not per word) to keep dimensionality low
    # and the signal interpretable.
    features["py_sandbox_sink_hits"] = sum(k in text for k in PY_SANDBOX_SINKS)
    features["jinja_context_hits"] = sum(k in lowered for k in JINJA_CONTEXT)
    features["exec_sink_hits"] = sum(k in lowered for k in EXEC_SINKS)
    features["engine_keyword_hits"] = sum(k in lowered for k in ENGINE_KEYWORDS)

    # ---- 3f. Encoding / evasion hints ---------------------------
    # WAF-evasion tricks: URL-encoding (%xx), HTML entities, backslash
    # escapes, concatenation. Presence hints at an obfuscated payload.
    features["num_percent"] = text.count("%")
    features["num_url_encoded"] = len(re.findall(r"%[0-9a-fA-F]{2}", text))
    features["num_html_entity"] = len(re.findall(r"&#?\w+;", text))
    features["num_backslash"] = text.count("\\")
    features["num_pipe"] = text.count("|")   # Jinja2 filter operator

    return features


# ==================================================================
# 4. DataFrame wrapper
#    Vectorize the whole corpus in one call.
# ==================================================================

def build_feature_dataframe(
    df: pd.DataFrame,
    text_col: str = "raw_text",
    label_col: str = "label",
) -> pd.DataFrame:
    """
    Apply extract_features across a DataFrame of raw samples.

    Parameters
    ----------
    df        : DataFrame containing at least `text_col` (and optionally
                `label_col`).
    text_col  : name of the column holding the raw injectable string.
    label_col : name of the label column to carry through, if present.

    Returns
    -------
    A new DataFrame: one row per input, one column per feature, with
    the label appended last (if it existed in the input). Ready to hand
    straight to train_test_split.
    """
    # Build the feature matrix. .apply returns a Series of dicts;
    # json-normalizing via DataFrame() expands them into columns.
    feat_rows = df[text_col].apply(extract_features).tolist()
    feat_df = pd.DataFrame(feat_rows, index=df.index)

    # Carry the label through untouched so X and y stay row-aligned.
    if label_col in df.columns:
        feat_df[label_col] = df[label_col].values

    return feat_df


# ==================================================================
# 5. Quick self-test  (run `python ssti_features.py` to sanity-check)
# ==================================================================

if __name__ == "__main__":
    # A tiny mixed batch: two attacks, two benign hard-negatives.
    samples = pd.DataFrame({
        "raw_text": [
            "{{7*7}}",                                              # Jinja2 probe
            "{{config.__class__.__init__.__globals__['os'].popen('id').read()}}",  # RCE chain
            "{{ user.name }}",                                     # benign template var (HARD negative)
            "The total is ${price} for 2 items",                   # benign ${} usage (HARD negative)
        ],
        "label": [1, 1, 0, 0],
    })

    out = build_feature_dataframe(samples)
    pd.set_option("display.max_columns", None, "display.width", 160)
    print(out.T)  # transpose so features are rows -> easy to eyeball
