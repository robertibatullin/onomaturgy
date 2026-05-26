"""Download-on-demand manager for onomaturgy CSV corpora.

On first use the manager downloads only the specific CSV files needed by the
calling generator and stores them in a local cache.  Subsequent calls are
served from the cache with no network access.

Resolution order for every file request:

1. **Installed data package** — if ``onomaturgy_data`` is importable (e.g.
   ``pip install onomaturgy-data``) its bundled files are used directly;
   no download, no cache write.
2. **Local cache** — ``~/.cache/onomaturgy/csv/`` (or the directory given by
   the ``ONOMATURGY_CACHE`` environment variable).
3. **Remote download** — ``https://raw.githubusercontent.com/
   robertibatullin/onomaturgy-data/main/csv/<path>``.  The file is saved to
   the cache so future calls do not re-download.

Directory listings (:func:`list_dir`) follow the same order but consult a
``manifest.json`` file in the data repository root instead of listing a remote
directory.
"""

import json
import os
import urllib.request
import urllib.error
from pathlib import Path


_BASE_URL = (
    'https://raw.githubusercontent.com/robertibatullin/onomaturgy-data/main/csv'
)
_MANIFEST_URL = (
    'https://raw.githubusercontent.com/robertibatullin/onomaturgy-data/main/manifest.json'
)

_cache_root = Path(
    os.environ.get('ONOMATURGY_CACHE', Path.home() / '.cache' / 'onomaturgy')
)
_CSV_CACHE = _cache_root / 'csv'
_MANIFEST_CACHE = _cache_root / 'manifest.json'


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _installed_data_root() -> str | None:
    """Return the data root from an installed onomaturgy_data package, or None."""
    try:
        from onomaturgy_data import data_path  # type: ignore[import]
        return data_path
    except ImportError:
        return None


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, dest)
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Failed to download {url}.\n"
            f"Check your internet connection, or install the data package:\n"
            f"  pip install onomaturgy-data\n"
            f"Original error: {exc}"
        ) from exc


def _load_manifest() -> dict:
    if not _MANIFEST_CACHE.exists():
        _download(_MANIFEST_URL, _MANIFEST_CACHE)
    with open(_MANIFEST_CACHE, encoding='utf-8') as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_path(relative_path: str) -> str:
    """Return an absolute local path to *relative_path*, downloading if needed.

    Args:
        relative_path: Path relative to the CSV data root, using forward
            slashes (e.g. ``'names/Russian/russian_m.csv'``).

    Returns:
        Absolute path string to the locally available file.

    Raises:
        RuntimeError: If the file cannot be found locally and cannot be
            downloaded (e.g. no internet access and not cached).
    """
    norm = relative_path.replace('\\', '/')

    # 1. Installed data package
    root = _installed_data_root()
    if root is not None:
        local = os.path.join(root, norm)
        if os.path.exists(local):
            return local

    # 2. Download cache
    cached = _CSV_CACHE / norm
    if cached.exists():
        return str(cached)

    # 3. Download from remote
    url = f'{_BASE_URL}/{norm}'
    _download(url, cached)
    return str(cached)


def list_dir(relative_dir: str) -> list[str]:
    """Return CSV filenames inside *relative_dir*.

    Args:
        relative_dir: Directory path relative to the CSV data root (e.g.
            ``'names/Russian'`` or ``'ethnonyms'``).

    Returns:
        List of ``*.csv`` filenames (basenames only) present in that
        directory.  Returns an empty list if the directory is unknown.
    """
    norm = relative_dir.replace('\\', '/')

    # 1. Installed data package
    root = _installed_data_root()
    if root is not None:
        d = os.path.join(root, norm)
        if os.path.isdir(d):
            return [f for f in os.listdir(d) if f.endswith('.csv')]

    # 2. Manifest
    return _load_manifest().get(norm, [])


def try_get_path(relative_path: str) -> str | None:
    """Like :func:`get_path` but returns ``None`` instead of raising if the
    file is absent both locally and remotely (HTTP 404).

    Use this for optional corpus files that may not exist for every language
    (e.g. ``_separate_beginnings.csv``).
    """
    norm = relative_path.replace('\\', '/')

    # 1. Installed data package
    root = _installed_data_root()
    if root is not None:
        local = os.path.join(root, norm)
        return local if os.path.exists(local) else None

    # 2. Download cache
    cached = _CSV_CACHE / norm
    if cached.exists():
        return str(cached)

    # 3. Attempt download; swallow 404
    url = f'{_BASE_URL}/{norm}'
    cached.parent.mkdir(parents=True, exist_ok=True)
    try:
        urllib.request.urlretrieve(url, cached)
        return str(cached)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise RuntimeError(
            f"Failed to download {url}: {exc}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Failed to download {url}.\n"
            f"Check your internet connection.\n"
            f"Original error: {exc}"
        ) from exc


def invalidate_cache() -> None:
    """Delete all cached data so it will be re-downloaded on next use."""
    import shutil
    if _cache_root.exists():
        shutil.rmtree(_cache_root)
