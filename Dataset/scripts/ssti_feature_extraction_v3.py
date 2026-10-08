"""
ssti_feature_extraction_v3.py
=============================

Version 3 of the SSTI feature set: the 18 v2 features plus 4 new ones.
Versions 1 and 2 are imported, not copied, and are left unchanged so every
earlier result stays reproducible.

Why v3. The v2 features describe what an ATTACK looks like (delimiters,
calls, dunder chains). Most remaining false alarms are ordinary template
code with the same shape. v3 adds features that describe what NORMAL
template code does, so the model has evidence pointing the other way.

  ADDED
    v3_is_i18n_call       1 if every expression is a translation call,
                          e.g. t('Save') or _("New user?").
    v3_simple_read_ratio  Share of expressions that only read a value,
                          e.g. user.name or @order[:id] | upper.
    v3_control_ratio      Share of tags that are control statements
                          (if / for / set / end / block ...).
    v3_chained_calls      Calls made on the RESULT of another call or index,
                          e.g. a(x).b() or x[1].c(). Attacks walk an object
                          graph and call what they get back.

  RULE: no feature may learn names or words from the data. Each one is a
  fixed regex about template syntax, so it means the same thing on a
  project the model has never seen.

  WHY THE RULE. A first attempt (2026-10-08) also had a helper-name
  vocabulary learned from the training benign rows. It raised test F1 but
  only because the test benign rows come from the same four projects; on
  benign code from 13 unseen repositories it doubled false alarms. It was
  dropped, together with a literal-text ratio (an artifact of how benign
  rows were cut from their files) and a prose flag (fired on <1% of rows).

  EVIDENCE (XGBoost, 2026-10-08, AUC):
    test split (full_DS)                       v2 0.976 -> v3 0.986
    training, one benign project held out      v2 0.885 -> v3 0.916
    test attacks vs 1,372 unseen-repo benign   v2 0.888 -> v3 0.899
  Caveat: the i18n and control-statement ideas came from reading test-set
  false alarms. The held-out-project and unseen-repo checks are what
  support them, not the test split.

  KNOWN LIMIT: a cutoff learned from the training benign rows (5% false
  alarms) drops from 0.80 (v2) to 0.61 (v3) and does not transfer to new
  projects. Report AUC and results at 0.5 until the benign set is broader.

Naming rule: any column starting with `v3_` is new in v3.
Result: 22 features (v2 had 18).
"""

import re
import pandas as pd

import ssti_feature_extraction_v2 as v2


# ---------------------------------------------------------------------------
# Column order: all v2 columns first, in their v2 order, then v3 columns.
# ---------------------------------------------------------------------------
V3_COLUMNS = [
    "v3_is_i18n_call",
    "v3_simple_read_ratio",
    "v3_control_ratio",
    "v3_chained_calls",
]
FEATURE_ORDER = v2.FEATURE_ORDER + V3_COLUMNS

# 0/1 flags. These must NOT be scaled.
BINARY_FEATURES = v2.BINARY_FEATURES + ["v3_is_i18n_call"]
SCALE_FEATURES = [f for f in FEATURE_ORDER if f not in BINARY_FEATURES]


# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Whole tags: same delimiters as v2, plus FreeMarker <#...>
_TAG = re.compile(r"\{\{.*?\}\}|\$\{.*?\}|\{%.*?%\}|<%.*?%>|#\{.*?\}|<#.*?>", re.DOTALL)

# The text inside one tag
_INNER = re.compile(r"^(?:\{\{|\$\{|\{%|<%[=-]?|#\{|<#)(.*?)(?:\}\}|\}|%\}|-?%>|>)$", re.DOTALL)

# t('..'), _("..."), __('..'), gettext(..), I18n.t(..), or 'text'|trans
_I18N = re.compile(
    r"""^\s*(?:(?:I18n\.)?t|_|__|gettext|ngettext|trans|translate)\s*\(\s*['"][^'"]*['"].*\)\s*$"""
    r"""|^\s*['"][^'"]*['"]\s*\|\s*trans\b""",
    re.DOTALL,
)

