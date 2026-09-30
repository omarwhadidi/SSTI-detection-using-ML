"""
ssti_feature_extraction.py
==========================

Feature extraction for binary SSTI attack-input classification (SSTI vs benign).

Each feature is a deterministic function of one payload string, chosen so its
value differs systematically between SSTI attempts and benign inputs. Comments
explain the *why* (the discriminative rationale), not the *what*, because every
choice here has to be defensible on paper.

Categorization is exported on two axes:

  * FEATURE_GROUPS -- semantic role (structural / semantic / lexical). Aggregate
    feature importance by group to show the model draws real weight from the
    semantic group and is not resting on delimiter surface artifacts alone.

  * BINARY_FEATURES / SCALE_FEATURES -- value type. Binary 0/1 flags must NOT be
    scaled; counts and length go through a StandardScaler fit ONCE on the
    training fold and reused. Feed only SCALE_FEATURES to the scaler.
"""

import re
import pandas as pd


# ---------------------------------------------------------------------------
# Canonical column order -> stable, reproducible feature matrix across folds.
# ---------------------------------------------------------------------------
FEATURE_ORDER = [
    # lexical
    "payload_length",
    "special_char_ratio",
    # structural (the full delimiter surface)
    "count_double_brace",
    "count_dollar_brace",
    "count_hash_brace",
    "count_percent_brace",
    "count_erb",
    "delimiter_family_count",
    "max_bracket_depth",
    # semantic (exploit intent + evasion)
    "has_dunder_chain",
    "has_exec_tokens",
    "has_java_reflection",
    "has_flask_objects",
    "has_arithmetic_operation",
    "has_string_operation",
    "count_method_calls",
    "count_dots",
]

# ---------------------------------------------------------------------------
# AXIS 1 -- semantic role. Report importance aggregated by these groups.
# ---------------------------------------------------------------------------
FEATURE_GROUPS = {
    "structural": [            # delimiter surface: high signal, but exactly the
        "count_double_brace",  # level that can make the task trivial without hard
        "count_dollar_brace",  # negatives. Watch this group's importance share.
        "count_hash_brace",
        "count_percent_brace",
        "count_erb",
        "delimiter_family_count",
        "max_bracket_depth",
    ],
    "semantic": [              # what the payload is TRYING TO DO + how it hides.
        "has_dunder_chain",    # Generalizes past the data source -> defensibility.
        "has_exec_tokens",
        "has_java_reflection",
        "has_flask_objects",
        "has_arithmetic_operation",
        "has_string_operation",
        "count_method_calls",
        "count_dots",
    ],
    "lexical": [               # statistical shape of the string, orthogonal signal
        "payload_length",
        "special_char_ratio",
    ],
}

# ---------------------------------------------------------------------------
# AXIS 2 -- value type, for preprocessing discipline.
#   BINARY_FEATURES : already 0/1 -> DO NOT scale.
#   SCALE_FEATURES  : counts + length + bounded ratio -> StandardScaler fit ONCE
#                     on the training fold, reused everywhere (same discipline as
#                     the CICIDS2017 pipeline).
# ---------------------------------------------------------------------------
BINARY_FEATURES = [
    "has_dunder_chain",
    "has_exec_tokens",
    "has_java_reflection",
    "has_flask_objects",
    "has_arithmetic_operation",
    "has_string_operation",
]
SCALE_FEATURES = [f for f in FEATURE_ORDER if f not in BINARY_FEATURES]


# ---------------------------------------------------------------------------
# Precompiled patterns (compiled once at import for speed over large corpora).
# ---------------------------------------------------------------------------

# Python/Jinja2 sandbox-escape fingerprint: the magic attributes an attacker
# walks to climb from a harmless object up to __globals__ / __builtins__.
_DUNDER = re.compile(
    r"__(?:class|mro|subclasses|globals|builtins|import|base|init|dict|"
    r"getattribute|reduce)__"
)

# RCE intent, engine-agnostic. Bare `os`/`eval`/`exec` are deliberately avoided
# (they collide with benign words); a call/access context is required.
_EXEC = re.compile(
    r"system\s*\(|popen|subprocess|Runtime|ProcessBuilder|getRuntime|"
    r"__import__|os\.system|os\.popen|commands\.|\beval\s*\(|\bexec\s*\(|"
    r"/bin/(?:ba)?sh|cmd\.exe"
)

# Java-engine escape route (Freemarker / Velocity / Thymeleaf reflection).
_JAVA_REFLECT = re.compile(
    r"getClass|forName|getClassLoader|ClassLoader|\.class\b|getDeclared|getMethod|"
    r"freemarker\.template\.utility\.Execute"
)

# Flask/Jinja2 built-in objects abused as a springboard to globals. Word-bounded
# so they match as tokens, not substrings. One weak signal among many.
_FLASK = re.compile(
    r"\b(?:config|request|self|cycler|lipsum|joiner|namespace|url_for|"
    r"get_flashed_messages)\b"
)

# Method invocation: `.name(` is where an object-graph walk actually FIRES.
_METHOD_CALL = re.compile(r"\.\w+\s*\(")

# String operations: concatenation (~, quote+quote) is the primary keyword-
# splitting EVASION mechanism ('sys'+'tem'); the listed methods build/obfuscate
# payloads. This feature is the model's hook for catching obfuscated attempts.
_STRING_OP = re.compile(
    r"~"                                        # Jinja2 concatenation operator
    r"|['\"]\s*[+~]\s*['\"]"                     # 'a'+'b' keyword splitting
    r"|['\"]\s*[+~]"                             # quote followed by concat op
    r"|\.(?:replace|join|split|format|concat|encode|decode|lower|upper|strip|"
    r"substring|charAt|reverse|slice|substr)\s*\("
)

