import csv
import os
import pytest


@pytest.fixture(autouse=True)
def repo_root():
    """Ensure every test runs with CWD = repository root."""
    original = os.getcwd()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root)
    yield
    os.chdir(original)


@pytest.fixture
def csv_file(tmp_path):
    """Return a factory that writes a minimal name CSV and returns its path.

    Each call within the same test gets a unique filename so multiple calls
    do not overwrite each other.
    """
    counter = [0]

    def _make(rows, header=('name', 'frequency')):
        counter[0] += 1
        path = tmp_path / f'names_{counter[0]}.csv'
        with open(path, 'w', encoding='utf-8', newline='') as f:
            w = csv.writer(f)
            w.writerow(header)
            for row in rows:
                w.writerow(row)
        return str(path)
    return _make
