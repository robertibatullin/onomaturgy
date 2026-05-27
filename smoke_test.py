"""
End-to-end smoke test for all generators.
Run from the repository root:  python smoke_test.py
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')


class _Tee:
    def __init__(self, *files):
        self._files = files
    def write(self, text):
        for f in self._files:
            f.write(text)
    def flush(self):
        for f in self._files:
            f.flush()

_log = open('smoke_test_output.txt', 'w', encoding='utf-8')
sys.stdout = _Tee(sys.stdout, _log)


from onomaturgy.generators.simple_name import SimpleNameGenerator
from onomaturgy.generators.personal_name import PersonalNameGenerator
from onomaturgy.generators.tribal_name import TribalNameGenerator
from onomaturgy.generators.place_name import PlaceNameGenerator

N = 8
PASS = 0
FAIL = 0


def section(title):
    print(f'\n{"=" * 60}')
    print(f'  {title}')
    print(f'{"=" * 60}')


def run(label, gen, **generate_kwargs):
    global PASS, FAIL
    print(f'\n{label}')
    try:
        gen.train()
        results = gen.generate(n=N, **generate_kwargs)
        for r in results:
            print(f'  {r}')
        PASS += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        FAIL += 1


# ── SimpleNameGenerator ───────────────────────────────────────

section('SimpleNameGenerator')

run('Russian male given names (markov=0.5)',
    SimpleNameGenerator('Russian',
                        gender='male', markov=0.5,
                        pattern=None, name_part_type='given_name'))

run('Russian female given names (markov=1.0 — fully synthetic)',
    SimpleNameGenerator('Russian',
                        gender='female', markov=1.0,
                        pattern=None, name_part_type='given_name'))

run('Norwegian + Danish male given names (markov=0.0 — corpus only)',
    SimpleNameGenerator('Norwegian', 'Danish',
                        gender='male', markov=0.0,
                        pattern=None, name_part_type='given_name'))

run('Polish female surnames',
    SimpleNameGenerator('Polish',
                        gender='female', markov=0.5,
                        pattern=None, name_part_type='surname'))

run('Russian patronymics (male)',
    SimpleNameGenerator('Russian',
                        gender='male', markov=0.0,
                        pattern=None, name_part_type='patronymic'))


# ── PersonalNameGenerator ─────────────────────────────────────

section('PersonalNameGenerator')

run('Russian full name: given + patronymic + surname',
    PersonalNameGenerator(
        'Russian',
        name_pattern=['given_name', 'patronymic', 'surname'],
        markov={'given_name': 0.5, 'patronymic': 0.0, 'surname': 0.5},
    ),
    female_fraction=0.4)

run('Polish given + surname (50 % female)',
    PersonalNameGenerator(
        'Polish',
        name_pattern=['given_name', 'surname'],
        markov={'given_name': 0.5, 'surname': 0.5},
    ),
    female_fraction=0.5)

run('Norwegian + Danish given + surname (male only)',
    PersonalNameGenerator(
        'Norwegian', 'Danish',
        name_pattern=['given_name', 'surname'],
        markov={'given_name': 0.5, 'surname': 0.5},
    ),
    female_fraction=0.0)


# ── TribalNameGenerator ───────────────────────────────────────

section('TribalNameGenerator')

run('Germanic tribal names (markov=0.7)',
    TribalNameGenerator('Germanic', markov=0.7, pattern=None))

run('Celtic tribal names (markov=0.5)',
    TribalNameGenerator('Celtic', markov=0.5, pattern=None))

run('Slavic tribal names (markov=0.0 — corpus only)',
    TribalNameGenerator('Slavic', markov=0.0, pattern=None))


# ── PlaceNameGenerator ────────────────────────────────────────

section('PlaceNameGenerator')

run('English populated places (up to 3 word parts)',
    PlaceNameGenerator('English',
                       pattern=None,
                       place_categories=['populated place'],
                       max_word_parts=3))

run('English rivers / streams',
    PlaceNameGenerator('English',
                       pattern=None,
                       place_categories=['stream']))

run('Norwegian all categories',
    PlaceNameGenerator('Norwegian',
                       pattern=None,
                       place_categories=[]))

run('English + Norwegian mixed',
    PlaceNameGenerator('English', 'Norwegian',
                       pattern=None,
                       place_categories=['populated place'],
                       max_word_parts=2))



# ── Summary ───────────────────────────────────────────────────

print(f'\n{"=" * 60}')
print(f'  Results: {PASS} passed, {FAIL} failed')
print(f'{"=" * 60}\n')
