"""Tests for helpers/data_manager.py — download-on-demand caching layer.

All three resolution paths are exercised:
  1. Installed onomaturgy-data package  → use it directly, no download
  2. Local cache hit                    → return cached path, no download
  3. Cache miss                         → download, write to cache, return path

No real network calls are made; urllib.request.urlretrieve is monkeypatched.
The installed-package path is exercised by monkeypatching _installed_data_root.
"""

import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest

import helpers.data_manager as dm
from generators.simple_name import SimpleNameGenerator


# ---------------------------------------------------------------------------
# Shared fake data
# ---------------------------------------------------------------------------

_CSV = "name,frequency\nAlice,10\nBob,5\nCarol,7\n"
_MANIFEST = {"names/Testlang": ["testlang_m.csv"]}


def _make_urlretrieve(responses: dict, call_count: list[int] | None = None):
    """Return a urlretrieve stub that serves fake content by URL substring.

    If no pattern matches, raises HTTPError 404.
    """
    def _stub(url: str, dest) -> None:
        if call_count is not None:
            call_count[0] += 1
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        for pattern, content in responses.items():
            if pattern in url:
                dest.write_text(content, encoding="utf-8")
                return
        raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
    return _stub


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def no_pkg(monkeypatch):
    """Simulate onomaturgy-data not installed."""
    monkeypatch.setattr(dm, "_installed_data_root", lambda: None)


@pytest.fixture()
def fake_cache(monkeypatch, tmp_path):
    """Redirect the cache to tmp_path; return (csv_cache_dir, manifest_path)."""
    csv_cache = tmp_path / "csv"
    manifest = tmp_path / "manifest.json"
    monkeypatch.setattr(dm, "_CSV_CACHE", csv_cache)
    monkeypatch.setattr(dm, "_MANIFEST_CACHE", manifest)
    monkeypatch.setattr(dm, "_cache_root", tmp_path)
    return csv_cache, manifest


# ---------------------------------------------------------------------------
# get_path
# ---------------------------------------------------------------------------

class TestGetPath:
    def test_installed_package_used_directly(self, monkeypatch, fake_cache, tmp_path):
        """Path 1: installed package file is returned without any download."""
        pkg_root = tmp_path / "pkg"
        target = pkg_root / "names" / "Russian" / "russian_m.csv"
        target.parent.mkdir(parents=True)
        target.write_text(_CSV, encoding="utf-8")
        monkeypatch.setattr(dm, "_installed_data_root", lambda: str(pkg_root))

        network_calls = []
        monkeypatch.setattr(
            urllib.request, "urlretrieve",
            lambda url, dest: network_calls.append(url),
        )

        result = dm.get_path("names/Russian/russian_m.csv")

        assert Path(result) == target
        assert network_calls == [], "installed package must not trigger a download"

    def test_cache_hit_no_download(self, monkeypatch, no_pkg, fake_cache):
        """Path 2: file already in cache → return it, no network."""
        csv_cache, _ = fake_cache
        cached = csv_cache / "names" / "Russian" / "russian_m.csv"
        cached.parent.mkdir(parents=True)
        cached.write_text(_CSV, encoding="utf-8")

        network_calls = []
        monkeypatch.setattr(
            urllib.request, "urlretrieve",
            lambda url, dest: network_calls.append(url),
        )

        result = dm.get_path("names/Russian/russian_m.csv")

        assert result == str(cached)
        assert network_calls == [], "cached file must not trigger a download"

    def test_download_on_cache_miss(self, monkeypatch, no_pkg, fake_cache):
        """Path 3: file absent → download, write to cache, return path."""
        csv_cache, _ = fake_cache
        monkeypatch.setattr(
            urllib.request, "urlretrieve",
            _make_urlretrieve({"russian_m.csv": _CSV}),
        )

        result = dm.get_path("names/Russian/russian_m.csv")

        expected = csv_cache / "names" / "Russian" / "russian_m.csv"
        assert Path(result) == expected
        assert expected.exists()
        assert expected.read_text(encoding="utf-8") == _CSV

    def test_second_call_hits_cache_not_network(self, monkeypatch, no_pkg, fake_cache):
        """Once cached, repeated calls must not re-download."""
        count = [0]
        monkeypatch.setattr(
            urllib.request, "urlretrieve",
            _make_urlretrieve({"russian_m.csv": _CSV}, count),
        )

        dm.get_path("names/Russian/russian_m.csv")   # first: downloads
        dm.get_path("names/Russian/russian_m.csv")   # second: cache

        assert count[0] == 1, "urlretrieve must be called exactly once"

    def test_network_failure_raises_runtime_error(
        self, monkeypatch, no_pkg, fake_cache
    ):
        def broken(url, dest):
            raise urllib.error.URLError("connection refused")
        monkeypatch.setattr(urllib.request, "urlretrieve", broken)

        with pytest.raises(RuntimeError, match="Failed to download"):
            dm.get_path("names/Russian/russian_m.csv")


