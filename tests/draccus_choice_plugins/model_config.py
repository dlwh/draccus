# Copyright 2025 The Board of Trustees of the Leland Stanford Junior University
# SPDX-License-Identifier: MIT


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
