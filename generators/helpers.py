"""Utility functions for phonetic pattern matching and weighted random selection.

Phonetic patterns extend regular expressions with two special tokens:

* ``C`` — matches any consonant in :data:`generators.constants.consonants`.
* ``V`` — matches any vowel in :data:`generators.constants.vowels`.

Patterns used by the Markov chain generators must either start *or* end
with ``".+"`` (the free-match anchor) but not both.  For example:

* ``".+ing"`` — word must end with *ing*.
* ``"al.+"`` — word must start with *al*.
* ``".+CVa"`` — word must end with a consonant + vowel + *a*.
"""

import re
import random

from generators.constants import vowels, consonants


def phonetic_match(pattern: str, word: str) -> str | None:
    """Attempt a full ``re.match`` of *pattern* against *word*.

    ``C`` and ``V`` in *pattern* are expanded to character classes covering
    consonants and vowels respectively before matching.

    Args:
        pattern: A regex pattern, optionally using ``C`` / ``V`` tokens.
        word: The candidate word to test.

    Returns:
        The matched string if the pattern matches from the start of *word*,
        otherwise ``None``.
    """
    pattern = pattern.replace('C', '#')
    pattern = pattern.replace('V', '%')
    pattern = pattern.replace('#', f'[{consonants}]')
    pattern = pattern.replace('%', f'[{vowels}]')
    match = re.match(pattern, word)
    if match is None:
        return None
    return match.group(0)


def phonetic_search(pattern: str, word: str) -> str | None:
    """Search for *pattern* anywhere inside *word*.

    Unlike :func:`phonetic_match`, the leading/trailing ``".+"`` anchor is
    stripped before the search so that only the fixed portion is looked up.

    Args:
        pattern: A pattern using the same ``C`` / ``V`` syntax as
            :func:`phonetic_match`, optionally prefixed or suffixed with
            ``".+"``.
        word: The string to search in.

    Returns:
        The matched substring, or ``None`` if not found.
    """
    pattern = pattern.strip('.+')
    pattern = pattern.replace('C', '#')
    pattern = pattern.replace('V', '%')
    pattern = pattern.replace('#', f'[{consonants}]')
    pattern = pattern.replace('%', f'[{vowels}]')
    match = re.search(pattern, word)
    if match is None:
        return None
    return match.group(0)


def random_choice(counter: dict) -> str | None:
    """Pick a random key from *counter* weighted by its values.

    Args:
        counter: A ``{item: weight}`` mapping.  Weights must be numeric and
            positive.

    Returns:
        A randomly selected key, or ``None`` if *counter* is empty.
    """
    if len(counter) == 0:
        return None
    return random.choices(
        list(counter.keys()),
        weights=list(counter.values()),
        k=1
    )[0]
