"""CSV loading helpers for name corpora."""

import csv
import re


def load_names_with_weights(
        path: str,
        pattern: str | None = None,
        ) -> tuple[list[str], list[float]]:
    """Load a name corpus CSV and return names with normalised frequency weights.

    The CSV must have a header row.  The first column is the name; an
    optional second column is an integer frequency count.  Rows without a
    frequency default to 1.

    Args:
        path: Path to the CSV file (UTF-8 encoded).
        pattern: Optional regex; only names that fully match (via
            ``re.match``) are included.  ``None`` means accept all names.

    Returns:
        A tuple ``(names, weights)`` where ``weights`` are normalised so
        that they sum to 1.0.
    """
    names, weights = [], []
    with open(path, 'r', encoding='utf8') as f:
        sum_weights = 0
        for i, row in enumerate(csv.reader(f)):
            if i == 0:
                continue
            if len(row) == 0:
                continue
            if pattern is not None and not re.match(pattern, row[0]):
                continue
            name = row[0]
            weight = 1 if len(row) == 1 else int(row[1])
            sum_weights += weight
            names.append(name)
            weights.append(weight)
    weights = [weight/sum_weights for weight in weights]
    return names, weights