# name, name.attr, @name, name[:key], plus optional plain filters (| upper)
_SIMPLE_READ = re.compile(
    r"^\s*[@$]?[A-Za-z_]\w*(?:\.[A-Za-z_]\w*|\[\s*['\":]?\w+['\"]?\s*\])*"
    r"(?:\s*\|\s*[A-Za-z_]\w*)*\s*$"
)

# A control keyword at the start of a tag
_CONTROL = re.compile(
    r"^\s*(?:if|elif|elsif|else|endif|for|endfor|each|end|unless|set|endset|block|endblock|"
    r"extends|include|import|from|macro|endmacro|with|endwith|list|/if|/list|case|when|"
    r"trans|endtrans|autoescape|endautoescape|spaceless|endspaceless)\b"
)

# ")" or "]" followed by ".name(" : calling something on what a call/index returned
_CHAINED = re.compile(r"[)\]]\s*\.\s*\w+\s*\(")


def _inners(s: str):
    """Text inside each template tag, delimiters removed."""
    out = []
    for tag in _TAG.findall(s):
        m = _INNER.match(tag)
        out.append(m.group(1) if m else tag)
    return out


def extract_v3_only(payload: str) -> dict:
    """The 4 new v3 features for one payload."""
    s = payload if isinstance(payload, str) else str(payload)
    inners = _inners(s)
    exprs = [i for i in inners if not _CONTROL.match(i)]   # tags that output a value
    return {
        "v3_is_i18n_call": int(bool(exprs) and all(_I18N.match(e) for e in exprs)),
        "v3_simple_read_ratio": (sum(bool(_SIMPLE_READ.match(e)) for e in exprs) / len(exprs)) if exprs else 0.0,
        "v3_control_ratio": (sum(bool(_CONTROL.match(i)) for i in inners) / len(inners)) if inners else 0.0,
        "v3_chained_calls": len(_CHAINED.findall(" ".join(inners))),
    }


def extract_features(payload: str) -> dict:
    """Map one payload string to its 22 v3 features, in FEATURE_ORDER."""
    feats = v2.extract_features(payload)
    feats.update(extract_v3_only(payload))
    return {k: feats[k] for k in FEATURE_ORDER}


def build_feature_matrix(payloads, labels=None) -> pd.DataFrame:
    """Same interface as v1 and v2."""
    df = pd.DataFrame([extract_features(p) for p in payloads], columns=FEATURE_ORDER)
    if labels is not None:
        df["label"] = list(labels)
    return df


def build_full_ds(src_csv, dst_csv):
    """Rebuild full_DS.csv with v3 features.

    Layout: payload, base_id, features..., label, split.
    payload, base_id, label and split are copied from the source file, so the
    rows, their order, grouping keys, labels and train/test split are
    guaranteed identical -- only the feature columns differ.
    """
    src = pd.read_csv(src_csv, keep_default_na=False)
    src = src[["payload", "base_id", "label", "split"]]     # ignore any old feature columns
    feats = build_feature_matrix(src["payload"])
    out = pd.concat(
        [src[["payload", "base_id"]].reset_index(drop=True),
         feats,
         src[["label", "split"]].reset_index(drop=True)],
        axis=1,
    )
    out.to_csv(dst_csv, index=False)
    return out


if __name__ == "__main__":
    from pathlib import Path

    # The evaluation folder is "model Evaluation" in the research folder and
    # "model_evaluation" in the repository.
    root = Path(__file__).resolve().parents[2]
    folder = root / "model Evaluation"
    if not folder.exists():
        folder = root / "model_evaluation"

    # Only payload, base_id, label and split are read from the source, so the
    # v3 file itself can be the source when full_DS.csv is not there (the
    # repository ships only full_DS_v3.csv). The result is the same file.
    src = folder / "full_DS.csv"
    if not src.exists():
        src = folder / "full_DS_v3.csv"
    out = build_full_ds(src, folder / "full_DS_v3.csv")
    print(f"full_DS_v3.csv: {len(out)} rows, {len(FEATURE_ORDER)} features, "
          f"split = {out['split'].value_counts().to_dict()}")
