from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")
deep_models = pytest.importorskip("carerisk48h.models.deep")


@pytest.mark.parametrize("family", ["grud", "tcn"])
def test_deep_model_shape_and_parameter_budget(family: str) -> None:
    model = deep_models.build_deep_model(family)
    values = torch.zeros(3, 48, 37)
    mask = torch.zeros(3, 48, 37)
    delta = torch.ones(3, 48, 37)
    static = torch.zeros(3, 5)
    output = model(values, mask, delta, static)
    assert output.shape == (3,)
    assert sum(parameter.numel() for parameter in model.parameters()) <= 250_000
