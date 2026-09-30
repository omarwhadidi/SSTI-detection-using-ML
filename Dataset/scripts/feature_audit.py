"""
feature_audit.py -- evidence for the feature-engineering review (2026-09-21)
===========================================================================

Rerun this to reproduce every number in the feature review. Nothing here
trains or changes a model used for reporting; it only measures the existing
17 features and eight candidate replacements.

The central idea: the benign set has two halves that are NOT equally hard.

    normal-param   (1,214 rows) -- ordinary web values, no template delimiters
    hard-negative  (  787 rows) -- real template fragments that look like attacks

A feature that only detects "a template delimiter is present" scores brilliantly
against normal-params and does nothing against hard negatives. Reporting one
pooled number hides that. Every feature below is therefore scored TWICE, and the
gap between the two scores is the diagnostic.

Run:  python feature_audit.py
"""
import re, warnings
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")
pd.set_option("display.width", 200)

ROOT = Path(__file__).resolve().parents[1]          # .../Dataset
TRAIN = ROOT / "train/combined/train_features.csv"
TEST = ROOT / "test_set/features/test_features.csv"
BENIGN = ROOT / "train/benign/benign.csv"

SEEDS = range(5)                                     # 5 grouped splits -> a noise floor


# --------------------------------------------------------------------------
# Candidate features. These are PROPOSALS under test, not adopted features.
# --------------------------------------------------------------------------
_DELIM = re.compile(r"\{\{(.*?)\}\}|\$\{(.*?)\}|\{%(.*?)%\}|<%(.*?)%>|#\{(.*?)\}", re.DOTALL)
_CHAIN = re.compile(r"[A-Za-z_]\w*(?:\s*(?:\.\s*\w+|\[[^\]]*\]))+")
_CALL = re.compile(r"\.\w+\s*\(")
_INERT = re.compile(r"^[\s\w.\[\]'\"|:=-]*$")


def _interiors(s: str):
    """Text inside template delimiters only -- where an expression would evaluate."""
    return [g for groups in _DELIM.findall(str(s)) for g in groups if g]


def _max_attr_chain(s: str) -> int:
    """Longest attribute/index walk, e.g. a.b[0].c -> 3.

    An SSTI object-graph climb is a LONG chain; benign `user.name` is short.
    This is what count_dots was reaching for but could not express, because a
    dot in an email address or a version number counts there too."""
    return max([m.group(0).count(".") + m.group(0).count("[")
                for m in _CHAIN.finditer(str(s))] + [0])


def candidate_features(s: str) -> dict:
    s = str(s)
    ins = _interiors(s)
    joined = " ".join(ins)
    return {
        "max_attr_chain_len": _max_attr_chain(s),
        # a call inside a delimiter is a call that would actually FIRE
        "call_inside_delim": len(_CALL.findall(joined)),
        "count_index_access": len(re.findall(r"\[\s*['\"]?\w+['\"]?\s*\]", s)),
        "dot_density": round(s.count(".") / len(s), 4) if s else 0.0,
        "distinct_specials": len({c for c in s if not c.isalnum() and not c.isspace()}),
        # --- the three below FAIL the hard-negative test; kept so the failure
        # --- is reproducible rather than asserted
        "interior_ratio": round(len(joined) / len(s), 4) if s else 0.0,
        "delim_inert": int(bool(ins) and all(_INERT.match(i or "") for i in ins)),
        "brace_imbalance": abs(s.count("{") - s.count("}")) + abs(s.count("(") - s.count(")")),
    }


def xgb(seed=42):
    return XGBClassifier(n_estimators=400, max_depth=6, learning_rate=0.05,
                         subsample=0.8, eval_metric="logloss",
                         random_state=seed, n_jobs=4)


