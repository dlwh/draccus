# SPDX-License-Identifier: MIT
# Copyright 2019 Fabrice Normandin
# Copyright 2021 Elad Richardson
# Copyright 2022-2025 The Draccus Authors

import dataclasses
from typing import Optional

from draccus.choice_types import PluginRegistry


@dataclasses.dataclass(frozen=True)
class ModelConfig(PluginRegistry, discover_packages_path="tests.draccus_choice_plugins"):
    layers: int

    @classmethod
    def default_choice_name(cls) -> Optional[str]:
        return "mlp"


@ModelConfig.register_subclass("mlp")
@dataclasses.dataclass(frozen=True)
class MlpConfig(ModelConfig):
    hidden_size: int = 100
