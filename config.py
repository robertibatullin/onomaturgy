"""Configuration for onomaturgy.

Data access is handled by :mod:`helpers.data_manager`, which downloads CSV
files on demand from https://github.com/robertibatullin/onomaturgy-data and
caches them in ``~/.cache/onomaturgy/``.

Set the ``ONOMATURGY_CACHE`` environment variable to override the cache
directory (useful in CI or when running tests against a local data copy).
"""
