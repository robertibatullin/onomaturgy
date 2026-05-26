"""Rule-based generators that derive new names from existing ethnonyms.

All four classes in this module apply deterministic morphological rules
to a single input word and return the derived forms.  Because no corpus
is needed, :meth:`train` is a no-op that simply sets :attr:`is_trained`.
"""

from generators.constants import vowels
from generators.base_generator import BaseGenerator
from generators.simple_name import SimpleNameGenerator


class AdjectiveFromEthnonymGenerator(BaseGenerator):
    """Derive an adjective (or adjectives) from a Latin or English ethnonym.

    Applies suffix-substitution rules modelled on common Latinate and
    English patterns:

    ============  ===================================
    Ending        Derived form(s)
    ============  ===================================
    ``-ii``       ``-ian``  (e.g. *Germanii → Germanian*)
    ``-i``        ``-ian``  (*Sclavi → Sclavian*)
    ``-es``       ``-ian``, ``-ean``  (*Saxones → Saxonian, Saxonean*)
    ``-ans``      drop *s*  (*Romans → Roman*)
    ``-s``        ``-ian``  (*Franks → Frankian*)
    ``-ae``       ``-n``, ``-nian``  (*Baltae → Baltan, Baltanian*)
    vowel         ``-nian``  (*Gale → Galenian*)
    other         unchanged  (*Bulgar → Bulgar*)
    ============  ===================================

    Args:
        ethnonym: Source ethnonym in its Latin or English plural form.
    """

    def __init__(self, ethnonym: str):
        super().__init__()
        self.ethnonym = ethnonym

    def __eq__(self, other: "AdjectiveFromEthnonymGenerator") -> bool:
        return (
            type(other) is type(self)
            and self.ethnonym == other.ethnonym
        )

    def train(self):
        """No-op — rule-based generator requires no corpus."""
        self.is_trained = True

    def generate(self, n: int) -> list[str]:
        """Return all derived adjective forms for the ethnonym.

        The *n* argument is accepted for API compatibility but is ignored;
        all applicable forms are always returned.

        Returns:
            Sorted list of derived adjective strings.
        """
        result = set()
        if self.ethnonym.endswith('ii'):
            result.add(self.ethnonym[:-1] + 'an')
        elif self.ethnonym.endswith('i'):
            result.add(self.ethnonym + 'an')
        elif self.ethnonym.endswith('es'):
            result.add(self.ethnonym[:-2] + 'ian')
            result.add(self.ethnonym[:-2] + 'ean')
        elif self.ethnonym.endswith('ans'):
            result.add(self.ethnonym[:-1])
        elif self.ethnonym.endswith('s'):
            result.add(self.ethnonym[:-1] + 'ian')
        elif self.ethnonym.endswith('ae'):
            result.add(self.ethnonym[:-1] + 'n')
            result.add(self.ethnonym[:-1] + 'nian')
        elif self.ethnonym[-1] in vowels:
            result.add(self.ethnonym + 'nian')
        else:
            result.add(self.ethnonym)
        return sorted(result)


class CountryNameFromLatinEthnonymGenerator(BaseGenerator):
    """Derive a country name (or names) from a Latin ethnonym.

    Applies suffix-substitution rules that reflect how Latin ethnonyms
    historically evolved into territorial names:

    ============  ===================================
    Ending        Derived form(s)
    ============  ===================================
    ``-ii``       ``-ia``   (*Germanii → Germania*)
    ``-i``        ``-ia``   (*Sclavi → Sclavia*)
    ``-es``       ``-ia``   (*Saxones → Saxonia*)
    ``-ians``     drop *ns* (*Persians → Persia*)
    ``-ans``      drop *s*; drop *ns*  (*Romans → Roman, Roma*)
    ``-s``        ``-ia``; drop *s*  (*Francs → Francia, Franc*)
    ``-ae``       drop *e*; drop *e* + *nia*  (*Baltae → Balta, Baltania*)
    other         unchanged; + *ia*  (*Bulgar → Bulgar, Bulgaria*)
    ============  ===================================

    Args:
        ethnonym: Source ethnonym in its Latin form.
    """

    def __init__(self, ethnonym: str):
        super().__init__()
        self.ethnonym = ethnonym

    def __eq__(self, other: "CountryNameFromLatinEthnonymGenerator") -> bool:
        return (
            type(other) is type(self)
            and self.ethnonym == other.ethnonym
        )

    def train(self):
        """No-op — rule-based generator requires no corpus."""
        self.is_trained = True

    def generate(self, n: int) -> list[str]:
        """Return all derived country name forms for the ethnonym.

        Returns:
            Sorted list of derived country name strings.
        """
        result = set()
        if self.ethnonym.endswith('ii'):
            result.add(self.ethnonym[:-1] + 'a')
        elif self.ethnonym.endswith('i'):
            result.add(self.ethnonym[:-1] + 'ia')
        elif self.ethnonym.endswith('es'):
            result.add(self.ethnonym[:-2] + 'ia')
        elif self.ethnonym.endswith('ians'):
            result.add(self.ethnonym[:-2])
        elif self.ethnonym.endswith('ans'):
            result.add(self.ethnonym[:-1])
            result.add(self.ethnonym[:-2])
        elif self.ethnonym.endswith('s'):
            result.add(self.ethnonym[:-1] + 'ia')
            result.add(self.ethnonym[:-1])
        elif self.ethnonym.endswith('ae'):
            result.add(self.ethnonym[:-1])
            result.add(self.ethnonym[:-1] + 'nia')
        else:
            result.add(self.ethnonym)
            result.add(self.ethnonym + 'ia')
        return sorted(result)


