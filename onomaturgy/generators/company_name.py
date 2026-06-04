"""Company name generator using company-name corpora with optional prefix/suffix words.

Each company name is assembled from three components:

1. A **separate beginning** (e.g. *Global*, *United*) — drawn from
   ``<lang>_separate_beginnings.csv``, or omitted when ``'<NONE>'``.
2. A **main part** — synthesised by a backward Markov chain trained on
   ``<lang>_cleared.csv``.
3. A **separate ending** (e.g. *Group*, *International*) — drawn from
   ``<lang>_separate_endings.csv``, or omitted when ``'<NONE>'``.

Industries (e.g. ``'INDUSTRIALS'``, ``'HEALTH CARE'``) are used to filter
beginnings/endings so the affix vocabulary matches the sector.
"""

import csv
import os
import random

from onomaturgy.generators.base_generator import BaseGenerator
from onomaturgy.generators.word_constraints import WordConstraints
from onomaturgy.generators.markov_chain import MarkovChainWordGenerator
from onomaturgy.helpers.data_manager import get_path, try_get_path


class CompanyNameGenerator(BaseGenerator):
    """Generate company names for one or more languages and industries.

    Args:
        *languages: Language folder names under
            ``companies/namesets/`` in the corpus data package.
        pattern: Optional phonetic suffix/prefix pattern for the main part.
            ``None`` or ``'.+'`` means unconstrained.
        industries: List of industry strings used to filter beginning/ending
            affixes (e.g. ``['INDUSTRIALS', 'MATERIALS']``).
            Pass an empty list to use all industries.
        **constraints: Forwarded to
            :class:`~generators.word_constraints.WordConstraints` for the
            main generated part (e.g. ``max_word_parts=2``).
    """

    def __init__(self,
                 *languages: list[str],
                 pattern: str | None,
                 industries: list[str],
                 **constraints):
        super().__init__()
        self.languages = languages
        self.industries = industries
        self.constraints = WordConstraints(**constraints)
        markov_constraints = constraints.copy()
        max_word_parts_in_main = markov_constraints.get('max_word_parts', 3) - 2
        max_word_parts_in_main = max(1, max_word_parts_in_main)
        markov_constraints['max_word_parts'] = max_word_parts_in_main
        self.pattern = None if pattern == '.+' else pattern
        self.__markov_chain = MarkovChainWordGenerator(
            window=3,
            overlap=2,
            pattern=self.pattern,
            forward=False,
            **markov_constraints)

    def __eq__(self, other: "CompanyNameGenerator"):
        return (
            type(other) is type(self)
            and set(self.languages) == set(other.languages)
            and set(self.industries) == set(other.industries)
            and self.pattern == other.pattern
            and self.constraints == other.constraints
        )

    def __try_read_csv(self, path: str | None, columns: list[str]) -> list[tuple]:
        if path is None:
            return []
        rows = []
        try:
            with open(path, encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    rows.append(tuple(row[c] for c in columns))
        except FileNotFoundError:
            pass
        return rows

    def __load_data(self):
        root = 'companies/namesets'
        self.__names: list[tuple] = []
        self.__begs: list[tuple] = []
        self.__ends: list[tuple] = []
        self.__sep_begs: list[tuple] = []
        self.__sep_ends: list[tuple] = []

        for lang in self.languages:
            names = self.__try_read_csv(
                get_path(f'{root}/{lang}/{lang}_cleared.csv'),
                ['name', 'frequency'])
            self.__names.extend(names)

            begs = self.__try_read_csv(
                get_path(f'{root}/{lang}/{lang}_beginnings.csv'),
                ['beginning', 'industry'])
            if self.industries:
                begs = [r for r in begs if r[1] in self.industries]
            self.__begs.extend(begs)

            ends = self.__try_read_csv(
                get_path(f'{root}/{lang}/{lang}_endings.csv'),
                ['ending', 'industry'])
            if self.industries:
                ends = [r for r in ends if r[1] in self.industries]
            self.__ends.extend(ends)

            sep_begs = self.__try_read_csv(
                try_get_path(f'{root}/{lang}/{lang}_separate_beginnings.csv'),
                ['separate_beginning', 'industry', 'frequency'])
            if self.industries:
                sep_begs = [r for r in sep_begs if r[1] in self.industries]
            self.__sep_begs.extend(sep_begs)

            sep_ends = self.__try_read_csv(
                try_get_path(f'{root}/{lang}/{lang}_separate_endings.csv'),
                ['separate_ending', 'industry', 'frequency'])
            if self.industries:
                sep_ends = [r for r in sep_ends if r[1] in self.industries]
            self.__sep_ends.extend(sep_ends)

        if not self.__sep_begs:
            categories = self.industries or ['<ALL>']
            self.__sep_begs = [('<NONE>', ind, '1') for ind in categories]
        if not self.__sep_ends:
            categories = self.industries or ['<ALL>']
            self.__sep_ends = [('<NONE>', ind, '1') for ind in categories]

    @property
    def names(self) -> list[tuple]:
        """Raw ``(name, frequency)`` rows from ``<lang>_cleared.csv``."""
        return self.__names

    @property
    def beginnings(self) -> list[tuple]:
        """``(beginning, industry)`` rows from ``<lang>_beginnings.csv``."""
        return self.__begs

    @property
    def endings(self) -> list[tuple]:
        """``(ending, industry)`` rows from ``<lang>_endings.csv``."""
        return self.__ends

    @property
    def separate_beginnings(self) -> list[tuple]:
        """``(word, industry, frequency)`` rows from ``<lang>_separate_beginnings.csv``."""
        return self.__sep_begs

    @property
    def separate_endings(self) -> list[tuple]:
        """``(word, industry, frequency)`` rows from ``<lang>_separate_endings.csv``."""
        return self.__sep_ends

    def train(self):
        """Load corpus data and prepare the Markov chain and affix tables."""
        self.__load_data()
        self.__markov_chain.train_on_nameset([name for name, _ in self.__names])
        external_endings = {ending + '#': 10 for ending, _ in self.__ends}
        if len(external_endings) < 50:
            update_size = 50 - len(external_endings)
            self.__markov_chain.endings = {
                e: f for e, f in list(self.__markov_chain.endings.items())[:update_size]}
            self.__markov_chain.endings.update(external_endings)
        if self.industries:
            self.__sep_beg_slices = {
                ind: [(beg, int(freq)) for beg, cat, freq in self.__sep_begs if cat == ind]
                for ind in self.industries
            }
            self.__sep_end_slices = {
                ind: [(end, int(freq)) for end, cat, freq in self.__sep_ends if cat == ind]
                for ind in self.industries
            }
        else:
            self.__sep_beg_slices = {
                '<ALL>': [(beg, int(freq)) for beg, _, freq in self.__sep_begs]
            }
            self.__sep_end_slices = {
                '<ALL>': [(end, int(freq)) for end, _, freq in self.__sep_ends]
            }
        self.is_trained = True

    def generate(self, n: int) -> list[str]:
        """Generate *n* company names.

        Each name is ``[separate_beginning] main [separate_ending]``.
        The separate parts are omitted when the sampled value is ``'<NONE>'``.
        The loop retries until the separate parts do not duplicate each other
        or appear in the main part.

        Trains automatically if :meth:`train` has not been called.

        Args:
            n: Number of company names to generate.

        Returns:
            List of generated company name strings.
        """
        if not self.is_trained:
            self.train()
        main_parts = self.__markov_chain.generate(n, no_repeat=True)
        if self.constraints.max_word_parts == 1:
            return main_parts
        result = []
        for main in main_parts:
            industry = (random.choice(self.industries)
                        if self.industries else '<ALL>')
            sep_beg_slice = self.__sep_beg_slices[industry]
            sep_end_slice = self.__sep_end_slices[industry]
            while True:
                sep_beg = random.choices(
                    [beg for beg, _ in sep_beg_slice],
                    weights=[freq for _, freq in sep_beg_slice], k=1
                )[0]
                sep_end = random.choices(
                    [end for end, _ in sep_end_slice],
                    weights=[freq for _, freq in sep_end_slice], k=1
                )[0]
                if (
                    (sep_end == '<NONE>' or sep_end != sep_beg)
                    and sep_beg not in main
                    and sep_end not in main
                ):
                    break
            name = '' if sep_beg == '<NONE>' else sep_beg + ' '
            name += main
            name += '' if sep_end == '<NONE>' else ' ' + sep_end
            result.append(name)
        return result
