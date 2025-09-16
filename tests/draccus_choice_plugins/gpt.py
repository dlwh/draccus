# SPDX-License-Identifier: MIT
# Copyright 2025 The Board of Trustees of the Leland Stanford Junior University

import dataclasses

from tests.draccus_choice_plugins.model_config import ModelConfig


@ModelConfig.register_subclass("gpt")
@dataclasses.dataclass(frozen=True)
class GptConfig(ModelConfig):
    attn_pdrop: float = 0.1
