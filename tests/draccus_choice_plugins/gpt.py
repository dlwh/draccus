import dataclasses

from tests.draccus_choice_plugins.model_config import ModelConfig


@ModelConfig.register_subclass("gpt")
@dataclasses.dataclass
class GptConfig(ModelConfig):
    attn_pdrop: float = 0.1
