from onomaturgy.generators.helpers import phonetic_match, phonetic_search, random_choice
from onomaturgy.helpers.csv_loaders import load_names_with_weights


class TestPhoneticMatch:
    def test_cv_prefix_matches_consonant_vowel_start(self):
        assert phonetic_match('CV.+', 'hello') == 'hello'

    def test_cv_suffix_matches_consonant_vowel_end(self):
        # 'lo' = l(consonant) + o(vowel)
        assert phonetic_match('.+CV', 'hello') == 'hello'

    def test_literal_suffix(self):
        assert phonetic_match('.+ing', 'running') == 'running'

    def test_literal_suffix_no_match_returns_none(self):
        assert phonetic_match('.+ing', 'runner') is None

    def test_vowel_only_start_fails_cv(self):
        # 'aa' starts with vowel, not consonant
        assert phonetic_match('CV', 'aa') is None

    def test_pipe_alternatives(self):
        assert phonetic_match('.+ov|.+in', 'ivanov') == 'ivanov'

    def test_returns_full_match_string(self):
        result = phonetic_match('CV.+', 'hello')
        assert isinstance(result, str)


class TestPhoneticSearch:
    def test_finds_cv_within_word(self):
        # 'ro' in 'strong' = r(consonant) + o(vowel)
        assert phonetic_search('CV', 'strong') == 'ro'

    def test_strips_leading_dot_plus_before_searching(self):
        result = phonetic_search('.+CV', 'strong')
        assert result is not None

    def test_strips_trailing_dot_plus_before_searching(self):
        result = phonetic_search('CV.+', 'hello')
        assert result is not None

    def test_no_match_returns_none(self):
        # 'str' contains no vowels, so VV cannot match
        assert phonetic_search('VV', 'str') is None

    def test_returned_match_is_substring(self):
        result = phonetic_search('CV', 'strong')
        assert 'strong'.find(result) != -1


class TestRandomChoice:
    def test_empty_dict_returns_none(self):
        assert random_choice({}) is None

    def test_single_item_always_returned(self):
        assert random_choice({'only': 1}) == 'only'

    def test_result_is_always_a_key(self):
        d = {'a': 1, 'b': 2, 'c': 3}
        for _ in range(50):
            assert random_choice(d) in d

    def test_all_keys_reachable(self):
        d = {'x': 1, 'y': 1, 'z': 1}
        seen = {random_choice(d) for _ in range(300)}
        assert seen == {'x', 'y', 'z'}

    def test_higher_weight_chosen_more_often(self):
        d = {'rare': 1, 'common': 99}
        results = [random_choice(d) for _ in range(500)]
        assert results.count('common') > results.count('rare')


class TestLoadNamesWithWeights:
    def test_returns_names_in_order(self, csv_file):
        path = csv_file([('alice', 10), ('bob', 5)])
        names, _ = load_names_with_weights(path)
        assert names == ['alice', 'bob']

    def test_weights_sum_to_one(self, csv_file):
        path = csv_file([('alice', 3), ('bob', 7)])
        _, weights = load_names_with_weights(path)
        assert abs(sum(weights) - 1.0) < 1e-9

    def test_weights_proportional_to_frequency(self, csv_file):
        path = csv_file([('alice', 1), ('bob', 3)])
        _, weights = load_names_with_weights(path)
        assert abs(weights[1] / weights[0] - 3.0) < 1e-9

    def test_missing_frequency_defaults_to_uniform(self, csv_file):
        path = csv_file([('alice',), ('bob',)], header=('name',))
        _, weights = load_names_with_weights(path)
        assert weights == [0.5, 0.5]

    def test_header_row_not_included_in_names(self, csv_file):
        path = csv_file([('alice', 1)])
        names, _ = load_names_with_weights(path)
        assert 'name' not in names

    def test_pattern_filters_non_matching_names(self, csv_file):
        path = csv_file([('abc', 1), ('abz', 1), ('xyz', 1)])
        names, _ = load_names_with_weights(path, pattern='^ab')
        assert set(names) == {'abc', 'abz'}

    def test_pattern_none_includes_all_names(self, csv_file):
        path = csv_file([('abc', 1), ('xyz', 1)])
        names, _ = load_names_with_weights(path, pattern=None)
        assert len(names) == 2
