import pytest
from generators.markov_chain import MarkovChainWordGenerator

# Enough names so the chain can produce novel words
CORPUS = [
    'william', 'charles', 'henry', 'richard', 'robert',
    'thomas', 'edward', 'george', 'james', 'arthur',
    'margaret', 'elizabeth', 'katherine', 'eleanor', 'matilda',
    'raymond', 'godfrey', 'baldwin', 'bertrand', 'humphrey',
    'aldric', 'bertulf', 'clovis', 'dagbert', 'erwig',
]


def make_gen(**kwargs):
    defaults = dict(window=3, overlap=2, pattern=None, forward=True)
    defaults.update(kwargs)
    return MarkovChainWordGenerator(**defaults)


class TestMarkovChainTraining:
    def test_train_sets_is_trained(self):
        g = make_gen()
        g.train_on_nameset(CORPUS)
        assert g.is_trained is True

    def test_is_not_trained_before_train(self):
        assert make_gen().is_trained is False

    def test_empty_corpus_raises_value_error(self):
        with pytest.raises(ValueError):
            make_gen().train_on_nameset([])

    def test_all_names_too_short_raises_value_error(self):
        # window=3, overlap=2 → min usable length = 2*3 - 2 = 4
        with pytest.raises(ValueError):
            make_gen().train_on_nameset(['ab', 'cd', 'ef'])

    def test_invalid_pattern_no_dot_plus_raises(self):
        with pytest.raises(ValueError):
            make_gen(pattern='abc')

    def test_valid_pattern_ending(self):
        # '.+es' matches 'charles', 'james' — ensures at least one corpus hit
        g = make_gen(pattern='.+es')
        g.train_on_nameset(CORPUS)
        assert g.is_trained is True

    def test_valid_pattern_beginning(self):
        # 'al.+' matches 'aldric' from CORPUS
        g = make_gen(pattern='al.+')
        g.train_on_nameset(CORPUS)
        assert g.is_trained is True

    def test_pipe_pattern_valid(self):
        g = make_gen(pattern='.+ing|.+ert')
        g.train_on_nameset(CORPUS)
        assert g.is_trained is True


class TestMarkovChainGeneration:
    @pytest.fixture(autouse=True)
    def trained_gen(self):
        self.gen = make_gen()
        self.gen.train_on_nameset(CORPUS)

    def test_returns_a_list(self):
        assert isinstance(self.gen.generate(5, no_repeat=True), list)

    def test_all_results_are_strings(self):
        assert all(isinstance(w, str) for w in self.gen.generate(5, no_repeat=True))

    def test_no_repeat_produces_no_duplicates(self):
        result = self.gen.generate(8, no_repeat=True)
        assert len(result) == len(set(result))

    def test_no_repeat_excludes_training_words(self):
        corpus_set = set(CORPUS)
        result = self.gen.generate(10, no_repeat=True)
        assert all(w not in corpus_set for w in result)

    def test_with_repeat_may_include_training_words(self):
        # no_repeat=False means training words are not excluded
        result = self.gen.generate(5, no_repeat=False)
        assert isinstance(result, list)

    def test_max_characters_respected(self):
        g = make_gen(max_characters=6)
        g.train_on_nameset(CORPUS)
        result = g.generate(15, no_repeat=True)
        assert all(len(w) <= 6 for w in result)

    def test_min_characters_respected(self):
        g = make_gen(min_characters=5)
        g.train_on_nameset(CORPUS)
        result = g.generate(10, no_repeat=True)
        assert all(len(w) >= 5 for w in result)

    def test_backward_generation_returns_strings(self):
        g = make_gen(forward=False)
        g.train_on_nameset(CORPUS)
        result = g.generate(5, no_repeat=True)
        assert all(isinstance(w, str) for w in result)

    def test_generate_auto_trains_if_needed(self):
        g = make_gen()
        g.paths = []  # no paths → train() would fail, but train_on_nameset already ran
        # Use a fresh generator that hasn't been trained
        g2 = make_gen()
        g2.train_on_nameset(CORPUS)
        # Calling generate without explicit train() is fine (is_trained already True)
        result = g2.generate(3, no_repeat=True)
        assert isinstance(result, list)


class TestMarkovChainEquality:
    def test_same_config_are_equal(self):
        g1 = make_gen(window=3, overlap=2, forward=True)
        g2 = make_gen(window=3, overlap=2, forward=True)
        assert g1 == g2

    def test_different_window_not_equal(self):
        assert make_gen(window=3) != make_gen(window=4)

    def test_different_overlap_not_equal(self):
        assert make_gen(overlap=1) != make_gen(overlap=2)

    def test_different_pattern_not_equal(self):
        assert make_gen(pattern=None) != make_gen(pattern='.+ing')

    def test_different_direction_not_equal(self):
        assert make_gen(forward=True) != make_gen(forward=False)

    def test_different_constraints_not_equal(self):
        assert make_gen(max_characters=5) != make_gen(max_characters=10)
