import dataclasses

from draccus.choice_types import PluginRegistry


@dataclasses.dataclass
class ModelConfig(PluginRegistry, discover_packages_path="tests.draccus_choice_plugins"):
    layers: int


@ModelConfig.register_subclass("mlp")
@dataclasses.dataclass
class MlpConfig(ModelConfig):
    hidden_size: int = 100