# ---------------------------------------------------------------------------
# try_get_path
# ---------------------------------------------------------------------------

class TestTryGetPath:
    def test_returns_none_on_404(self, monkeypatch, no_pkg, fake_cache):
        """A 404 from the server must return None, not raise."""
        def raise_404(url, dest):
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)
        monkeypatch.setattr(urllib.request, "urlretrieve", raise_404)

        assert dm.try_get_path("names/Russian/optional.csv") is None

    def test_cache_hit_no_download(self, monkeypatch, no_pkg, fake_cache):
        csv_cache, _ = fake_cache
        cached = csv_cache / "names" / "Russian" / "russian_sep.csv"
        cached.parent.mkdir(parents=True)
        cached.write_text(_CSV, encoding="utf-8")

        network_calls = []
        monkeypatch.setattr(
            urllib.request, "urlretrieve",
            lambda url, dest: network_calls.append(url),
        )

        result = dm.try_get_path("names/Russian/russian_sep.csv")
        assert result == str(cached)
        assert network_calls == []

    def test_download_when_found_on_server(self, monkeypatch, no_pkg, fake_cache):
        monkeypatch.setattr(
            urllib.request, "urlretrieve",
            _make_urlretrieve({"russian_m.csv": _CSV}),
        )

        result = dm.try_get_path("names/Russian/russian_m.csv")
        assert result is not None

    def test_installed_package_returns_none_for_missing_optional(
        self, monkeypatch, fake_cache, tmp_path
    ):
        """Installed package but the optional file doesn't exist → None."""
        pkg_root = tmp_path / "pkg"
        pkg_root.mkdir()
        monkeypatch.setattr(dm, "_installed_data_root", lambda: str(pkg_root))

        result = dm.try_get_path("names/Russian/nonexistent.csv")
        assert result is None


# ---------------------------------------------------------------------------
# list_dir
# ---------------------------------------------------------------------------

class TestListDir:
    def test_installed_package_listed_directly(
        self, monkeypatch, fake_cache, tmp_path
    ):
        """Installed package → scan the real directory, no manifest."""
        pkg_root = tmp_path / "pkg"
        lang_dir = pkg_root / "names" / "Russian"
        lang_dir.mkdir(parents=True)
        (lang_dir / "russian_m.csv").write_text(_CSV, encoding="utf-8")
        (lang_dir / "russian_f.csv").write_text(_CSV, encoding="utf-8")
        monkeypatch.setattr(dm, "_installed_data_root", lambda: str(pkg_root))

        result = dm.list_dir("names/Russian")
        assert set(result) == {"russian_m.csv", "russian_f.csv"}

    def test_manifest_used_when_no_package(self, monkeypatch, no_pkg, fake_cache):
        _, manifest = fake_cache
        manifest.write_text(json.dumps(_MANIFEST), encoding="utf-8")

        result = dm.list_dir("names/Testlang")
        assert result == ["testlang_m.csv"]

    def test_unknown_dir_returns_empty_list(self, monkeypatch, no_pkg, fake_cache):
        _, manifest = fake_cache
        manifest.write_text("{}", encoding="utf-8")

        assert dm.list_dir("names/Nonexistent") == []

    def test_manifest_downloaded_when_absent(self, monkeypatch, no_pkg, fake_cache):
        """If manifest.json is not cached, it must be downloaded automatically."""
        monkeypatch.setattr(
            urllib.request, "urlretrieve",
            _make_urlretrieve({"manifest.json": json.dumps(_MANIFEST)}),
        )

        result = dm.list_dir("names/Testlang")
        assert result == ["testlang_m.csv"]


