# Onomaturgy — developer guide for Claude Code

## Two-repo structure

This project is split across two git repositories that are **always versioned and released together**. Keep the version numbers in sync.

| Repo | GitHub | Local path | Contains |
|---|---|---|---|
| `onomaturgy` | robertibatullin/onomaturgy | `c:/Users/User/projects/onomaturgy` | Python package `onomaturgy/` (submodules `generators/`, `helpers/`, `tools/`); tests; docs |
| `onomaturgy-data` | robertibatullin/onomaturgy-data | `c:/Users/User/projects/onomaturgy-data` | All CSV corpora under `onomaturgy_data/csv/`; `manifest.json`; the `onomaturgy-data` pip package |

**Hard rule: no CSV data ever goes in the `onomaturgy` repo.**  
The `onomaturgy` repo contains no data files at all. Never add CSVs here, never recreate `setting/csv/`, never add an `onomaturgy_data/` subdirectory inside this repo (a local shim with that name was deleted — it caused the installed package to be shadowed).

---

## Dev setup

Both packages must be installed for tests that touch real data. Run this once after cloning:

```bash
# 1. Install data package from the data repo (editable)
pip install -e c:/Users/User/projects/onomaturgy-data

# 2. Install code package with dev dependencies (editable)
pip install -e .[dev]
```

Verify the data package resolves to the data repo, not a local shim:

```python
from onomaturgy_data import data_path
print(data_path)
# Expected: …/onomaturgy-data/onomaturgy_data/csv
```

If it prints anything ending in `setting/csv` or a path inside the `onomaturgy` repo, a stale shim is shadowing the real package. Delete any `onomaturgy_data/` directory found inside `c:/Users/User/projects/onomaturgy/` and reinstall.

---

## Running tests

```bash
# Unit tests only — no corpus data required, runs in <1 s
python -m pytest -m "not integration"

# All tests including integration (requires onomaturgy-data installed and data_path correct)
python -m pytest
```

Tests are in `tests/`. Integration tests are marked `@pytest.mark.integration`. The conftest.py fixture sets CWD to the repo root before each test.

---

## Code layout

```
onomaturgy/              Top-level Python package
  generators/            Generator classes (SimpleNameGenerator, PlaceNameGenerator, …)
  helpers/
    data_manager.py      Download-on-demand layer — the only code that touches file paths
    csv_loaders.py       CSV reading utilities
  tools/
    compile_toponyms.py  Script to process raw toponym CSVs into derived files
tests/
  test_data_manager.py   Unit tests for all three resolution paths of data_manager
  test_integration.py    Integration tests against real corpora
config.py                Documentation stub for the ONOMATURGY_CACHE env var
```

---

## Data layout (inside onomaturgy-data)

```
onomaturgy_data/csv/
  names/<Language>/          Personal name CSVs  (name,frequency)
  toponyms/namesets/<Lang>/  Toponym CSVs (see below)
  ethnonyms/                 Ethnonym CSVs  (name,frequency)
manifest.json                Canonical list of every CSV path (see below)
```

### CSV formats

| Corpus type | Columns |
|---|---|
| Personal names, ethnonyms | `name,frequency` |
| Toponym raw | `name,frequency,place_type,place_category` |
| Toponym `_cleared` | `name,place_category,frequency` |
| Toponym `_beginnings` / `_endings` | `place_category,beginning` / `place_category,ending` |
| Toponym `_separate_beginnings` / `_separate_endings` | `place_category,separate_beginning,frequency` / `place_category,separate_ending,frequency` |

### Personal name file suffixes

| Suffix | Meaning |
|---|---|
| `_m` | Male given names |
| `_f` | Female given names |
| `_s` | Surnames (gender-neutral) |
| `_sm` / `_sf` | Male / female surnames |
| `_pm` / `_pf` | Male / female patronymics |
| `_mm` / `_mf` | Male / female metronymics |

---

## manifest.json

`manifest.json` in the `onomaturgy-data` repo root maps every data directory path (relative to `onomaturgy_data/csv/`) to a list of CSV filenames. It is used by `onomaturgy/helpers/data_manager.py` when the `onomaturgy-data` package is not installed (download-on-demand path) to know which files exist without being able to `ls` a remote URL.

**Keep it in sync with the actual files.** After adding or removing any CSV in the data repo, update `manifest.json` in the same commit.

A `manifest.json` may also appear at the root of the `onomaturgy` code repo as a stale cache artifact — it is **not used by any code** and should be deleted if found.

---

## Adding a new personal name corpus

All work in the `onomaturgy-data` repo:

1. Create `onomaturgy_data/csv/names/<Language>/` and add CSV files following the naming convention above.
2. Add the new entry to `manifest.json`.
3. Commit and push `onomaturgy-data`.
4. If README or API docs mention the available languages, update them in the `onomaturgy` repo and push that too.

---

## Adding / compiling a new toponym nameset

All work in the `onomaturgy-data` repo, using the compilation tool from the `onomaturgy` repo:

1. Place the raw CSV at `onomaturgy_data/csv/toponyms/namesets/<Language>/<Language>.csv`.  
   Required columns: `name,frequency,place_type,place_category`.

2. Run the compilation script (from the `onomaturgy-data` repo root):
   ```bash
   python c:/Users/User/projects/onomaturgy/onomaturgy/tools/compile_toponyms.py \
       onomaturgy_data/csv/toponyms/namesets/<Language>/<Language>.csv
   ```
   This produces five files alongside the raw CSV:
   `_cleared`, `_beginnings`, `_endings`, `_separate_beginnings`, `_separate_endings`.

3. Update `manifest.json`: add all six filenames (raw + five derived) for the new language.

4. Commit and push `onomaturgy-data`.

5. Update the toponym-languages list in `onomaturgy/README.md`, commit and push `onomaturgy`.

---

## Releasing

Both packages share a version number. Bump both together:

1. Update `version` in `onomaturgy/pyproject.toml`.
2. Update `version` in `onomaturgy-data/pyproject.toml`.
3. Add entries to `onomaturgy/CHANGELOG.md` and `onomaturgy-data/CHANGELOG.md`.
4. Commit and push both repos.

---

## data_manager resolution order

`onomaturgy/helpers/data_manager.py` resolves every file request through three tiers, in order:

1. **Installed package** — if `onomaturgy-data` is importable, its bundled `csv/` directory is used directly; no download.
2. **Local cache** — `~/.cache/onomaturgy/csv/` (override with the `ONOMATURGY_CACHE` env var).
3. **Remote download** — `https://raw.githubusercontent.com/robertibatullin/onomaturgy-data/main/csv/<path>`. The file is saved to the cache for future calls.

`list_dir()` follows the same order but consults `manifest.json` instead of listing a remote directory.

In the dev setup (after `pip install -e c:/Users/User/projects/onomaturgy-data`), tier 1 always hits, so tiers 2 and 3 are never reached. The `test_data_manager.py` tests cover all three tiers with mocked network calls.
