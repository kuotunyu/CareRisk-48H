from __future__ import annotations

import pandas as pd
import pytest

from carerisk48h.data.split import make_split_manifest, validate_split_manifest


def _metadata(n: int = 400) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "RecordID": range(1000, 1000 + n),
            "label": [int(index % 7 == 0) for index in range(n)],
            "ICUType": [index % 4 + 1 for index in range(n)],
        }
    )


def test_split_is_deterministic_disjoint_and_complete() -> None:
    metadata = _metadata()
    first = make_split_manifest(metadata, seed=2026)
    second = make_split_manifest(metadata, seed=2026)
    pd.testing.assert_frame_equal(first, second)
    assert first["RecordID"].is_unique
    assert set(first["RecordID"]) == set(metadata["RecordID"])
    counts = first["split"].value_counts().to_dict()
    assert counts == {"train": 280, "validation": 60, "calibration": 60}


def test_split_validator_rejects_duplicates() -> None:
    manifest = pd.DataFrame(
        {"RecordID": [1, 1, 2], "split": ["train", "validation", "calibration"]}
    )
    with pytest.raises(ValueError, match="duplicate"):
        validate_split_manifest(manifest)