class CountryNameFromNativeEthnonymGenerator(BaseGenerator):
    """Derive a vernacular country name from a native (non-Latin) ethnonym.

    Uses language-family-specific patterns:

    * **Germanic** — strips a trailing *-s* plural, strips trailing vowels
      to find the stem, then yields *<stem>land* and *<stem>en*
      (e.g. *Saxons → Saxonland, Saxonen*).
    * **Celtic** — strips trailing *-s*, yields the singular form and a
      *Dal <singular>* construction  (e.g. *Gaels → Gael, Dal Gael*).
    * **Finnic** — appends *-maa* (land/country) directly to the ethnonym
      (e.g. *Suomi → Suomimaa*).
    * **Unknown family** — returns an empty list.

    Args:
        ethnonym: Source ethnonym in its native plural (or base) form.
        language_family: One of ``'Germanic'``, ``'Celtic'``, ``'Finnic'``,
            or ``None`` / any other value for an unrecognised family.
    """

    def __init__(self,
                 ethnonym: str,
                 language_family: str | None = None):
        super().__init__()
        self.ethnonym = ethnonym
        self.language_family = language_family

    def __eq__(self, other: "CountryNameFromNativeEthnonymGenerator") -> bool:
        return (
            type(other) is type(self)
            and self.ethnonym == other.ethnonym
            and self.language_family == other.language_family
        )

    def train(self):
        """No-op — rule-based generator requires no corpus."""
        self.is_trained = True

    def generate(self, n: int) -> list[str]:
        """Return all vernacular country name forms for the ethnonym.

        Returns:
            Sorted list of derived country name strings, or an empty list
            for unrecognised language families.
        """
        result = set()
        if self.ethnonym.endswith('s') and self.language_family in (
            'Germanic', 'Celtic', 'Baltic',
        ):
            singular = self.ethnonym[:-1]
        else:
            singular = self.ethnonym
        if singular[-1] in vowels:
            stem = singular
            while stem[-1] in vowels:
                stem = stem[:-1]
        else:
            stem = singular
        if self.language_family == 'Germanic':
            result.add(stem + 'land')
            result.add(stem + 'en')
        elif self.language_family == 'Celtic':
            result.add(singular)
            result.add('Dal ' + singular)
        elif self.language_family == 'Finnic':
            result.add(self.ethnonym + 'maa')
        return sorted(result)


class DynastyNameGenerator(SimpleNameGenerator):
    """Generate dynastic family names by appending or prepending a dynasty affix.

    Derives dynasty names from male given-name corpora by applying a
    language-specific suffix or prefix convention:

    * **OldGerman, Gothic, AngloSaxon, OldNorse** — strip trailing vowels,
      append *-ing* (e.g. *Sigismund → Sigismunding*).
    * **OldIrish** — prepend *Ui* (e.g. *Conall → Ui Conall*).
    * **All other languages** — strip trailing vowels, append *-id*
      (e.g. *Rurik → Rurikid*).

    Inherits all generation options from
    :class:`~generators.simple_name.SimpleNameGenerator`.

    Args:
        *languages: Language names for the male given-name corpus.
        pattern: Optional phonetic pattern for the base name.
        markov: Synthesis fraction.
        **constraints: Forwarded to
            :class:`~generators.word_constraints.WordConstraints`.
    """

    def __init__(self,
                 *languages: list[str],
                 pattern: str | None,
                 markov: float,
                 **constraints
                 ):
        super().__init__(*languages,
                         pattern=pattern,
                         gender='male',
                         name_part_type='given_name',
                         markov=markov,
                         **constraints)

    def __add_dynasty_affix(self, name: str) -> str:
        """Apply the language-appropriate dynasty affix to a base name."""
        language = self.languages[0]
        stem = name
        while len(stem) > 1 and stem[-1] in vowels:
            stem = stem[:-1]
        if language in (
            'OldGerman',
            'Gothic',
            'AngloSaxon',
            'OldNorse',
        ):
            return stem + 'ing'	
        if language == 'OldIrish':
            return 'Ui ' + stem
        return stem + 'id'

    def generate(self, n: int) -> list[str]:
        """Generate *n* dynasty names with the language-specific affix applied.

        Args:
            n: Number of dynasty names to generate.

        Returns:
            List of dynasty name strings.
        """
        names = super().generate(n)
        return [self.__add_dynasty_affix(name) for name in names]
