"""Full personal name generator that combines multiple name parts.

Builds one :class:`~generators.simple_name.SimpleNameGenerator` per
(name-part, gender) pair at training time, then assembles complete names
by sampling each part in sequence with a consistent gender.
"""

import random

from onomaturgy.generators.simple_name import NamePartType, SimpleNameGenerator
from onomaturgy.generators.base_generator import BaseGenerator


class PersonalNameGenerator(BaseGenerator):
    """Generate complete personal names with gender-consistent parts.

    Each name is constructed by concatenating the parts listed in
    *name_pattern* (e.g. given name → patronymic → surname), where every
    part is drawn from the sub-generator that matches the randomly chosen
    gender for that name.

    Args:
        *languages: Language names whose corpora are merged for every part.
        name_pattern: Ordered list of name parts to include, e.g.
            ``['given_name', 'patronymic', 'surname']``.  Each entry must be
            a :class:`~generators.simple_name.NamePartType` or its lowercase
            string equivalent.
        markov: Per-part Markov synthesis fraction, e.g.
            ``{'given_name': 0.5, 'surname': 0.0}``.
        name_part_patterns: Optional per-part phonetic pattern, e.g.
            ``{'surname': '.+ov|.+ev'}``.  Parts without an entry are
            unconstrained.
    """

    def __init__(self,
                 *languages: list[str],
                 name_pattern: list[str | NamePartType],
                 markov: dict[NamePartType, float],
                 name_part_patterns: dict[NamePartType, str] | None = None
    ):
        super().__init__()
        self.languages = languages
        self.name_pattern = name_pattern
        self.markov = markov
        if name_part_patterns is None:
            name_part_patterns = {}
        self.name_part_patterns = name_part_patterns
        self.name_part_generators = {}

    def __eq__(self, other: "PersonalNameGenerator") -> bool:
        return (
            type(other) is type(self)
            and set(self.languages) == set(other.languages)
            and self.name_pattern == other.name_pattern
            and self.markov == other.markov
            and self.name_part_patterns == other.name_part_patterns
        )

    def train(self):
        """Train one :class:`~generators.simple_name.SimpleNameGenerator` per
        (name-part, gender) combination."""
        self.__name_part_generators = {}
        for name_part in set(self.name_pattern):
            self.__name_part_generators[name_part] = {}
            for gender in ('male', 'female'):
                g = SimpleNameGenerator(
                    *self.languages,
                    markov=self.markov[name_part],
                    pattern=self.name_part_patterns.get(name_part),
                    gender=gender,
                    name_part_type=name_part,
                    )
                g.train()
                self.__name_part_generators[name_part][gender] = g
        self.is_trained = True

    def generate(self,
                 n: int,
                 female_fraction: float,
                ) -> list[str]:
        """Generate *n* full names with the requested gender balance.

        Trains automatically if :meth:`train` has not yet been called.

        Args:
            n: Number of full names to generate.
            female_fraction: Probability (0–1) that any individual name is
                female.  Use ``0.5`` for equal split, ``0.0`` for all male.

        Returns:
            Sorted list of space-joined full names.
        """
        if not self.is_trained:
            self.train()
        result = set()
        while len(result) < n:
            full_name = []
            gender = 'female' if random.random() < female_fraction else 'male'
            for name_part in self.name_pattern:
                name_part = self.__name_part_generators[
                    name_part][gender].generate(1)[0]
                full_name.append(name_part)
            result.add(' '.join(full_name))
        result = list(result)[:n]
        return sorted(result)
