# Copyright 2025 The Draccus Authors
# SPDX-License-Identifier: Apache-2.0


import dataclasses

from tests.draccus_choice_plugins.model_config import ModelConfig


@ModelConfig.register_subclass("gpt")
@dataclasses.dataclass(frozen=True)
class GptConfig(ModelConfig):
    attn_pdrop: float = 0.1
