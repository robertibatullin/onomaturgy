# API Reference

All generators follow the same two-step lifecycle:

1. **Instantiate** — pass configuration (languages, markov ratio, constraints, etc.)
2. **`train()`** — load CSV data and build internal models
3. **`generate(n, ...)`** — return a list of `n` generated strings

`generate()` auto-calls `train()` if it hasn't been called yet.

---

## `BaseGenerator` — abstract base

**`generators/base_generator.py`**

All generators inherit from this class.

```python
class BaseGenerator(ABC):
    is_trained: bool          # True after train() completes

    @abstractmethod
    def train(self): ...

    @abstractmethod
    def generate(self, n: int, **kwargs) -> list[str]: ...
```

---

## `WordConstraints` / `WordExtremes`

**`generators/word_constraints.py`**

Passed as `**kwargs` to most generators to limit output word size.

```python
@dataclass
class WordConstraints:
    max_characters: int | None = None
    min_characters: int | None = None
    max_syllables:  int | None = None
    min_syllables:  int | None = None
    max_word_parts: int | None = None   # space- or hyphen-separated parts
    min_word_parts: int | None = None
```

`None` means unconstrained. Values not supplied by the caller are inferred from the training corpus (set to the corpus extremes) via `update_by_extremes()`.

### Helper functions

```python
def count_word_parts(word: str) -> int
```
Returns number of space/hyphen-delimited parts (minimum 1).

```python
def count_syllables(word: str) -> int
```
Counts contiguous vowel groups (includes accented characters).

---

## `MarkovChainWordGenerator`

**`generators/markov_chain.py`**

Low-level character-level Markov chain. Typically used through `WordGenerator` rather than directly.

```python
MarkovChainWordGenerator(
    window: int,            # n-gram size (e.g. 3)
    overlap: int,           # shared characters between consecutive n-grams (e.g. 2)
    pattern: str | None,    # phonetic pattern constraint (see Patterns)
    forward: bool,          # True = left-to-right, False = right-to-left
    **constraints           # WordConstraints fields
)
```

### Methods

```python
def train_on_nameset(self, names: list[str]) -> None
```
Train from an in-memory list of strings. Raises `ValueError` if no valid beginnings/endings are found.

```python
def train(self) -> None
```
Train from CSV files previously added to `self.paths`.

```python
def generate(self, n: int, no_repeat: bool) -> list[str]
```
Generate `n` words. With `no_repeat=True`, excludes words already seen in the training corpus and avoids duplicates in the output. Makes up to `10 * n` attempts; returns fewer than `n` if attempts are exhausted.

### Phonetic patterns

`pattern` accepts a regex-like string where `C` matches any consonant and `V` matches any vowel (including accented variants). The pattern must either start with `.+` (match from the end) or end with `.+` (match from the beginning). Multiple alternatives can be joined with `|`.

| Pattern | Meaning |
|---------|---------|
| `None` | No constraint |
| `'.+VC'` | Word must end with a vowel followed by a consonant |
| `'CV.+'` | Word must start with a consonant followed by a vowel |
| `'.+ing\|.+burg'` | Word must end with `ing` or `burg` |

---

## `WordPicker`

**`generators/word_generator.py`**

Selects words directly from the training corpus using frequency weights.

```python
WordPicker(**constraints)   # WordConstraints fields as kwargs
```

```python
def train(self, names: list[str], weights: list[float]) -> None
def generate(self, n: int, no_repeat: bool) -> list[str]
```

---

## `WordGenerator`

**`generators/word_generator.py`**

Combines `MarkovChainWordGenerator` and `WordPicker` in a configurable ratio. Base class for `SimpleNameGenerator` and `TribalNameGenerator`.

```python
WordGenerator(
    *paths: str,            # paths to CSV files (name, frequency)
    markov: float,          # 0.0 = corpus-only; 1.0 = Markov-only; 0.5 = mixed
    pattern: str | None,    # phonetic pattern (see Patterns above)
    **constraints           # WordConstraints fields
)
```

`markov=0.0` picks directly from the corpus; `markov=1.0` always synthesises new words via the Markov chain; intermediate values blend both strategies randomly on each generation call.

### Methods

```python
def train(self) -> None
def generate(self, n: int, no_repeat: bool = True) -> list[str]
def equalize_weights(self) -> None   # set all corpus weights to 1 (uniform sampling)
```

### CSV format

```
name,frequency
Björn,142
Leif,89
```
Header row is skipped. `frequency` column is optional; defaults to 1 if absent.

---

## `SimpleNameGenerator`

**`generators/simple_name.py`**