# ---------------------------------------------------------------------------
# invalidate_cache
# ---------------------------------------------------------------------------

class TestInvalidateCache:
    def test_removes_cache_directory(self, monkeypatch, no_pkg, fake_cache, tmp_path):
        csv_cache, manifest = fake_cache
        csv_cache.mkdir(parents=True, exist_ok=True)
        (csv_cache / "dummy.csv").write_text("x", encoding="utf-8")
        manifest.write_text("{}", encoding="utf-8")
        # _cache_root already patched to tmp_path by fake_cache fixture

        dm.invalidate_cache()

        assert not tmp_path.exists()

    def test_no_error_when_cache_absent(self, monkeypatch, no_pkg, fake_cache, tmp_path):
        # _cache_root points to tmp_path which exists but has nothing relevant
        # Call twice to confirm idempotent behaviour
        dm.invalidate_cache()   # deletes tmp_path
        # tmp_path gone; calling again should be a no-op (root doesn't exist)
        dm.invalidate_cache()


# ---------------------------------------------------------------------------
# End-to-end: SimpleNameGenerator → data_manager → download → cache
# ---------------------------------------------------------------------------

class TestEndToEnd:
    """Full chain: generator.train() triggers downloads on first call,
    reads silently from cache on the second call — no real network used."""

    def _setup(self, monkeypatch, tmp_path):
        csv_cache = tmp_path / "csv"
        manifest_path = tmp_path / "manifest.json"
        monkeypatch.setattr(dm, "_installed_data_root", lambda: None)
        monkeypatch.setattr(dm, "_CSV_CACHE", csv_cache)
        monkeypatch.setattr(dm, "_MANIFEST_CACHE", manifest_path)
        monkeypatch.setattr(dm, "_cache_root", tmp_path)
        # Pre-populate manifest so the manifest download doesn't inflate the count
        manifest_path.write_text(
            json.dumps({"names/Russian": ["russian_m.csv"]}), encoding="utf-8"
        )
        return csv_cache

    def test_first_train_downloads_csv_to_cache(self, monkeypatch, tmp_path):
        csv_cache = self._setup(monkeypatch, tmp_path)
        monkeypatch.setattr(
            urllib.request, "urlretrieve",
            _make_urlretrieve({"russian_m.csv": _CSV}),
        )

        g = SimpleNameGenerator(
            "Russian", gender="male", markov=0.0, pattern=None,
            name_part_type="given_name",
        )
        g.train()

        cached_csv = csv_cache / "names" / "Russian" / "russian_m.csv"
        assert cached_csv.exists(), "CSV must be written to cache after first train()"
        assert len(g.generate(3)) > 0

    def test_second_train_reads_cache_no_extra_download(
        self, monkeypatch, tmp_path
    ):
        csv_cache = self._setup(monkeypatch, tmp_path)
        count = [0]
        monkeypatch.setattr(
            urllib.request, "urlretrieve",
            _make_urlretrieve({"russian_m.csv": _CSV}, count),
        )

        # First train: must download
        g1 = SimpleNameGenerator(
            "Russian", gender="male", markov=0.0, pattern=None,
            name_part_type="given_name",
        )
        g1.train()
        after_first = count[0]
        assert after_first >= 1, "At least one download expected on first train()"

        # Second train (fresh generator object, same language): must use cache
        g2 = SimpleNameGenerator(
            "Russian", gender="male", markov=0.0, pattern=None,
            name_part_type="given_name",
        )
        g2.train()

        assert count[0] == after_first, (
            f"No downloads expected on second train(); "
            f"got {count[0] - after_first} extra"
        )
        assert len(g2.generate(3)) > 0
