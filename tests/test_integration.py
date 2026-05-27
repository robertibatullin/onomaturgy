"""
Integration tests that use the real CSV data under setting/.
Run with: pytest -m integration
"""
import pytest
from onomaturgy.generators.simple_name import SimpleNameGenerator
from onomaturgy.generators.personal_name import PersonalNameGenerator
from onomaturgy.generators.tribal_name import TribalNameGenerator
from onomaturgy.generators.place_name import PlaceNameGenerator
from onomaturgy.generators.generator_factory import generator_factory

pytestmark = pytest.mark.integration


class TestSimpleNameGenerator:
    def test_russian_male_given_names_count(self):
        g = SimpleNameGenerator('Russian', gender='male', markov=0.5,
                                pattern=None, name_part_type='given_name')
        g.train()
        assert len(g.generate(10)) == 10

    def test_russian_female_given_names_are_strings(self):
        g = SimpleNameGenerator('Russian', gender='female', markov=0.0,
                                pattern=None, name_part_type='given_name')
        g.train()
        assert all(isinstance(n, str) for n in g.generate(5))

    def test_russian_female_surnames_are_feminine(self):
        # After adding russian_sf.csv, female surnames should end in 'a' or 'aja'
        g = SimpleNameGenerator('Russian', gender='female', markov=0.0,
                                pattern=None, name_part_type='surname')
        g.train()
        result = g.generate(20)
        feminine = sum(1 for n in result if n.endswith('a') or n.endswith('aja'))
        # Allow for indeclinable surnames (~12 % of corpus)
        assert feminine / len(result) >= 0.7

    def test_russian_male_surnames_do_not_end_in_a(self):
        g = SimpleNameGenerator('Russian', gender='male', markov=0.0,
                                pattern=None, name_part_type='surname')
        g.train()
        result = g.generate(20)
        # Masculine surnames end in ov/ev/in/ij etc., not bare 'a'/'aja'
        ending_in_a = sum(1 for n in result
                         if n.endswith('ova') or n.endswith('eva')
                         or n.endswith('ina') or n.endswith('aja'))
        assert ending_in_a == 0

    def test_multi_language_generates_names(self):
        g = SimpleNameGenerator('Norwegian', 'Danish', gender='male',
                                markov=0.5, pattern=None, name_part_type='given_name')
        g.train()
        assert len(g.generate(5)) > 0

    def test_no_repeat_produces_unique_names(self):
        g = SimpleNameGenerator('Russian', gender='male', markov=0.5,
                                pattern=None, name_part_type='given_name')
        g.train()
        result = g.generate(10, no_repeat=True)
        assert len(result) == len(set(result))

    def test_max_characters_constraint_respected(self):
        g = SimpleNameGenerator('Russian', gender='male', markov=0.0,
                                pattern=None, name_part_type='given_name',
                                max_characters=6)
        g.train()
        result = g.generate(10)
        assert all(len(n) <= 6 for n in result)


