"""Compile raw toponym CSV into the five derived files the generator needs.

Input:  <Language>.csv  — columns: name, frequency, place_type, place_category
Output (same directory):
  <Language>_cleared.csv              name, place_category, frequency
  <Language>_beginnings.csv           place_category, beginning   (char n-grams 3-6)
  <Language>_endings.csv              place_category, ending      (char n-grams 3-9)
  <Language>_separate_beginnings.csv  place_category, separate_beginning, frequency
  <Language>_separate_endings.csv     place_category, separate_ending,    frequency

Usage (run from the onomaturgy-data repo root):
  python /path/to/onomaturgy/tools/compile_toponyms.py onomaturgy_data/csv/toponyms/namesets/French/French.csv [...]
"""

import csv
import os
import sys
from collections import defaultdict


MIN_FREQ = 2  # minimum weighted frequency (per category) to qualify as a separate word


def compile_nameset(csv_path: str) -> None:
    base = os.path.splitext(csv_path)[0]
    lang = os.path.basename(base)

    raw: list[dict] = []
    with open(csv_path, encoding="utf-8") as f:
        raw = list(csv.DictReader(f))

    all_cats = sorted({r["place_category"] for r in raw})

    # ── Step 1: discover separate beginnings and endings ────────────────────
    # Count weighted frequency of each word as first/last word in multi-word
    # names, broken down per place_category.
    first_freq: dict[tuple, int] = defaultdict(int)  # (word, cat) → Σ frequency
    last_freq:  dict[tuple, int] = defaultdict(int)

    for r in raw:
        parts = r["name"].split()
        if len(parts) < 2:
            continue
        freq = int(r["frequency"])
        cat  = r["place_category"]
        first_freq[(parts[0],  cat)] += freq
        last_freq[ (parts[-1], cat)] += freq

    sep_begs: dict[tuple, int] = {k: v for k, v in first_freq.items() if v >= MIN_FREQ}
    sep_ends: dict[tuple, int] = {k: v for k, v in last_freq.items()  if v >= MIN_FREQ}

    sep_beg_by_cat: dict[str, dict[str, int]] = defaultdict(dict)
    sep_end_by_cat: dict[str, dict[str, int]] = defaultdict(dict)
    for (word, cat), freq in sep_begs.items():
        sep_beg_by_cat[cat][word] = freq
    for (word, cat), freq in sep_ends.items():
        sep_end_by_cat[cat][word] = freq

    # ── Step 2: clear names ──────────────────────────────────────────────────
    cleared: dict[tuple, int] = defaultdict(int)  # (name, cat) → Σ frequency
    cat_total_freq:       dict[str, int] = defaultdict(int)
    cat_beg_stripped_freq: dict[str, int] = defaultdict(int)
    cat_end_stripped_freq: dict[str, int] = defaultdict(int)

    for r in raw:
        parts = r["name"].split()
        freq  = int(r["frequency"])
        cat   = r["place_category"]
        cat_total_freq[cat] += freq

        beg_stripped = len(parts) >= 2 and (parts[0], cat) in sep_begs
        if beg_stripped:
            parts = parts[1:]
            cat_beg_stripped_freq[cat] += freq

        end_stripped = len(parts) >= 2 and (parts[-1], cat) in sep_ends
        if end_stripped:
            parts = parts[:-1]
            cat_end_stripped_freq[cat] += freq

        if parts:
            cleared[(" ".join(parts), cat)] += freq

    # ── Step 3: character n-grams from single-word cleared names ────────────
    beg_ngrams: dict[str, set] = defaultdict(set)
    end_ngrams: dict[str, set] = defaultdict(set)

    for (name, cat) in cleared:
        if " " in name:
            continue
        for n in range(3, 7):
            if len(name) >= n:
                beg_ngrams[cat].add(name[:n])
        for n in range(3, 10):
            if len(name) >= n:
                end_ngrams[cat].add(name[-n:])

    # ── Write outputs ────────────────────────────────────────────────────────
    def write(filename, header, rows):
        with open(filename, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)

    # cleared.csv
    write(
        f"{base}_cleared.csv",
        ["name", "place_category", "frequency"],
        [(name, cat, freq) for (name, cat), freq in sorted(cleared.items())],
    )

    # separate_beginnings.csv
    beg_rows = []
    for cat in all_cats:
        none_freq = cat_total_freq[cat] - cat_beg_stripped_freq[cat]
        beg_rows.append((cat, "<NONE>", max(1, none_freq)))
        for word, freq in sorted(sep_beg_by_cat.get(cat, {}).items()):
            beg_rows.append((cat, word, freq))
    write(f"{base}_separate_beginnings.csv", ["place_category", "separate_beginning", "frequency"], beg_rows)

    # separate_endings.csv
    end_rows = []
    for cat in all_cats:
        none_freq = cat_total_freq[cat] - cat_end_stripped_freq[cat]
        end_rows.append((cat, "<NONE>", max(1, none_freq)))
        for word, freq in sorted(sep_end_by_cat.get(cat, {}).items()):
            end_rows.append((cat, word, freq))
    write(f"{base}_separate_endings.csv", ["place_category", "separate_ending", "frequency"], end_rows)

    # beginnings.csv
    write(
        f"{base}_beginnings.csv",
        ["place_category", "beginning"],
        [(cat, ng) for cat in sorted(beg_ngrams) for ng in sorted(beg_ngrams[cat])],
    )

    # endings.csv
    write(
        f"{base}_endings.csv",
        ["place_category", "ending"],
        [(cat, ng) for cat in sorted(end_ngrams) for ng in sorted(end_ngrams[cat])],
    )

    n_begs = sum(len(v) for v in sep_beg_by_cat.values())
    n_ends = sum(len(v) for v in sep_end_by_cat.values())
    print(f"{lang}: {len(raw)} raw -> {len(cleared)} cleared, {n_begs} sep_begs, {n_ends} sep_ends")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    for path in sys.argv[1:]:
        compile_nameset(path)
