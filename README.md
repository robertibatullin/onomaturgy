# Onomaturgy

A Python library for procedurally generating historically-grounded names — personal names, place names, tribal/ethnonymic names, and derived forms (adjectives, country names, dynasty names). Generators are trained on real historical name corpora and combine Markov chain synthesis with weighted corpus sampling.

## Installation

Onomaturgy is split into two packages: the code library and the data package that contains the CSV corpora.

```bash
pip install onomaturgy
pip install onomaturgy-data
```

No other dependencies are required. Python 3.10+ is needed for `X | Y` union type hints.

### Development install (from source)

```bash
git clone https://github.com/robertibatullin/onomaturgy.git
cd onomaturgy
pip install -e .[dev]
```

The `[dev]` extra installs `onomaturgy-data` from the local `onomaturgy_data/` subdirectory so the corpus is available immediately.

## Quick Start

Generators load their corpus lazily on the first `generate()` call (or explicit `train()` call), so construction is always cheap.

### Personal names

```python
from generators.personal_name import PersonalNameGenerator

gen = PersonalNameGenerator(
    'Russian',
    name_pattern=['given_name', 'patronymic', 'surname'],
    markov={'given_name': 0.5, 'patronymic': 0.0, 'surname': 0.5},
)
print(gen.generate(n=5, female_fraction=0.4))
# ['Aleksei Nikolaevich Volkov', 'Darya Ivanovna Sorokina', ...]
```

### Place names

```python
from generators.place_name import PlaceNameGenerator

gen = PlaceNameGenerator(
    'English',
    pattern=None,
    place_categories=['populated place'],
    max_word_parts=3,
)
print(gen.generate(n=5))
# ['Ashford', 'Little Thornton', 'Great Barwick upon Trent', ...]
```

### Tribal / ethnonymic names

```python
from generators.tribal_name import TribalNameGenerator

gen = TribalNameGenerator('Germanic', markov=0.7, pattern=None)
print(gen.generate(n=5))
# ['Marcomanni', 'Thuringi', 'Saxones', ...]
```

### Name transformers

```python
from generators.name_transformers import (
    AdjectiveFromEthnonymGenerator,
    CountryNameFromLatinEthnonymGenerator,
    CountryNameFromNativeEthnonymGenerator,
    DynastyNameGenerator,
)

adj_gen = AdjectiveFromEthnonymGenerator('Saxones')
adj_gen.train()
print(adj_gen.generate(1))   # ['Saxonian', 'Saxonean']

country_gen = CountryNameFromLatinEthnonymGenerator('Saxones')
country_gen.train()
print(country_gen.generate(1))   # ['Saxonia']

native_gen = CountryNameFromNativeEthnonymGenerator('Saxons', language_family='Germanic')
native_gen.train()
print(native_gen.generate(1))   # ['Saxonland', 'Saxonen']

dynasty_gen = DynastyNameGenerator('OldNorse', markov=0.5, pattern=None)
dynasty_gen.train()
print(dynasty_gen.generate(3))   # ['Bjorning', 'Haraling', 'Yngling']
```

### Factory pattern (config-driven)

```python
from generators.generator_factory import generator_factory

context = {}
config = {
    'name': 'my_generator',
    'class': 'SimpleNameGenerator',
    'languages': ['Norwegian', 'Danish'],
    'gender': 'male',
    'markov': 0.6,
    'pattern': None,
    'name_part_type': 'given_name',
}
gen = generator_factory(config, context)
print(gen.generate(n=5))
```

## Available Data

### Personal name languages

| Directory | Covers |
|-----------|--------|
| Abkhazian | Abkhazian |
| Afghan | Afghan |
| Albanian | Albanian |
| AngloSaxon | Anglo-Saxon (given names only) |
| Arabic | Libyan, Syrian |
| Armenian | Armenian |
| Azeri | Azerbaijani (with gendered surnames) |
| Burmese | Burmese |
| Czech | Czech (with gendered surnames) |
| Danish | Danish |
| Dutch | Dutch |
| EarlyByzantine | Early Byzantine (given names only) |
| English | British English |
| Estonian | Estonian |
| Faeroese | Faroese |
| Finnish | Finnish |
| French | French |
| Georgian | Georgian |
| German | German |
| Gothic | Gothic (given names only) |
| Greek | Greek |
| Hungarian | Hungarian |
| Icelandic | Icelandic (given names only) |
| Indian | Indian, Nepali, Sri Lankan |
| Iranian | Iranian |
| Irish | Irish |
| Italian | Italian |
| Kazakh | Kazakh (with gendered surnames) |
| Khmer | Khmer |
| Laotian | Laotian |
| Latvian | Latvian (with gendered surnames) |
| Lithuanian | Lithuanian (with gendered surnames) |
| Malay | Malay |
| Maltese | Maltese |
| Norwegian | Norwegian |
| OldGerman | Frankish (given names only) |
| OldIrish | Old Irish (given names only) |
| OldNorse | Old Norse (given names only) |
| OldWelsh | Old Welsh (given names only) |
| Polish | Polish (with gendered surnames) |
| Portuguese | Brazilian, Portuguese |
| PseudoOldFinnic | Fictional Proto-Finnic (given names only) |
| Romanian | Romanian |
| Russian | Russian (with patronymics and gendered surnames) |
| SerboCroatian | Croatian, Serbian |
| Spanish | Spanish |
| Swedish | Swedish |
| Thai | Thai |
| Turkish | Turkish |
| Uzbek | Uzbek (with gendered surnames) |
| Vietnamese | Vietnamese |

### Toponym languages

Abkhazian, Armenian, Azerbaijani, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, Georgian, German, Gothic, Icelandic, Irish, Latvian, Lithuanian, NorthEastcaucasian, Norwegian, Ossetian, Polish, RomanWest, Scottish, Swedish, Welsh

> **Note:** Basque, Catalan, French, Italian, and Spanish toponym datasets contain only the raw place-name list — the beginnings/endings analysis files have not yet been produced. `PlaceNameGenerator` will raise `ValueError` for those languages until the analysis is complete.

### Ethnonym families

`Baltic`, `Celtic`, `Germanic`, `Slavic`

## Architecture

```
BaseGenerator (abstract)
├── WordGenerator
│   ├── SimpleNameGenerator      — personal name parts
│   │   └── DynastyNameGenerator — adds dynasty suffix
│   └── TribalNameGenerator      — ethnonyms
├── MarkovChainWordGenerator     — Markov synthesis engine
├── WordPicker                   — weighted corpus sampling
├── PlaceNameGenerator           — toponyms with category affixes
├── PersonalNameGenerator        — composes multiple name parts
├── AdjectiveFromEthnonymGenerator
├── CountryNameFromLatinEthnonymGenerator
└── CountryNameFromNativeEthnonymGenerator
```

## Running tests

```bash
# Unit tests only (no corpus data required)
pytest -m "not integration"

# All tests including integration tests (requires onomaturgy-data)
pytest
```
