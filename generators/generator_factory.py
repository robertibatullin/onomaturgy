"""Factory function for creating and caching generators from YAML config dicts."""

from generators.base_generator import BaseGenerator
from generators.word_generator import WordGenerator
from generators.simple_name import SimpleNameGenerator
from generators.place_name import PlaceNameGenerator
from generators.tribal_name import TribalNameGenerator

def generator_factory(config: dict, context: dict) -> BaseGenerator:
    """Instantiate (or return a cached) generator from a config dictionary.

    The *config* dict is consumed (keys are popped) and should contain at
    minimum ``name`` and ``class``.  The expected YAML structure is::

        name: my_generator
        class: SimpleNameGenerator   # any generator class name in this module
        languages:
          - Norwegian
          - English
        markov: 0.5

    If a generator with the same *name* already exists in *context* **and**
    compares equal to the newly constructed one (via ``__eq__``), the
    existing trained instance is returned without retraining — enabling
    efficient reuse across multiple calls that share the same configuration.

    Args:
        config: Configuration mapping.  Modified in place (keys are popped).
        context: Shared state dict.  A ``'generators'`` sub-dict is created
            on first use to store trained instances keyed by *name*.

    Returns:
        A trained :class:`~generators.base_generator.BaseGenerator` instance.
    """
    generator_name = config.pop('name')
    if not 'generators' in context:
        context['generators'] = {}
    generator_class = config.pop('class')
    generator_languages = config.pop('languages', [])
    if isinstance(generator_languages, str):
        generator_languages = [generator_languages]
    generator_kwargs = config
    generator = globals()[generator_class](*generator_languages, **generator_kwargs)
    if generator_name in context['generators']:
        existing_generator = context['generators'][generator_name]
        if generator == existing_generator:
            return existing_generator
    generator.train()
    context['generators'][generator_name] = generator
    return generator
