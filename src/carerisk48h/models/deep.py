"""Compact missingness-aware GRU-D and TCN mortality models."""

from __future__ import annotations

from typing import Any

import torch
from torch import Tensor, nn
from torch.nn import functional as F

from carerisk48h.constants import STATIC_VARIABLES, TIME_SERIES_VARIABLES


class GRUD(nn.Module):
    """Small GRU-D variant with value and hidden-state exponential decay."""

    def __init__(self, *, hidden_size: int = 64, static_size: int = 16) -> None:
        super().__init__()
        variables = len(TIME_SERIES_VARIABLES)
        self.hidden_size = hidden_size
        self.register_buffer("feature_mean", torch.zeros(variables))
        self.decay_x_weight = nn.Parameter(torch.ones(variables))
        self.decay_x_bias = nn.Parameter(torch.zeros(variables))
        self.delta_to_hidden = nn.Linear(variables, hidden_size)
        self.gru_cell = nn.GRUCell(variables * 2, hidden_size)
        self.static_branch = nn.Sequential(
            nn.Linear(len(STATIC_VARIABLES), static_size), nn.ReLU(), nn.Dropout(0.1)
        )
        self.classifier = nn.Linear(hidden_size + static_size, 1)

    def forward(self, values: Tensor, mask: Tensor, delta: Tensor, static: Tensor) -> Tensor:
        batch_size = values.shape[0]
        hidden = values.new_zeros((batch_size, self.hidden_size))
        last_value = self.feature_mean.expand(batch_size, -1)
        for hour in range(values.shape[1]):
            current_mask = mask[:, hour]
            current_delta = delta[:, hour]
            gamma_x = torch.exp(-F.relu(current_delta * self.decay_x_weight + self.decay_x_bias))
            gamma_h = torch.exp(-F.relu(self.delta_to_hidden(current_delta)))
            hidden = gamma_h * hidden
            decayed_value = gamma_x * last_value + (1.0 - gamma_x) * self.feature_mean
            current_value = current_mask * values[:, hour] + (1.0 - current_mask) * decayed_value
            hidden = self.gru_cell(torch.cat([current_value, current_mask], dim=1), hidden)
            last_value = current_mask * values[:, hour] + (1.0 - current_mask) * last_value
        static_embedding = self.static_branch(static)
        return self.classifier(torch.cat([hidden, static_embedding], dim=1)).squeeze(1)


class CausalConv1d(nn.Conv1d):
    def __init__(self, channels: int, *, kernel_size: int, dilation: int) -> None:
        self.trim = (kernel_size - 1) * dilation
        super().__init__(
            channels,
            channels,
            kernel_size,
            padding=self.trim,
            dilation=dilation,
        )

    def forward(self, inputs: Tensor) -> Tensor:
        output = super().forward(inputs)
        return output[:, :, : -self.trim] if self.trim else output


class ResidualTCNBlock(nn.Module):
    def __init__(self, channels: int, *, dilation: int) -> None:
        super().__init__()
        self.network = nn.Sequential(
            CausalConv1d(channels, kernel_size=3, dilation=dilation),
            nn.ReLU(),
            nn.Dropout(0.1),
            CausalConv1d(channels, kernel_size=3, dilation=dilation),
            nn.ReLU(),
            nn.Dropout(0.1),
        )

    def forward(self, inputs: Tensor) -> Tensor:
        return F.relu(inputs + self.network(inputs))


class SmallTCN(nn.Module):
    """Compact TCN over normalized value, mask, and log1p(delta) channels."""

    def __init__(self, *, channels: int = 32, static_size: int = 16) -> None:
        super().__init__()
        variables = len(TIME_SERIES_VARIABLES)
        self.input_projection = nn.Conv1d(variables * 3, channels, kernel_size=1)
        self.blocks = nn.Sequential(
            *(ResidualTCNBlock(channels, dilation=item) for item in (1, 2, 4, 8))
        )
        self.static_branch = nn.Sequential(
            nn.Linear(len(STATIC_VARIABLES), static_size), nn.ReLU(), nn.Dropout(0.1)
        )
        self.classifier = nn.Linear(channels + static_size, 1)

    def forward(self, values: Tensor, mask: Tensor, delta: Tensor, static: Tensor) -> Tensor:
        channels = torch.cat([values, mask, torch.log1p(delta)], dim=2).transpose(1, 2)
        temporal = self.blocks(self.input_projection(channels)).mean(dim=2)
        static_embedding = self.static_branch(static)
        return self.classifier(torch.cat([temporal, static_embedding], dim=1)).squeeze(1)


def build_deep_model(family: str, **parameters: Any) -> nn.Module:
    if family == "grud":
        model: nn.Module = GRUD(**parameters)
    elif family == "tcn":
        model = SmallTCN(**parameters)
    else:
        raise ValueError("family must be 'grud' or 'tcn'")
    count = sum(parameter.numel() for parameter in model.parameters())
    if count > 250_000:
        raise ValueError(f"{family} exceeds the 250k parameter budget: {count}")
    return model
