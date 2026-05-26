"""Word-level measurement and filtering utilities.

Provides two helper functions (:func:`count_word_parts`,
:func:`count_syllables`) and two dataclasses:

* :class:`WordExtremes` — accumulates the observed min/max statistics of
  a corpus, used to set default bounds for generation.
* :class:`WordConstraints` — holds the desired min/max limits and tests
  candidate words against them.
"""

from dataclasses import dataclass, asdict

from generators.constants import vowels


def count_word_parts(word: str) -> int:
    """Return the number of space- or hyphen-separated parts in *word*.

    Examples::

        count_word_parts('London')        # → 1
        count_word_parts('New York')      # → 2
        count_word_parts('Stratford-upon-Avon')  # → 3
    """
    return word.count(' ') + word.count('-') + 1


def count_syllables(word: str) -> int:
    """Return the number of syllables in *word*.

    A syllable is counted as one contiguous run of vowel characters
    (including accented forms).  Consecutive vowels count as one syllable.
    """
    for v in vowels:
        word = word.replace(v, '#')
    while '##' in word:
        word = word.replace('##', '#')
    return word.count('#')


@dataclass
class WordExtremes:
    """Running min/max statistics collected while scanning a corpus.

    Call :meth:`update` once per word.  After processing the full corpus
    the attributes hold the true extremes, which can be fed into a
    :class:`WordConstraints` instance via
    :meth:`WordConstraints.update_by_extremes`.
    """

    max_characters: int = 0
    min_characters: int = 10_000
    max_syllables: int = 0
    min_syllables: int = 10_000
    max_word_parts: int = 0
    min_word_parts: int = 10_000

    def update(self, word: str):
        """Extend the running extremes to include *word*."""
        word_parts = count_word_parts(word)
        syllables = count_syllables(word)
        if word_parts > self.max_word_parts:
            self.max_word_parts = word_parts
        if word_parts < self.min_word_parts:
            self.min_word_parts = word_parts
        if syllables > self.max_syllables:
            self.max_syllables = syllables
        if syllables < self.min_syllables:
            self.min_syllables = syllables
        if len(word) > self.max_characters:
            self.max_characters = len(word)
        if len(word) < self.min_characters:
            self.min_characters = len(word)


@dataclass
class WordConstraints:
    """Upper and lower bounds applied when filtering or generating words.

    All attributes default to ``None``, meaning unconstrained.  Only
    non-``None`` bounds are enforced by :meth:`match_max` and
    :meth:`match_min`.

    Attributes:
        max_characters: Maximum allowed character length (inclusive).
        min_characters: Minimum required character length (inclusive).
        max_syllables: Maximum allowed syllable count (inclusive).
        min_syllables: Minimum required syllable count (inclusive).
        max_word_parts: Maximum allowed number of space/hyphen-separated
            parts (inclusive).
        min_word_parts: Minimum required number of parts (inclusive).
    """

    max_characters: int | None = None
    min_characters: int | None = None
    max_syllables: int | None = None
    min_syllables: int | None = None
    max_word_parts: int | None = None
    min_word_parts: int | None = None

    def update_by_extremes(self, extremes: WordExtremes):
        """Fill in any ``None`` attributes from *extremes*.

        Explicit (non-``None``) constraints are never overwritten; only
        attributes that are still ``None`` are set from the corpus extremes.
        """
        for key, value in asdict(extremes).items():
            if getattr(self, key) is None:
                setattr(self, key, value)

    def match_max(self, word: str) -> bool:
        """Return ``True`` if *word* does not exceed any upper bound."""
        if self.max_characters is not None and len(word) > self.max_characters:
            return False
        syllables_count = count_syllables(word)
        if self.max_syllables is not None and syllables_count > self.max_syllables:
            return False
        word_parts_count = count_word_parts(word)
        if self.max_word_parts is not None and word_parts_count > self.max_word_parts:
            return False
        return True

    def match_min(self, word: str) -> bool:
        """Return ``True`` if *word* meets all lower bounds."""
        if self.min_characters is not None and len(word) < self.min_characters:
            return False
        syllables_count = count_syllables(word)
        if self.min_syllables is not None and syllables_count < self.min_syllables:
            return False
        word_parts_count = count_word_parts(word)
        if self.min_word_parts is not None and word_parts_count < self.min_word_parts:
            return False
        return True