Generates a single name part (given name, surname, patronymic, or metronymic) for a given gender and set of languages. Inherits `WordGenerator`.

```python
SimpleNameGenerator(
    *languages: str,                        # e.g. 'Russian', 'Norwegian'
    gender: str,                            # 'male' or 'female'
    markov: float,
    pattern: str | None,
    name_part_type: str | NamePartType,     # see NamePartType
    **constraints                           # WordConstraints fields
)
```

### `NamePartType` enum

```python
class NamePartType(Enum):
    GIVEN_NAME   # → _m.csv / _f.csv
    SURNAME      # → _sm.csv / _sf.csv / _s.csv (fallback)
    PATRONYMIC   # → _pm.csv / _pf.csv
    METRONYMIC   # → _mm.csv / _mf.csv
```

String names (case-insensitive) are accepted and converted automatically: `'given_name'`, `'surname'`, `'patronymic'`, `'metronymic'`.

### Methods

```python
def train(self) -> None
def generate(self, n: int, no_repeat: bool = True) -> list[str]
```

### Helper function

```python
def get_nameset_paths(
    languages: list[str],
    name_part_type: NamePartType,
    gender: str,
) -> list[str]
```
Returns all CSV paths that exist for the given combination.

---

## `PersonalNameGenerator`

**`generators/personal_name.py`**

Composes multiple name parts into full personal names.

```python
PersonalNameGenerator(
    *languages: str,
    name_pattern: list[str | NamePartType],
    # e.g. ['given_name', 'patronymic', 'surname']
    markov: dict[str | NamePartType, float],
    # e.g. {'given_name': 0.7, 'patronymic': 0.0, 'surname': 0.5}
    name_part_patterns: dict[str | NamePartType, str] | None = None,
    # optional per-part phonetic patterns
)
```


### Methods

```python
def train(self) -> None
```
Builds one `SimpleNameGenerator` per (name-part, gender) combination.

```python
def generate(self, n: int, female_fraction: float) -> list[str]
```
Returns `n` full names. `female_fraction` (0.0–1.0) controls the probability that each name is female.

---

## `TribalNameGenerator`

**`generators/tribal_name.py`**

Generates tribe/people names drawn from ethnonym CSV files. Inherits `WordGenerator`.

```python
TribalNameGenerator(
    *languages: str,        # language family names, e.g. 'Germanic', 'Celtic'
    markov: float,
    pattern: str | None,
    **constraints           # WordConstraints fields
)
```

Available language families: `Baltic`, `Celtic`, `Germanic`, `Slavic`.

```python
def train(self) -> None
def generate(self, n: int, no_repeat: bool = True) -> list[str]
```

### Helper function

```python
def get_ethnonym_paths(language_families: list[str]) -> list[str]
```
Returns paths to existing ethnonym CSVs. Silently skips missing families.

---

## `PlaceNameGenerator`

**`generators/place_name.py`**

Generates place names with optional geographic-category prefixes/suffixes. Requires `pandas`.

```python
PlaceNameGenerator(
    *languages: str,                # e.g. 'English', 'Norwegian'
    pattern: str | None,
    place_categories: list[str],    # e.g. ['settlement', 'river']
    **constraints                   # WordConstraints fields
)
```

`place_categories` filters the beginning/ending affixes loaded from the data files. Pass an empty list to use all categories.

### Methods

```python
def train(self) -> None
```
Loads CSV data from `setting/csv/toponyms/namesets/<Language>/` and trains the internal Markov chain on `<Language>_cleared.csv`.

```python
def generate(self, n: int) -> list[str]
```
Returns `n` place names. If `max_word_parts == 1`, returns bare Markov-generated words. Otherwise prepends/appends random separate beginning/ending tokens (e.g. `"Great"`, `"upon Trent"`).

### Properties (after `train()`)

```python
gen.names               # pd.DataFrame — full name corpus
gen.beginnings          # pd.DataFrame — compound beginnings by category
gen.endings             # pd.DataFrame — compound endings by category
gen.separate_beginnings # pd.DataFrame — separate prefix tokens
gen.separate_endings    # pd.DataFrame — separate suffix tokens
```

### Data file layout (per language)

```
setting/csv/toponyms/namesets/<Language>/
    <Language>_cleared.csv           — name, frequency
    <Language>_beginnings.csv        — beginning, place_category
    <Language>_endings.csv           — ending, place_category
    <Language>_separate_beginnings.csv — separate_beginning, place_category, frequency
    <Language>_separate_endings.csv  — separate_ending, place_category, frequency
```

---

## Name transformer generators

