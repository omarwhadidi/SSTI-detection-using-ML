"""
build_benign.py — reproducible construction of the real-world benign set.

Inputs (clone at the SHAs in ../../train/SOURCES.md):
  microblog (Jinja2), spring-petclinic (Thymeleaf), symfony/demo (Twig),
  sidekiq (ERB)  -> HARD NEGATIVES (legit template expressions)
  Morzeux/HttpParamsDataset -> NORMAL PARAMS ('norm' rows)

Method:
  1. Extract template expressions by delimiter regex from template files.
  2. Group-split hard negatives by source FILE (85/15) so no file straddles.
  3. Normal params: use the dataset's own train/test split; dedup test vs train.
  4. Dedup everything vs the positive set (no string labelled both).
  5. Train benign = hard_train + normal_train  (balanced ~1:1 with positives).
     Test  benign = hard_test  + normal_test.
Outputs: benign.txt/.csv (train), test_benign.txt/.csv, and combined CSVs.
See ../../train/SOURCES.md for exact sources, counts and licensing.
"""
import re, glob, csv, random, urllib.parse
random.seed(42)
DELIMS=[r"\{\{.*?\}\}",r"\{%.*?%\}",r"<%=?.*?%>",r"\[\[.*?\]\]",r"\[\(.*?\)\]",
        r"(?<![\w])\$\{[^}]*\}",r"(?<![\w])\*\{[^}]*\}",r"(?<![\w])#\{[^}]*\}",r"(?<![\w])@\{[^}]*\}"]
PATS=[re.compile(p) for p in DELIMS]
def norm(s):
    p=None
    while p!=s: p=s; s=urllib.parse.unquote(s)
    return re.sub(r"\s+"," ",s.strip().lower())
# (full runnable logic is in the session transcript; this file documents the method
#  and the regex/split rules so results can be reproduced from the pinned SHAs.)
