"""Single-part name generator backed by language-specific CSV corpora.

CSV files for a given language live under ``names/<Language>/`` in the
corpus data package.  File names must end with one of the suffixes
recognised by :func:`get_nameset_paths` (e.g. ``_m.csv``,
``_sf.csv``).  Multiple files matching the suffix are all loaded and
merged.
"""

from enum import Enum, auto
import os

from generators.word_generator import WordGenerator
from helpers.data_manager import get_path, list_dir


class NamePartType(Enum):
    """The structural role of a name component within a full personal name."""

    GIVEN_NAME = auto()
    SURNAME = auto()
    PATRONYMIC = auto()
    METRONYMIC = auto()


def get_nameset_paths(
        languages: list[str],
        name_part_type: NamePartType,
        gender: str,
        ) -> list[str]:
    """Return all CSV paths for the given language(s), name-part type, and gender.

    Files are discovered by scanning each language directory under
    ``names/`` in the corpus data package and retaining those whose base
    name ends with one of the expected suffixes:

    ============================  ==================
    (name_part_type, gender)      accepted suffixes
    ============================  ==================
    GIVEN_NAME, male              ``_m``
    GIVEN_NAME, female            ``_f``
    SURNAME, male                 ``_sm``, ``_s``
    SURNAME, female               ``_sf``, ``_s``
    PATRONYMIC, male              ``_pm``
    PATRONYMIC, female            ``_pf``
    METRONYMIC, male              ``_mm``
    METRONYMIC, female            ``_mf``
    ============================  ==================

    Args:
        languages: Language folder names (e.g. ``['Russian', 'Polish']``).
        name_part_type: The part of the name to source.
        gender: ``'male'`` or ``'female'``.

    Returns:
        List of matching CSV file paths.
    """
    filename_suffixes = {
        (NamePartType.GIVEN_NAME, 'male'): ('_m'),
        (NamePartType.GIVEN_NAME, 'female'): ('_f'),
        (NamePartType.SURNAME, 'male'): ('_sm', '_s'),
        (NamePartType.SURNAME, 'female'): ('_sf', '_s'),
        (NamePartType.PATRONYMIC, 'male'): ('_pm'),
        (NamePartType.PATRONYMIC, 'female'): ('_pf'),
        (NamePartType.METRONYMIC, 'male'): ('_mm'),
        (NamePartType.METRONYMIC, 'female'): ('_mf'),
    }.get((name_part_type, gender))
    paths = []
    for language in languages:
        for filename in list_dir(f'names/{language}'):
            fname, ext = os.path.splitext(filename)
            if fname.endswith(filename_suffixes) and ext == '.csv':
                paths.append(get_path(f'names/{language}/{filename}'))
    return paths


class SimpleNameGenerator(WordGenerator):
    """Generate one name part (given name, surname, patronymic, or metronymic).

    Wraps :class:`~generators.word_generator.WordGenerator` with automatic
    corpus path resolution based on language, gender, and name-part type.

    Args:
        *languages: One or more language names (e.g. ``'Russian'``,
            ``'Norwegian'``).  Corpora for all listed languages are merged.
        gender: ``'male'`` or ``'female'``.
        markov: Synthesis fraction — see :class:`~generators.word_generator.WordGenerator`.
        pattern: Optional phonetic pattern — see :mod:`generators.helpers`.
        name_part_type: Which name component to generate.  Accepts a
            :class:`NamePartType` enum value or its string name (e.g.
            ``'given_name'``, ``'surname'``).
        **constraints: Forwarded to
            :class:`~generators.word_constraints.WordConstraints`.
    """

    def __init__(self,
                 *languages: list[str],
                 gender: str,
                 markov: float,
                 pattern: str | None,
                 name_part_type: str | NamePartType,
                 **constraints
                ):
        if isinstance(name_part_type, str):
            name_part_type = NamePartType[name_part_type.upper()]
        # Paths are resolved lazily in train() so that the data package is
        # not required at construction time.
        super().__init__(markov=markov, pattern=pattern, **constraints)
        self.languages = languages
        self.gender = gender
        self.name_part_type = name_part_type

    def __eq__(self, other: "SimpleNameGenerator") -> bool:
        return (
            type(other) is type(self)
            and set(self.languages) == set(other.languages)
            and self.gender == other.gender
            and self.name_part_type == other.name_part_type
            and self.markov == other.markov
            and self.pattern == other.pattern
            and self.constraints == other.constraints
        )

    def train(self):
        """Resolve corpus paths and delegate to :meth:`WordGenerator.train`."""
        self.paths = get_nameset_paths(self.languages, self.name_part_type, self.gender)
        super().train()