All four classes below are **rule-based** (no training corpus needed). `train()` is a no-op. `generate(n)` ignores `n` and returns as many forms as the rules produce.

### `AdjectiveFromEthnonymGenerator`

**`generators/name_transformers.py`**

Derives a demonym adjective from an ethnonym.

```python
AdjectiveFromEthnonymGenerator(ethnonym: str)
gen.generate(n)  # returns list[str]
```

| Input suffix | Output |
|---|---|
| `ii` | `…ian` (drop one `i`) |
| `i` | `…ian` |
| `es` | `…ian`, `…ean` |
| `ans` | `…an` |
| `s` | `…ian` |
| `ae` | `…n`, `…nian` |
| ends with vowel | `…nian` |
| other | unchanged |

### `CountryNameFromLatinEthnonymGenerator`

Derives country names from a Latin-form ethnonym.

```python
CountryNameFromLatinEthnonymGenerator(ethnonym: str)
gen.generate(n)  # returns list[str]
```

| Input suffix | Output |
|---|---|
| `ii` | `…ia` |
| `i` | `…ia` (drop `i`) |
| `es` | `…ia` |
| `ians` | `…ia` |
| `ans` | `…a`, `…` |
| `s` | `…ia`, `…` |
| `ae` | `…`, `…nia` |
| other | unchanged, `…ia` |


### `CountryNameFromNativeEthnonymGenerator`

Derives country names using language-family-specific rules.

```python
CountryNameFromNativeEthnonymGenerator(
    ethnonym: str,
    language_family: str | None = None,  # 'Germanic', 'Celtic', 'Finnic'
)
gen.generate(n)  # returns list[str]
```

| Language family | Rules |
|---|---|
| `Germanic` | Strips trailing `s`, removes final vowels → `…land`, `…en` |
| `Celtic` | Strips trailing `s`, returns singular and `Dal <singular>` |
| `Finnic` | Returns `<ethnonym>maa` |
| other / `None` | Returns nothing |

### `DynastyNameGenerator`

Generates dynasty names by producing male given names and applying a language-specific suffix. Inherits `SimpleNameGenerator`.

```python
DynastyNameGenerator(
    *languages: str,        # single language; uses languages[0] for suffix
    pattern: str | None,
    markov: float,
    **constraints
)
gen.generate(n)  # returns list[str]
```

| Language | Suffix rule |
|---|---|
| `OldGerman`, `Gothic`, `AngloSaxon`, `OldNorse` | strip trailing vowels + `ing` |
| `OldIrish` | `Ui <stem>` |
| all others | strip trailing vowels + `id` |

---

## `generator_factory`

**`generators/generator_factory.py`**

Creates and caches generator instances from a configuration dict.

```python
def generator_factory(config: dict, context: dict) -> BaseGenerator
```

`config` is consumed (keys are popped). Required keys:

| Key | Type | Description |
|-----|------|-------------|
| `name` | `str` | Unique name used as cache key in `context['generators']` |
| `class` | `str` | Generator class name (must be importable from this module) |
| `languages` | `str \| list[str]` | Passed as positional args |

All remaining keys are passed as `**kwargs` to the constructor.


---

## `load_names_with_weights`

**`helpers/csv_loaders.py`**

```python
def load_names_with_weights(
    path: str,
    pattern: str | None = None,
) -> tuple[list[str], list[float]]
```

Reads a CSV file (UTF-8, first row skipped as header). Returns names and normalised weights (sum = 1.0). If `pattern` is provided, only rows whose name matches `re.match(pattern, name)` are included.

CSV format:
```
name,frequency
Björn,142
Leif,89
```

---

## Helper utilities

### `generators/helpers.py`

```python
def phonetic_match(pattern: str, word: str) -> str | None
```
Applies a phonetic pattern to `word` using `re.match`. `C` → consonant character class, `V` → vowel character class. Returns the matched string or `None`.

```python
def phonetic_search(pattern: str, word: str) -> str | None
```
Same substitutions, but uses `re.search` and strips leading/trailing `.+` from the pattern first. Returns the matched substring or `None`.

```python
def random_choice(counter: dict) -> str | None
```
Weighted random selection from a `{item: weight}` dict. Returns `None` for empty dicts.

### `helpers/str_utils.py`

> **Dead code** — neither function is currently imported or used.

```python
def smart_join(lst: list[str]) -> str
```
Joins a list with commas and `"and"` before the last element. Empty list → `''`.

```python
def overlap(string1: str, string2: str) -> int
```
Returns the length of the longest suffix of `string1` that matches a prefix of `string2`.