def main():
    tr = pd.read_csv(TRAIN)
    te = pd.read_csv(TEST)
    base = [c for c in tr.columns if c not in ("payload", "base_id", "label")]
    new = list(candidate_features("x"))

    for d in (tr, te):
        cf = pd.DataFrame([candidate_features(p) for p in d.payload], index=d.index)
        for c in new:
            d[c] = cf[c]

    # ---------------------------------------------------------------- split the benign set
    bn = pd.read_csv(BENIGN)
    m = tr.merge(bn[["payload", "kind"]].drop_duplicates("payload"), on="payload", how="left")
    m["kind"] = m["kind"].fillna("POSITIVE")
    hard = m[m.kind.isin(["hard-negative", "POSITIVE"])]
    easy = m[m.kind.isin(["normal-param", "POSITIVE"])]
    y_hard = (hard.kind == "POSITIVE").astype(int)
    y_easy = (easy.kind == "POSITIVE").astype(int)
    print(f"positives {int((m.kind=='POSITIVE').sum())} | "
          f"hard negatives {int((m.kind=='hard-negative').sum())} | "
          f"normal params {int((m.kind=='normal-param').sum())}\n")

    # ---------------------------------------------------------------- per-feature, both halves
    print("=" * 96)
    print("PER-FEATURE DISCRIMINATION.  gap = easy AUC - hard AUC")
    print("a large gap means the feature detects 'a delimiter is present', not 'this is an attack'")
    print("=" * 96)
    rows = []
    for f in base + new:
        ah = roc_auc_score(y_hard, hard[f]); ah = max(ah, 1 - ah)
        ae = roc_auc_score(y_easy, easy[f]); ae = max(ae, 1 - ae)
        rows.append(dict(feature=f,
                         kind="existing" if f in base else "candidate",
                         fires_on_attacks=f"{(m[m.kind=='POSITIVE'][f] != 0).mean():.1%}",
                         auc_vs_hardneg=round(ah, 3),
                         auc_vs_normalparam=round(ae, 3),
                         gap=round(ae - ah, 3)))
    print(pd.DataFrame(rows).sort_values("auc_vs_hardneg", ascending=False).to_string(index=False))

    # ---------------------------------------------------------------- the reading that has headroom
    print("\n" + "=" * 96)
    print("READING 3 (proposed): attacks vs HARD NEGATIVES ONLY, grouped, 5 seeds")
    print("=" * 96)
    for name, cols in {"17 existing": base, "17 + 8 candidates": base + new}.items():
        scores = []
        for seed in SEEDS:
            a, b = next(GroupShuffleSplit(1, test_size=0.2, random_state=seed)
                        .split(hard[cols], y_hard, groups=hard.base_id))
            mdl = xgb().fit(hard.iloc[a][cols], y_hard.iloc[a])
            scores.append(roc_auc_score(y_hard.iloc[b], mdl.predict_proba(hard.iloc[b][cols])[:, 1]))
        print(f"  {name:<20} n={len(cols):>2}  AUC {np.mean(scores):.4f} +/- {np.std(scores):.4f}")

    # ---------------------------------------------------------------- full pipeline, for contrast
    print("\n" + "=" * 96)
    print("FULL POOLED PIPELINE (what you report today), grouped, 5 seeds")
    print("=" * 96)
    for name, cols in {"17 existing": base, "17 + 8 candidates": base + new}.items():
        ho, ex, pra = [], [], []
        for seed in SEEDS:
            a, b = next(GroupShuffleSplit(1, test_size=0.2, random_state=seed)
                        .split(tr[cols], tr.label, groups=tr.base_id))
            mdl = xgb().fit(tr.iloc[a][cols], tr.iloc[a].label)
            ho.append(roc_auc_score(tr.iloc[b].label, mdl.predict_proba(tr.iloc[b][cols])[:, 1]))
            p = mdl.predict_proba(te[cols])[:, 1]
            ex.append(roc_auc_score(te.label, p))
            pr, rc, _ = precision_recall_curve(te.label, p)
            pra.append(auc(rc, pr))
        print(f"  {name:<20} n={len(cols):>2}  holdout {np.mean(ho):.4f}+/-{np.std(ho):.4f} | "
              f"external {np.mean(ex):.4f}+/-{np.std(ex):.4f} | PR-AUC {np.mean(pra):.4f}+/-{np.std(pra):.4f}")


if __name__ == "__main__":
    main()
