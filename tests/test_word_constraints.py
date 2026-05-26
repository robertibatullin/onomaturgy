from generators.word_constraints import (
    count_word_parts,
    count_syllables,
    WordExtremes,
    WordConstraints,
)


class TestCountWordParts:
    def test_single_word(self):
        assert count_word_parts('hello') == 1

    def test_two_parts_space(self):
        assert count_word_parts('hello world') == 2

    def test_two_parts_hyphen(self):
        assert count_word_parts('hello-world') == 2

    def test_three_parts_mixed_separators(self):
        assert count_word_parts('a b-c') == 3

    def test_empty_string_counts_as_one(self):
        assert count_word_parts('') == 1


class TestCountSyllables:
    def test_single_vowel(self):
        assert count_syllables('a') == 1

    def test_consonant_then_vowel(self):
        assert count_syllables('be') == 1

    def test_two_syllables(self):
        assert count_syllables('hello') == 2

    def test_adjacent_vowels_count_as_one(self):
        assert count_syllables('ee') == 1

    def test_no_vowels(self):
        assert count_syllables('str') == 0

    def test_multiple_vowel_clusters(self):
        # b-eau-t-i-f-u-l → clusters: eau(1) i(1) u(1) = 3
        assert count_syllables('beautiful') == 3


class TestWordExtremes:
    def test_initial_defaults(self):
        e = WordExtremes()
        assert e.max_characters == 0
        assert e.min_characters == 10_000

    def test_update_sets_both_extremes_for_first_word(self):
        e = WordExtremes()
        e.update('hello')
        assert e.max_characters == 5
        assert e.min_characters == 5

    def test_update_tracks_max(self):
        e = WordExtremes()
        e.update('hi')
        e.update('hello')
        assert e.max_characters == 5

    def test_update_tracks_min(self):
        e = WordExtremes()
        e.update('hi')
        e.update('hello')
        assert e.min_characters == 2

    def test_update_tracks_syllable_extremes(self):
        e = WordExtremes()
        e.update('a')      # 1 syllable
        e.update('hello')  # 2 syllables
        assert e.min_syllables == 1
        assert e.max_syllables == 2

    def test_update_tracks_word_part_extremes(self):
        e = WordExtremes()
        e.update('one')
        e.update('two parts')
        assert e.min_word_parts == 1
        assert e.max_word_parts == 2


class TestWordConstraints:
    def test_match_max_passes_within_limit(self):
        assert WordConstraints(max_characters=10).match_max('hello') is True

    def test_match_max_fails_exceeding_limit(self):
        assert WordConstraints(max_characters=3).match_max('hello') is False

    def test_match_max_passes_at_exact_limit(self):
        assert WordConstraints(max_characters=5).match_max('hello') is True

    def test_match_min_passes_within_limit(self):
        assert WordConstraints(min_characters=3).match_min('hello') is True

    def test_match_min_fails_below_limit(self):
        assert WordConstraints(min_characters=10).match_min('hello') is False

    def test_match_min_passes_at_exact_limit(self):
        assert WordConstraints(min_characters=5).match_min('hello') is True

    def test_unconstrained_always_passes_max(self):
        assert WordConstraints().match_max('a' * 1000) is True

    def test_unconstrained_always_passes_min(self):
        assert WordConstraints().match_min('') is True

    def test_max_syllables_constraint(self):
        assert WordConstraints(max_syllables=1).match_max('hello') is False  # 2 syllables
        assert WordConstraints(max_syllables=2).match_max('hello') is True

    def test_min_syllables_constraint(self):
        assert WordConstraints(min_syllables=3).match_min('hello') is False  # 2 syllables
        assert WordConstraints(min_syllables=2).match_min('hello') is True

    def test_max_word_parts_constraint(self):
        assert WordConstraints(max_word_parts=1).match_max('two parts') is False
        assert WordConstraints(max_word_parts=2).match_max('two parts') is True

    def test_update_by_extremes_fills_none_fields(self):
        c = WordConstraints()  # all None
        e = WordExtremes()
        e.update('hi')
        e.update('hello')
        c.update_by_extremes(e)
        assert c.max_characters == 5
        assert c.min_characters == 2

    def test_update_by_extremes_preserves_already_set_fields(self):
        c = WordConstraints(max_characters=100)
        e = WordExtremes()
        e.update('hello')
        c.update_by_extremes(e)
        assert c.max_characters == 100  # not overwritten by extremes value of 5
