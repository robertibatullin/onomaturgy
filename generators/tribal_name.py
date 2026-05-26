"""Tribal / ethnic group name generator backed by ethnonym corpora.

Ethnonym CSV files live under ``setting/csv/ethnonyms/`` and are named
after language families (e.g. ``Germanic.csv``, ``Celtic.csv``).
"""

from generators.word_generator import WordGenerator
from helpers.data_manager import get_path, list_dir


def get_ethnonym_paths(language_families: list[str]) -> list[str]:
    """Return existing CSV paths for the given language families.

    Args:
        language_families: Names of language families (e.g. ``'Germanic'``,
            ``'Slavic'``).  Families without a corresponding CSV are silently
            ignored.

    Returns:
        List of paths to CSV files that exist on disk.
    """
    available = set(list_dir('ethnonyms'))
    return [
        get_path(f'ethnonyms/{family}.csv')
        for family in language_families
        if f'{family}.csv' in available
    ]


class TribalNameGenerator(WordGenerator):
    """Generate plausible tribal or ethnic-group names for a language family.

    Uses the ethnonym corpus for the specified language family/families as
    training data.  Inherits all generation options from
    :class:`~generators.word_generator.WordGenerator`.

    Args:
        *languages: One or more language-family names matching files in
            ``setting/csv/ethnonyms/``.
        markov: Synthesis fraction.
        pattern: Optional phonetic constraint pattern.
        **constraints: Forwarded to
            :class:`~generators.word_constraints.WordConstraints`.
    """

    def __init__(self,
                 *languages: list[str],
                 markov: float,
                 pattern: str | None,
                 **constraints):
        # Paths are resolved lazily in train() so that the data package is
        # not required at construction time.
        super().__init__(markov=markov, pattern=pattern, **constraints)
        self.languages = languages

    def __eq__(self, other: "TribalNameGenerator") -> bool:
        return (
            type(other) is type(self)
            and set(self.languages) == set(other.languages)
            and self.markov == other.markov
            and self.pattern == other.pattern
            and self.constraints == other.constraints
        )

    def train(self):
        """Resolve corpus paths and delegate to :meth:`WordGenerator.train`."""
        self.paths = get_ethnonym_paths(self.languages)
        super().train()
