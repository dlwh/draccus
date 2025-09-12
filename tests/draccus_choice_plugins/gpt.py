# SPDX-License-Identifier: MIT
# Copyright 2019 Fabrice Normandin
# Copyright 2021 Elad Richardson
# Copyright 2022-2025 The Draccus Authors

import dataclasses

from tests.draccus_choice_plugins.model_config import ModelConfig


@ModelConfig.register_subclass("gpt")
@dataclasses.dataclass(frozen=True)
class GptConfig(ModelConfig):
    attn_pdrop: float = 0.1
