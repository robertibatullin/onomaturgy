"""Corpus-backed word generators combining direct sampling and Markov generation."""

import random

from onomaturgy.generators.base_generator import BaseGenerator
from onomaturgy.helpers.csv_loaders import load_names_with_weights
from onomaturgy.generators.markov_chain import MarkovChainWordGenerator
from onomaturgy.generators.word_constraints import WordConstraints


class WordPicker(BaseGenerator):
    """Pick words at random from a fixed corpus, weighted by frequency.

    Unlike :class:`WordGenerator`, this class does not synthesise new words;
    it only samples from the training set.  It is used internally by
    :class:`WordGenerator` when ``markov < 1``.
    """

    def __init__(self, **constraints):
        """
        Args:
            **constraints: Forwarded to
                :class:`~generators.word_constraints.WordConstraints`.
                Only words that satisfy all constraints are retained.
        """
        super().__init__()
        self.constraints = WordConstraints(**constraints)

    def train(self, names: list[str], weights: list[float]):
        """Filter the corpus by constraints and store it for sampling.

        Args:
            names: List of candidate words.
            weights: Corresponding normalised sampling weights (must sum to 1).
        """
        self.names = []
        self.weights = []
        for n, w in zip(names, weights):
            if self.constraints.match_max(n) and self.constraints.match_min(n):
                self.names.append(n)
                self.weights.append(w)
        self.is_trained = True

    def generate(self, n: int, no_repeat: bool) -> list[str]:
        """Sample *n* words from the corpus.

        Args:
            n: Number of words to return.
            no_repeat: If ``True``, return only distinct words (sampling
                with up to ``10 * n`` attempts).

        Returns:
            Sorted list of sampled words.
        """
        if not no_repeat:
            return random.choices(self.names, weights=self.weights, k=n)
        result = set()
        n_trials = 0
        while len(result) < n and n_trials < 10 * n:
            n_trials += 1
            selected = random.choices(self.names, weights=self.weights, k=n)
            result.update(set(selected))
        return sorted(result)


class WordGenerator(BaseGenerator):
    """Generate words by blending corpus sampling with Markov synthesis.

    Each call to :meth:`generate` mixes two strategies controlled by the
    *markov* ratio:

    * ``markov=0`` — pure corpus sampling via :class:`WordPicker`.
    * ``markov=1`` — all words are synthesised by
      :class:`~generators.markov_chain.MarkovChainWordGenerator`.
    * ``0 < markov < 1`` — each word is independently drawn from either
      strategy with probability *markov*.

    Args:
        *paths: Paths to UTF-8 CSV name files (``name[,frequency]`` format).
        markov: Fraction of words to synthesise.  Must be in ``[0, 1]``.
        pattern: Optional phonetic pattern (see
            :mod:`generators.helpers`).  For ``markov > 0`` each
            pipe-separated sub-pattern must start or end with ``".+"``.
            Pass ``None`` for unconstrained output.  The degenerate pattern
            ``".+"`` is treated as ``None``.
        **constraints: Forwarded to
            :class:`~generators.word_constraints.WordConstraints`.
    """

    def __init__(self,
                 *paths: list[str],
                 markov: float,
                 pattern: str | None,
                 **constraints
                 ):
        super().__init__()
        self.paths = paths
        self.markov = markov
        self.pattern = None if pattern == '.+' else pattern
        self.constraints = constraints

    def __eq__(self, other: "WordGenerator"):
        return (
            type(other) is type(self)
            and set(self.paths) == set(other.paths)
            and self.markov == other.markov
            and self.pattern == other.pattern
            and self.constraints == other.constraints
        )
    
    def train_on_nameset(self,
                         names: list[str],
                         weights: list[int|float]):
        """Initialise the internal sampler and/or Markov chain from raw data.

        Called by :meth:`train`; can also be called directly when the corpus
        is already loaded in memory (e.g. by :class:`PersonalNameGenerator`).

        Args:
            names: Training words.
            weights: Corresponding sampling weights (need not be normalised).
        """
        if self.markov > 0:
            self.__markov_chain_generator = MarkovChainWordGenerator(
                window=3,
                overlap=2,
                pattern=self.pattern,
                forward=True,
                **self.constraints
                )
            self.__markov_chain_generator.train_on_nameset(names)
        if self.markov < 1:
            self.__word_picker = WordPicker(**self.constraints)
            self.__word_picker.train(names, weights)

    def train(self):
        """Load all CSV corpora and prepare for generation.

        Raises:
            ValueError: If no names pass the pattern filter across all paths.
        """
        names, weights = [], []
        for path in self.paths:
            n, w = load_names_with_weights(path, self.pattern)
            names.extend(n)
            weights.extend(w)
        if len(names) == 0:
            raise ValueError('Empty training set')
        self.train_on_nameset(names, weights)
        self.is_trained = True

    def equalize_weights(self):
        """Reset all corpus sampling weights to uniform (1 each).

        Useful when the frequency data in the CSV would cause the same
        high-frequency names to dominate output; call this after
        :meth:`train` to treat all corpus entries as equally likely.
        """
        self.__word_picker.weights = [1] * len(self.__word_picker.weights)

    def generate(self,
                 n: int,
                 no_repeat: bool = True
                 ) -> list[str]:
        """Generate *n* words using the configured mix of sampling and synthesis.

        Trains automatically if :meth:`train` has not yet been called.

        Args:
            n: Desired number of words.
            no_repeat: Exclude corpus words and duplicates when ``True``.

        Returns:
            Sorted list of up to *n* words.
        """
        if not self.is_trained:
            self.train()
        result = set()
        n_trials = 0
        while len(result) < n and n_trials < 10 * n:
            n_trials += 1
            use_markov = random.random() < self.markov
            if use_markov:
                words = self.__markov_chain_generator.generate(n, no_repeat=no_repeat)
            else:
                words = self.__word_picker.generate(n, no_repeat=no_repeat)
            result.update(words)
        result = list(result)[:n]
        return sorted(result)
