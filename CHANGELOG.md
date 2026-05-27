# Changelog

All notable changes to the **onomaturgy** code package are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.2.2] — 2026-05-27

### Added
- Personal name corpora for **Algerian** (under `Arabic`), **Cameroonian**,
  **Chinese**, and **Israeli** — see `onomaturgy-data` 0.2.2 for the CSV files.
- `README.md` updated: personal name languages table reflects all four new
  entries.

---

## [0.2.1] — 2026-05-27

### Added

- `onomaturgy` subdir, and moved `generators`, `tools` and `helpers` there.

- Imported all user-end generators into `onomaturgy.__init__` so they are importable as `from onomaturgy import SomeGenerator`.

---

## [0.2.0] — 2026-05-27

### Added
- `tools/compile_toponyms.py` — processes a raw `<Language>.csv` toponym file
  into the five derived files (`_cleared`, `_beginnings`, `_endings`,
  `_separate_beginnings`, `_separate_endings`) required by `PlaceNameGenerator`.
- Toponym namesets for **French, Italian, Spanish, Basque, and Catalan** are now
  fully compiled; all five languages are usable with `PlaceNameGenerator`.
- `tests/test_data_manager.py` — 17 unit tests covering every resolution path of
  the download-on-demand layer: installed-package priority, cache hit, cache miss
  with download, 404 handling, manifest download, `invalidate_cache`, and a full
  end-to-end test confirming that a second `train()` call adds zero network
  requests.
- `API.md`: place-categories table listing all 16 geographic feature types
  accepted by `PlaceNameGenerator`.
- `README.md`: matching place-categories table under Available Data.

### Removed
- **`generators/name_transformers.py`** and the four generator classes it
  contained: `AdjectiveFromEthnonymGenerator`,
  `CountryNameFromLatinEthnonymGenerator`,
  `CountryNameFromNativeEthnonymGenerator`, and `DynastyNameGenerator`.
  These rule-based transformers had no library users.
- **`PseudoOldFinnic`** personal-name dataset.
- `tests/test_name_transformers.py`.

### Fixed
- `API.md`: removed stale "Requires `pandas`" note from `PlaceNameGenerator`;
  property types corrected from `pd.DataFrame` to `list[tuple]`.
- `README.md`: architecture diagram updated to reflect actual class hierarchy;
  name-transformers Quick Start section removed; Basque and Catalan added to the
  toponym-languages list.

---

## [0.1.0] — 2026-05-25

Initial release.

- `BaseGenerator` abstract base with lazy `train()` / `generate()` lifecycle.
- `WordGenerator`, `SimpleNameGenerator`, `PersonalNameGenerator`,
  `TribalNameGenerator`, `PlaceNameGenerator` — core generator classes.
- `MarkovChainWordGenerator`, `WordPicker` — low-level synthesis engines.
- `generator_factory` — config-dict-driven generator construction with caching.
- `helpers/data_manager.py` — download-on-demand corpus manager with three-tier
  resolution: installed `onomaturgy-data` package → local cache →
  remote GitHub download.
- Personal name corpora for ~45 languages; ethnonym corpora for Baltic, Celtic,
  Germanic, and Slavic families; toponym namesets for 28 languages.
- Full pytest suite with unit and integration test markers.
