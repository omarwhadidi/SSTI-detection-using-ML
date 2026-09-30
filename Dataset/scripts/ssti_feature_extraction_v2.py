"""
ssti_feature_extraction_v2.py
=============================

Version 2 of the SSTI feature set. Version 1 (ssti_feature_extraction.py) is
imported, not copied, and is left completely unchanged so that every v1 result
stays reproducible.

What changed from v1, and why. Every change comes from the feature audit of
2026-09-21 (Dataset/scripts/feature_audit.py), which scored each feature
separately against hard negatives and against normal parameters.

  REMOVED
    count_percent_brace      Fired on 2 of 3,906 rows. AUC 0.500, and dropping
                             it changed nothing (leave-one-out delta 0.0000).

  REPLACED (renamed, because the definition changed)
    count_erb             -> v2_count_erb_open
        v1 counted opening AND closing tags, so an ERB expression scored 2
        while the equivalent Jinja expression scored 1 on count_double_brace.
        v2 counts opening tags only, matching how the other delimiter counts
        work. v1's standalone external AUC was 0.466, below chance.

    has_arithmetic_operation -> v2_has_arithmetic_probe
        v1 required a bare number on both sides of the operator, so it missed
        the common probe form where one operand is a quoted number. It fired
        on only 1.7% of attacks. v2 also accepts a quoted numeric operand.
        The delimiter-interior scoping from v1 is kept.

  ADDED
    v2_call_inside_delim     Method calls that occur INSIDE a template
                             delimiter, where they would actually execute.
                             AUC 0.702 against hard negatives, and nearly the
                             same against normal parameters (gap 0.023), which
                             means it measures behaviour, not "has a delimiter".

    v2_max_attr_chain_len    Longest attribute/index walk (a.b[0].c = 3).
                             Captures object-graph traversal depth, which
                             count_dots could not separate from dots in emails,
                             URLs and version numbers. AUC 0.659 vs hard negatives.

Naming rule: any column starting with `v2_` is new or has a changed definition.
A column without the prefix is computed exactly as in v1.

Result: 18 features (v1 had 17).
"""

import re
import pandas as pd

from ssti_feature_extraction import extract_features as extract_v1_features


# ---------------------------------------------------------------------------
# Column order. Unchanged v1 features first, in their v1 order, then v2 columns.
# ---------------------------------------------------------------------------
V1_KEPT = [
    "payload_length",
    "special_char_ratio",
    "count_double_brace",
    "count_dollar_brace",
    "count_hash_brace",
    "delimiter_family_count",
    "max_bracket_depth",
    "has_dunder_chain",
    "has_exec_tokens",
    "has_java_reflection",
    "has_flask_objects",
    "has_string_operation",
    "count_method_calls",
    "count_dots",
]
V2_COLUMNS = [
    "v2_count_erb_open",
    "v2_has_arithmetic_probe",
    "v2_call_inside_delim",
    "v2_max_attr_chain_len",
]
FEATURE_ORDER = V1_KEPT + V2_COLUMNS

# 0/1 flags. These must NOT be scaled. Everything else is a count, length or
# ratio and may be scaled (fit on the training fold only).
BINARY_FEATURES = [
    "has_dunder_chain",
    "has_exec_tokens",
    "has_java_reflection",
    "has_flask_objects",
    "has_string_operation",
    "v2_has_arithmetic_probe",
]
SCALE_FEATURES = [f for f in FEATURE_ORDER if f not in BINARY_FEATURES]


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Same delimiter-interior pattern v1 uses for its arithmetic feature.
_DELIM_INTERIOR = re.compile(
    r"\{\{(.*?)\}\}|\$\{(.*?)\}|\{%(.*?)%\}|<%(.*?)%>|#\{(.*?)\}", re.DOTALL
)

# Opening tags only. v1 also counted the closing tag.
_ERB_OPEN = re.compile(r"<%|<#|<@")

# A numeric operand, optionally wrapped in quotes, on each side of an operator.
_NUM = r"['\"]?\d+['\"]?"
_ARITH_PROBE = re.compile(_NUM + r"\s*[*+\-/]\s*" + _NUM)

# `.name(` -- same method-call pattern v1 uses for count_method_calls.
_METHOD_CALL = re.compile(r"\.\w+\s*\(")

# An identifier followed by one or more `.attr` or `[index]` steps.
_ATTR_CHAIN = re.compile(r"[A-Za-z_]\w*(?:\s*(?:\.\s*\w+|\[[^\]]*\]))+")


def _interiors(s: str):
    """Text inside template delimiters only."""
    return [g for groups in _DELIM_INTERIOR.findall(s) for g in groups if g]


def _has_arithmetic_probe(s: str) -> int:
    """Same scoping rule as v1: judge arithmetic inside delimiters when any
    exist, otherwise fall back to the whole string."""
    inside = _interiors(s)
    if inside:
        return 1 if any(_ARITH_PROBE.search(i) for i in inside) else 0
    return 1 if _ARITH_PROBE.search(s) else 0


def _max_attr_chain_len(s: str) -> int:
    """Number of `.attr` / `[index]` steps in the longest chain."""
    return max(
        [m.group(0).count(".") + m.group(0).count("[") for m in _ATTR_CHAIN.finditer(s)]
        + [0]
    )


def extract_features(payload: str) -> dict:
    """Map one payload string to its 18 v2 features, in FEATURE_ORDER."""
    s = payload if isinstance(payload, str) else str(payload)
    v1 = extract_v1_features(s)

    feats = {name: v1[name] for name in V1_KEPT}
    feats["v2_count_erb_open"] = len(_ERB_OPEN.findall(s))
    feats["v2_has_arithmetic_probe"] = _has_arithmetic_probe(s)
    feats["v2_call_inside_delim"] = len(_METHOD_CALL.findall(" ".join(_interiors(s))))
    feats["v2_max_attr_chain_len"] = _max_attr_chain_len(s)
    return {k: feats[k] for k in FEATURE_ORDER}


def build_feature_matrix(payloads, labels=None) -> pd.DataFrame:
    """Same interface as v1."""
    df = pd.DataFrame([extract_features(p) for p in payloads], columns=FEATURE_ORDER)
    if labels is not None:
        df["label"] = list(labels)
    return df


def build_feature_file(src_csv, dst_csv):
    """Rebuild a *_features.csv as v2.

    Keeps the v1 file's layout: payload, base_id, features..., label (last).
    Reads payload, base_id and label from the v1 file so rows, order, grouping
    keys and labels are guaranteed identical -- only the feature columns differ.
    """
    src = pd.read_csv(src_csv, keep_default_na=False)
    feats = build_feature_matrix(src["payload"])
    out = pd.concat(
        [src[["payload", "base_id"]].reset_index(drop=True),
         feats,
         src[["label"]].reset_index(drop=True)],
        axis=1,
    )
    out.to_csv(dst_csv, index=False)
    return out


if __name__ == "__main__":
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]      # .../Dataset
    pairs = [
        (root / "train/combined/train_features.csv",
         root / "train/combined/train_features_v2.csv"),
        (root / "test_set/features/test_features.csv",
         root / "test_set/features/test_features_v2.csv"),
    ]
    for src, dst in pairs:
        out = build_feature_file(src, dst)
        print(f"{dst.name}: {len(out)} rows, {len(FEATURE_ORDER)} features")
