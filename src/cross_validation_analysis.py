"""
additional_analysis.py
=======================

Strengthens the single-split evaluation already in Model_evaluation.ipynb with
two things a thesis/paper reviewer will ask for:

  1. Cross-validated metrics (mean +/- std over 5 stratified folds) for every
     model, using the best hyperparameters already found by RandomizedSearchCV
     in the notebook. A single 80/20 split can't show how stable a result is;
     CV does.

  2. Feature importance aggregated by semantic group (structural / semantic /
     lexical), from both Random Forest and XGBoost, plus a permutation
     importance check on the held-out test split. This is the evidence for
     the "the model isn't just keying off delimiter surface artifacts"
     argument the feature-extraction script was explicitly designed to support.

Run this in the SAME environment you used for Model_evaluation.ipynb
(the notebook already trains sklearn/xgboost models successfully there).

    cd SSTI
    python additional_analysis.py

Outputs:
  - Printed tables (paste into chat / thesis)
  - cv_results.json          <- CV mean/std per model per metric
  - feature_importance.json  <- per-feature and per-group importances
  - feature_importance.png   <- bar chart, grouped by feature category
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import StratifiedKFold, cross_validate, train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.naive_bayes import GaussianNB
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from xgboost import XGBClassifier

# Make the feature-group definitions importable from dataset/ssti_feature_extraction.py
from feature_extraction import FEATURE_ORDER, FEATURE_GROUPS  # noqa: E402  (same directory)

RANDOM_STATE = 42
DATA_PATH = Path(__file__).parent.parent / "data" / "processed" / "ssti_features_all.csv"

# ---------------------------------------------------------------------------
# Load data (mirrors Model_evaluation.ipynb: drop payload, split X/y)
# ---------------------------------------------------------------------------
df = pd.read_csv(DATA_PATH)
df = df.drop(columns=["payload"])
X = df.drop(columns=["label"])
y = df["label"]

assert list(X.columns) == FEATURE_ORDER, (
    "CSV column order doesn't match FEATURE_ORDER in ssti_feature_extraction.py "
    "-- check both are in sync before trusting group-importance results."
)

# Only payload_length was scaled in the notebook; keep that identical so CV
# numbers are directly comparable to the single-split numbers already reported.
preprocess = ColumnTransformer(
    transformers=[("scale_len", StandardScaler(), ["payload_length"])],
    remainder="passthrough",
    verbose_feature_names_out=False,
)

# ---------------------------------------------------------------------------
# Models, wired up with the BEST PARAMS already found by RandomizedSearchCV
# in Model_evaluation.ipynb. We reuse them instead of re-tuning inside every
# CV fold (nested CV) -- a documented simplification, call it out in the
# thesis methodology/limitations section.
# ---------------------------------------------------------------------------
MODELS = {
    "Naive Bayes": GaussianNB(),
    "Logistic Regression": LogisticRegression(
        max_iter=1000, class_weight="balanced", n_jobs=-1
    ),
    "Decision Tree": DecisionTreeClassifier(
        max_depth=10, min_samples_leaf=5, criterion="entropy",
        class_weight="balanced", random_state=RANDOM_STATE,
    ),
    "KNN": KNeighborsClassifier(n_neighbors=3, weights="distance", n_jobs=-1),
    "SVM": SVC(
        kernel="rbf", C=10, gamma=0.1, probability=True,
        class_weight="balanced", random_state=RANDOM_STATE,
    ),
    "Random Forest": RandomForestClassifier(
        n_estimators=400, max_depth=20, min_samples_leaf=1, max_features="sqrt",
        class_weight="balanced_subsample", random_state=RANDOM_STATE, n_jobs=-1,
    ),
    "XGBoost": XGBClassifier(
        n_estimators=500, max_depth=6, learning_rate=0.2,
        subsample=1.0, colsample_bytree=0.8,
        tree_method="hist", eval_metric="mlogloss",
        random_state=RANDOM_STATE, n_jobs=-1,
    ),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
SCORING = ["accuracy", "f1_macro", "roc_auc"]

# ---------------------------------------------------------------------------
# Part 1 -- 5-fold stratified CV, mean +/- std per model
# ---------------------------------------------------------------------------
print("=" * 70)
print("5-FOLD STRATIFIED CROSS-VALIDATION (mean +/- std)")
print("=" * 70)

cv_summary = {}
for name, clf in MODELS.items():
    pipe = Pipeline([("prep", preprocess), ("clf", clf)])
    scores = cross_validate(pipe, X, y, cv=cv, scoring=SCORING, n_jobs=-1)
    row = {}
    for metric in SCORING:
        vals = scores[f"test_{metric}"]
        row[metric] = {"mean": float(vals.mean()), "std": float(vals.std())}
    cv_summary[name] = row
    print(f"\n{name}")
    for metric in SCORING:
        m = row[metric]
        print(f"  {metric:10s}: {m['mean']:.4f} +/- {m['std']:.4f}")

RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)
with open(RESULTS_DIR / "cv_results.json", "w") as f:
    json.dump(cv_summary, f, indent=2)
print("\nSaved -> cv_results.json")

# ---------------------------------------------------------------------------
# Part 2 -- Feature importance, aggregated by group (structural/semantic/lexical)
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print("FEATURE IMPORTANCE (Random Forest + XGBoost, fit on full data)")
print("=" * 70)

# Fit on the FULL dataset for the "which features matter overall" story.
X_scaled = X.copy()
scaler_full = StandardScaler()
X_scaled["payload_length"] = scaler_full.fit_transform(X_scaled[["payload_length"]])

rf_full = RandomForestClassifier(
    n_estimators=400, max_depth=20, min_samples_leaf=1, max_features="sqrt",
    class_weight="balanced_subsample", random_state=RANDOM_STATE, n_jobs=-1,
)
xgb_full = XGBClassifier(
    n_estimators=500, max_depth=6, learning_rate=0.2,
    subsample=1.0, colsample_bytree=0.8,
    tree_method="hist", eval_metric="mlogloss",
    random_state=RANDOM_STATE, n_jobs=-1,
)
rf_full.fit(X_scaled, y)
xgb_full.fit(X_scaled, y)

importance_df = pd.DataFrame({
    "feature": FEATURE_ORDER,
    "rf_importance": rf_full.feature_importances_,
    "xgb_importance": xgb_full.feature_importances_,
})
importance_df["mean_importance"] = importance_df[["rf_importance", "xgb_importance"]].mean(axis=1)

group_of = {feat: grp for grp, feats in FEATURE_GROUPS.items() for feat in feats}
importance_df["group"] = importance_df["feature"].map(group_of)

print("\nPer-feature importance (sorted):")
print(importance_df.sort_values("mean_importance", ascending=False).to_string(index=False))

group_importance = importance_df.groupby("group")["mean_importance"].sum().sort_values(ascending=False)
print("\nAggregated by semantic group (RF+XGB mean, sums to ~1.0):")
print(group_importance.to_string())

# Permutation importance on a held-out split, as a model-agnostic cross-check
# against the impurity-based importances above (same split logic as the notebook).
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=15, stratify=y
)
X_train_s = X_train.copy()
X_test_s = X_test.copy()
scaler_split = StandardScaler()
X_train_s["payload_length"] = scaler_split.fit_transform(X_train_s[["payload_length"]])
X_test_s["payload_length"] = scaler_split.transform(X_test_s[["payload_length"]])

rf_split = RandomForestClassifier(
    n_estimators=400, max_depth=20, min_samples_leaf=1, max_features="sqrt",
    class_weight="balanced_subsample", random_state=RANDOM_STATE, n_jobs=-1,
)
rf_split.fit(X_train_s, y_train)
perm = permutation_importance(
    rf_split, X_test_s, y_test, n_repeats=30, random_state=RANDOM_STATE, n_jobs=-1
)
perm_df = pd.DataFrame({
    "feature": FEATURE_ORDER,
    "perm_importance_mean": perm.importances_mean,
    "perm_importance_std": perm.importances_std,
}).sort_values("perm_importance_mean", ascending=False)
perm_df["group"] = perm_df["feature"].map(group_of)

print("\nPermutation importance on held-out test split (RF, model-agnostic cross-check):")
print(perm_df.to_string(index=False))

# Save everything
out = {
    "impurity_importance_per_feature": importance_df.to_dict(orient="records"),
    "impurity_importance_per_group": group_importance.to_dict(),
    "permutation_importance_per_feature": perm_df.to_dict(orient="records"),
}
with open(RESULTS_DIR / "feature_importance.json", "w") as f:
    json.dump(out, f, indent=2)
print("\nSaved -> feature_importance.json")

# Bar chart, features colored/grouped by category
fig, ax = plt.subplots(figsize=(9, 6))
plot_df = importance_df.sort_values("mean_importance", ascending=True)
colors = {"structural": "#4C72B0", "semantic": "#DD8452", "lexical": "#55A868"}
bar_colors = plot_df["group"].map(colors)
ax.barh(plot_df["feature"], plot_df["mean_importance"], color=bar_colors)
ax.set_xlabel("Mean impurity-based importance (RF + XGBoost)")
ax.set_title("Feature importance by semantic group")
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in colors.values()]
ax.legend(handles, colors.keys(), loc="lower right")
plt.tight_layout()
plt.savefig(RESULTS_DIR / "figures" / "feature_importance.png", dpi=150)
print("Saved -> feature_importance.png")

print("\nDone. Send cv_results.json, feature_importance.json and the printed")
print("tables back so the report/paper can be written from real numbers.")
