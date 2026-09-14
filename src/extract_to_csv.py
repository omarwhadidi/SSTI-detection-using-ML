#!/usr/bin/env python3
"""
extract_to_csv.py
=================

Read payloads from a .txt file (one payload per line), extract SSTI features
with ssti_feature_extraction, and write a CSV whose columns are the feature
headings and whose rows are the per-payload values.

This file is deliberately just I/O + CLI: the feature definitions live in
ssti_feature_extraction.py and are imported, so the extraction logic has a
single source of truth and this script never redefines a feature.

Usage:
    python extract_to_csv.py payloads.txt
    python extract_to_csv.py ssti.txt   -o ssti_feats.csv   --label 1
    python extract_to_csv.py benign.txt -o benign_feats.csv --label 0
    python extract_to_csv.py payloads.txt --no-payload      # omit raw payload col

Both files must sit in the same directory (the import below needs the module).
"""

import argparse
import os
import sys

from feature_extraction import build_feature_matrix


def read_payloads(path, keep_blank=False):
    """One payload per line. Newlines stripped; blank lines skipped by default.
    errors='replace' keeps the reader from crashing on odd bytes in raw payloads."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = [line.rstrip("\r\n") for line in f]
    if not keep_blank:
        lines = [ln for ln in lines if ln.strip() != ""]
    return lines


def main():
    p = argparse.ArgumentParser(
        description="Extract SSTI features from a payload .txt file into a CSV."
    )
    p.add_argument("input", help="input .txt file, one payload per line")
    p.add_argument("-o", "--output",
                   help="output .csv path (default: <input>_features.csv)")
    p.add_argument("--label",
                   help="label stamped on every row, e.g. 1 for SSTI, 0 for benign")
    p.add_argument("--keep-blank", action="store_true",
                   help="keep blank lines instead of skipping them")
    p.add_argument("--no-payload", action="store_true",
                   help="do not include the raw payload column")
    args = p.parse_args()

    if not os.path.isfile(args.input):
        sys.exit(f"Input file not found: {args.input}")

    payloads = read_payloads(args.input, keep_blank=args.keep_blank)
    if not payloads:
        sys.exit("No payloads found in input file.")

    # Build the numeric feature matrix (columns follow FEATURE_ORDER).
    df = build_feature_matrix(payloads)

    # Keep the raw payload as the first column for traceability, unless suppressed.
    if not args.no_payload:
        df.insert(0, "payload", payloads)

    # Optional constant label column (numeric if it parses as int).
    if args.label is not None:
        try:
            df["label"] = int(args.label)
        except ValueError:
            df["label"] = args.label

    out = args.output or os.path.splitext(args.input)[0] + "_features.csv"
    # pandas handles quoting/escaping of commas and quotes inside payloads.
    df.to_csv(out, index=False)
    print(f"Wrote {len(df)} rows x {len(df.columns)} columns -> {out}")


if __name__ == "__main__":
    main()