class TestPersonalNameGenerator:
    def test_russian_full_name_count(self):
        g = PersonalNameGenerator(
            'Russian',
            name_pattern=['given_name', 'patronymic', 'surname'],
            markov={'given_name': 0.5, 'patronymic': 0.0, 'surname': 0.5},
        )
        g.train()
        assert len(g.generate(10, female_fraction=0.5)) == 10

    def test_full_name_has_three_parts(self):
        g = PersonalNameGenerator(
            'Russian',
            name_pattern=['given_name', 'patronymic', 'surname'],
            markov={'given_name': 0.5, 'patronymic': 0.0, 'surname': 0.5},
        )
        g.train()
        result = g.generate(5, female_fraction=0.5)
        assert all(len(n.split()) == 3 for n in result)

    def test_all_male_when_female_fraction_zero(self):
        g = PersonalNameGenerator(
            'Russian',
            name_pattern=['given_name', 'patronymic', 'surname'],
            markov={'given_name': 0.0, 'patronymic': 0.0, 'surname': 0.0},
        )
        g.train()
        result = g.generate(10, female_fraction=0.0)
        # Male patronymics end in 'ich' or 'vich'
        patronymics = [n.split()[1] for n in result]
        assert all(p.endswith('ich') for p in patronymics)

    def test_all_female_when_female_fraction_one(self):
        g = PersonalNameGenerator(
            'Russian',
            name_pattern=['given_name', 'patronymic', 'surname'],
            markov={'given_name': 0.0, 'patronymic': 0.0, 'surname': 0.0},
        )
        g.train()
        result = g.generate(10, female_fraction=1.0)
        # Female patronymics end in 'na' (e.g. Ivanovna, Petrovna)
        patronymics = [n.split()[1] for n in result]
        assert all(p.endswith('na') for p in patronymics)

    def test_female_surnames_are_feminine_form(self):
        g = PersonalNameGenerator(
            'Russian',
            name_pattern=['given_name', 'surname'],
            markov={'given_name': 0.0, 'surname': 0.0},
        )
        g.train()
        result = g.generate(15, female_fraction=1.0)
        surnames = [n.split()[1] for n in result]
        feminine = sum(1 for s in surnames if s.endswith('a') or s.endswith('aja'))
        assert feminine / len(surnames) >= 0.7


class TestTribalNameGenerator:
    def test_germanic_generates_names(self):
        g = TribalNameGenerator('Germanic', markov=0.5, pattern=None)
        g.train()
        assert len(g.generate(8)) > 0

    def test_celtic_generates_names(self):
        g = TribalNameGenerator('Celtic', markov=0.5, pattern=None)
        g.train()
        assert len(g.generate(8)) > 0

    def test_corpus_only_results_from_corpus(self):
        from onomaturgy.helpers.csv_loaders import load_names_with_weights
        from onomaturgy.generators.tribal_name import get_ethnonym_paths
        paths = get_ethnonym_paths(['Germanic'])
        corpus = set()
        for p in paths:
            names, _ = load_names_with_weights(p)
            corpus.update(names)
        g = TribalNameGenerator('Germanic', markov=0.0, pattern=None)
        g.train()
        result = g.generate(10, no_repeat=False)
        assert all(n in corpus for n in result)


class TestPlaceNameGenerator:
    def test_english_generates_names(self):
        g = PlaceNameGenerator('English', pattern=None, place_categories=[])
        g.train()
        assert len(g.generate(8)) > 0

    def test_results_are_strings(self):
        g = PlaceNameGenerator('English', pattern=None, place_categories=[])
        g.train()
        assert all(isinstance(n, str) for n in g.generate(5))

    def test_max_word_parts_one_returns_bare_words(self):
        g = PlaceNameGenerator('English', pattern=None,
                               place_categories=[], max_word_parts=1)
        g.train()
        result = g.generate(5)
        assert all(' ' not in n for n in result)

    def test_category_filter_accepted(self):
        g = PlaceNameGenerator('English', pattern=None,
                               place_categories=['populated place'])
        g.train()
        assert len(g.generate(5)) > 0


class TestGeneratorFactoryCaching:
    def _config(self):
        return {
            'name': 'test_tribal',
            'class': 'TribalNameGenerator',
            'languages': 'Germanic',
            'markov': 0.0,
            'pattern': None,
        }

    def test_factory_returns_trained_generator(self):
        gen = generator_factory(self._config(), {})
        assert gen.is_trained is True

    def test_same_config_returns_cached_instance(self):
        context = {}
        gen1 = generator_factory(self._config(), context)
        gen2 = generator_factory(self._config(), context)
        assert gen1 is gen2

    def test_different_config_returns_new_instance(self):
        context = {}
        cfg1 = self._config()
        cfg2 = {**self._config(), 'name': 'other', 'languages': 'Celtic'}
        gen1 = generator_factory(cfg1, context)
        gen2 = generator_factory(cfg2, context)
        assert gen1 is not gen2
