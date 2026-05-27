"""Abstract base class shared by all generator implementations."""

from abc import ABC, abstractmethod


class BaseGenerator(ABC):
    """Common interface for all name and word generators.

    Subclasses must implement :meth:`train` and :meth:`generate`.
    The :attr:`is_trained` flag is set to ``False`` on construction and
    must be set to ``True`` by :meth:`train` once the generator is ready.
    """

    def __init__(self, *args, **kwargs) -> None:
        self.is_trained = False

    @abstractmethod
    def train(self):
        """Load data and prepare internal state for generation.

        After this call :attr:`is_trained` must be ``True``.
        """

    @abstractmethod
    def generate(self, n: int, **kwargs) -> list[str]:
        """Return a list of *n* generated strings.

        Args:
            n: Number of items to generate.
            **kwargs: Generator-specific options (e.g. ``no_repeat``).

        Returns:
            A list of generated strings.  The list may be shorter than *n*
            if the generator cannot produce enough unique results.
        """
