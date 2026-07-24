from __future__ import annotations

import numpy as np

from carerisk48h.deep_preprocessing import DeepPreprocessor
from carerisk48h.synthetic import generate_synthetic_cohort


def test_deep_preprocessor_fit_scope_and_round_trip(tmp_path) -> None:
    stays, _ = generate_synthetic_cohort(120, seed=2026)
    train = stays[:80]
    processor = DeepPreprocessor.fit(train)
    assert set(processor.fit_record_ids) == {stay.record_id for stay in train}
    transformed = processor.transform(stays[80:])
    assert transformed["values"].shape == (40, 48, 37)
    assert transformed["mask"].shape == (40, 48, 37)
    assert np.isfinite(transformed["values"]).all()
    path = tmp_path / "preprocessor.npz"
    processor.save(path)
    loaded = DeepPreprocessor.load(path)
    for name in ("value_mean", "value_std", "static_median", "static_mean", "static_std"):
        np.testing.assert_array_equal(getattr(loaded, name), getattr(processor, name))


def test_deep_preprocessor_uses_only_fit_rows() -> None:
    stays, _ = generate_synthetic_cohort(120, seed=2026)
    first = DeepPreprocessor.fit(stays[:80])
    stays[90].values[:, 0] = 1_000_000
    second = DeepPreprocessor.fit(stays[:80])
    np.testing.assert_array_equal(first.value_mean, second.value_mean)
