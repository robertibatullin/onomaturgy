import pytest
from generators.word_generator import WordPicker, WordGenerator

NAMES = ['alice', 'bob', 'carol', 'dave', 'eve', 'frank', 'grace', 'henry']
WEIGHTS = [1 / len(NAMES)] * len(NAMES)


class TestWordPicker:
    def test_is_not_trained_before_train(self):
        assert WordPicker().is_trained is False

    def test_train_sets_is_trained(self):
        p = WordPicker()
        p.train(NAMES, WEIGHTS)
        assert p.is_trained is True

    def test_generate_returns_list(self):
        p = WordPicker()
        p.train(NAMES, WEIGHTS)
        assert isinstance(p.generate(3, no_repeat=True), list)

    def test_generate_results_come_from_corpus(self):
        p = WordPicker()
        p.train(NAMES, WEIGHTS)
        result = p.generate(4, no_repeat=False)
        assert all(n in NAMES for n in result)

    def test_no_repeat_produces_no_duplicates(self):
        p = WordPicker()
        p.train(NAMES, WEIGHTS)
        result = p.generate(6, no_repeat=True)
        assert len(result) == len(set(result))

    def test_with_repeat_can_return_duplicates(self):
        p = WordPicker()
        p.train(NAMES, WEIGHTS)
        # Request more than corpus size; with no_repeat=False duplicates are allowed
        result = p.generate(20, no_repeat=False)
        assert len(result) == 20

    def test_max_characters_filters_long_names(self, csv_file):
        # 'alice'=5, 'bob'=3 → max 3 keeps only 'bob'
        p = WordPicker(max_characters=3)
        p.train(['alice', 'bob'], [0.5, 0.5])
        result = p.generate(5, no_repeat=False)
        assert all(len(n) <= 3 for n in result)


class TestWordGenerator:
    def test_is_not_trained_before_train(self, csv_file):
        path = csv_file([(n, 1) for n in NAMES])
        g = WordGenerator(path, markov=0.0, pattern=None)
        assert g.is_trained is False

    def test_train_sets_is_trained(self, csv_file):
        path = csv_file([(n, 1) for n in NAMES])
        g = WordGenerator(path, markov=0.0, pattern=None)
        g.train()
        assert g.is_trained is True

    def test_corpus_only_results_come_from_corpus(self, csv_file):
        path = csv_file([(n, 1) for n in NAMES])
        g = WordGenerator(path, markov=0.0, pattern=None)
        g.train()
        result = g.generate(4, no_repeat=False)
        assert all(n in NAMES for n in result)

    def test_markov_only_generates_strings(self, csv_file):
        path = csv_file([(n, 1) for n in NAMES])
        g = WordGenerator(path, markov=1.0, pattern=None)
        g.train()
        result = g.generate(3, no_repeat=True)
        assert all(isinstance(n, str) for n in result)

    def test_empty_csv_raises_value_error(self, csv_file):
        path = csv_file([])  # header only, no data rows
        g = WordGenerator(path, markov=0.0, pattern=None)
        with pytest.raises(ValueError, match='Empty training set'):
            g.train()

    def test_dot_plus_pattern_normalised_to_none(self, csv_file):
        path = csv_file([(n, 1) for n in NAMES])
        g = WordGenerator(path, markov=0.0, pattern='.+')
        assert g.pattern is None

    def test_generate_auto_calls_train(self, csv_file):
        path = csv_file([(n, 1) for n in NAMES])
        g = WordGenerator(path, markov=0.0, pattern=None)
        result = g.generate(3)  # no explicit train()
        assert g.is_trained is True
        assert isinstance(result, list)


class TestWordGeneratorEquality:
    def test_same_config_equal(self, csv_file):
        path = csv_file([(n, 1) for n in NAMES])
        g1 = WordGenerator(path, markov=0.5, pattern=None)
        g2 = WordGenerator(path, markov=0.5, pattern=None)
        assert g1 == g2

    def test_different_markov_not_equal(self, csv_file):
        path = csv_file([(n, 1) for n in NAMES])
        assert (WordGenerator(path, markov=0.5, pattern=None)
                != WordGenerator(path, markov=1.0, pattern=None))

    def test_different_pattern_not_equal(self, csv_file):
        path = csv_file([(n, 1) for n in NAMES])
        assert (WordGenerator(path, markov=0.5, pattern=None)
                != WordGenerator(path, markov=0.5, pattern='.+ing'))

    def test_different_paths_not_equal(self, csv_file):
        path1 = csv_file([(n, 1) for n in NAMES])
        path2 = csv_file([(n, 1) for n in NAMES[:4]], )
        assert (WordGenerator(path1, markov=0.5, pattern=None)
                != WordGenerator(path2, markov=0.5, pattern=None))

    def test_different_constraints_not_equal(self, csv_file):
        path = csv_file([(n, 1) for n in NAMES])
        assert (WordGenerator(path, markov=0.5, pattern=None, max_characters=5)
                != WordGenerator(path, markov=0.5, pattern=None, max_characters=10))