# Delimiter interiors, so arithmetic is judged INSIDE a template expression
# (where 7*7 means "evaluate this") rather than anywhere in the string.
_DELIM_INTERIOR = re.compile(
    r"\{\{(.*?)\}\}|\$\{(.*?)\}|\{%(.*?)%\}|<%(.*?)%>|#\{(.*?)\}", re.DOTALL
)
_ARITH = re.compile(r"\d+\s*[*+\-/]\s*\d+")     # digit-op-digit evaluation probe

# Engine delimiter families for delimiter_family_count.
_FAMILY_PATTERNS = {
    "jinja_twig_handlebars": re.compile(r"\{\{"),
    "freemarker_thymeleaf_mako": re.compile(r"\$\{"),
    "velocity": re.compile(r"#\{|#set|#foreach|#if"),
    "ognl_struts": re.compile(r"%\{"),
    "erb_freemarker_directive": re.compile(r"<%|<#|<@"),
}

# Per-family count patterns (for the individual count_* features).
_DOUBLE_BRACE = "{{"
_DOLLAR_BRACE = "${"
_HASH = re.compile(r"#\{|#set|#foreach|#if")
_PERCENT = re.compile(r"%\{")
_ERB = re.compile(r"<%|%>|<#|<@")


def _max_bracket_depth(s: str) -> int:
    """Deepest simultaneous nesting of () [] {}. Object-graph walks nest;
    benign parameters almost never do, so peak depth is a structural tell."""
    depth = max_depth = 0
    for ch in s:
        if ch in "([{":
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch in ")]}":
            depth = max(0, depth - 1)
    return max_depth


def _has_arithmetic_operation(s: str) -> int:
    """1 if a digit-op-digit arithmetic operation appears inside a template
    delimiter (the evaluation probe). Falls back to a raw scan only when no
    delimiters are present, which keeps benign dates/paths from false-firing."""
    interiors = [g for groups in _DELIM_INTERIOR.findall(s) for g in groups if g]
    if interiors:
        return 1 if any(_ARITH.search(i) for i in interiors) else 0
    return 1 if _ARITH.search(s) else 0


def extract_features(payload: str) -> dict:
    """Map one payload string to its 17 numeric features (ordered dict)."""
    s = payload if isinstance(payload, str) else str(payload)
    length = len(s)

    special = sum(1 for c in s if not c.isalnum() and not c.isspace())
    special_ratio = (special / length) if length else 0.0

    delimiter_families = sum(1 for pat in _FAMILY_PATTERNS.values() if pat.search(s))

    feats = {
        # lexical
        "payload_length": length,
        "special_char_ratio": round(special_ratio, 6),
        # structural
        "count_double_brace": s.count(_DOUBLE_BRACE),
        "count_dollar_brace": s.count(_DOLLAR_BRACE),
        "count_hash_brace": len(_HASH.findall(s)),
        "count_percent_brace": len(_PERCENT.findall(s)),
        "count_erb": len(_ERB.findall(s)),
        "delimiter_family_count": delimiter_families,
        "max_bracket_depth": _max_bracket_depth(s),
        # semantic
        "has_dunder_chain": 1 if _DUNDER.search(s) else 0,
        "has_exec_tokens": 1 if _EXEC.search(s) else 0,
        "has_java_reflection": 1 if _JAVA_REFLECT.search(s) else 0,
        "has_flask_objects": 1 if _FLASK.search(s) else 0,
        "has_arithmetic_operation": _has_arithmetic_operation(s),
        "has_string_operation": 1 if _STRING_OP.search(s) else 0,
        "count_method_calls": len(_METHOD_CALL.findall(s)),
        "count_dots": s.count("."),
    }
    return {k: feats[k] for k in FEATURE_ORDER}


def build_feature_matrix(payloads, labels=None) -> pd.DataFrame:
    """Vectorize payloads into a fully numeric DataFrame in FEATURE_ORDER.
    If labels are given, a `label` column is appended."""
    rows = [extract_features(p) for p in payloads]
    df = pd.DataFrame(rows, columns=FEATURE_ORDER)
    if labels is not None:
        df["label"] = list(labels)
    return df


if __name__ == "__main__":
    samples = [
        # SSTI (label 1): clean chain, arithmetic probe, velocity RCE, evasion
        ("{{''.__class__.__mro__[1].__subclasses__()[396]('id')}}", 1),
        ("${7*7}", 1),
        ("#set($x=$rt.getRuntime().exec('id'))", 1),
        ("{{''['__cl'+'ass__']['__ba'+'se__']}}", 1),   # string-op evasion
        # benign (label 0): JSON, and template text that trips count_double_brace
        ('{"user":{"name":"omar","roles":["admin"]}}', 0),
        ("Hello {{ user.first_name }}, your total is $42", 0),
    ]
    df = build_feature_matrix([p for p, _ in samples], [y for _, y in samples])
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 60)
    print(df.to_string(index=False))
    print("\nGroups:", {k: len(v) for k, v in FEATURE_GROUPS.items()})
    print("Total features:", len(FEATURE_ORDER))
    print("SCALE_FEATURES :", SCALE_FEATURES)
    print("BINARY_FEATURES:", BINARY_FEATURES)
