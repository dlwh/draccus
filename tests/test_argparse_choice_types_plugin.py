import dataclasses
import sys

import pytest

from draccus import ParsingError

from .draccus_choice_plugins.model_config import MlpConfig, ModelConfig
from .testutils import TestSetup


def test_plugin_registry_argparse():
    @dataclasses.dataclass
    class Something(TestSetup):
        model: ModelConfig = MlpConfig(10, 5)

    s = Something.setup("")
    assert s.model == MlpConfig(10, 5)

    s = Something.setup("--model.type mlp --model.layers 12 --model.hidden_size 6")
    assert s.model == MlpConfig(12, 6)

    s = Something.setup("--model.layers 12 --model.hidden_size 6")
    assert s.model == MlpConfig(12, 6)

    s = Something.setup("--model.type gpt --model.layers 12 --model.attn_pdrop 0.2")
    from .draccus_choice_plugins.gpt import GptConfig

    assert s.model == GptConfig(12, 0.2)

    with pytest.raises(SystemExit):
        Something.setup("--model.type baby")

    with pytest.raises(ParsingError):
        Something.setup("--model.type gpt --model.layers 12 --model.hidden_size 6")

    with pytest.raises(ParsingError):
        Something.setup("--model.attn_pdrop 12")


# skip this test if using python 3.8
# the help text is a bit different in 3.8


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.9 or higher")
def test_choice_registry_examine_help():
    @dataclasses.dataclass
    class Something(TestSetup):
        model: ModelConfig = MlpConfig(10, 5)

    # TODO: why is the default: None here?
    target = """
usage: draccus [-h] [--config_path str] [--model str] [--model.type {mlp,gpt}]
               [--model.hidden_size int] [--model.layers int]
               [--model.attn_pdrop float]

options:
  -h, --help            show this help message and exit
  --config_path str     Path for a config file to parse with draccus (default:
                        None)
  --model str           Config file for model (default: None)

test_choice_registry_examine_help.<locals>.Something:

ModelConfig ['model']:

  --model.type {mlp,gpt}
                        Which type of ModelConfig ['model'] to use (default:
                        None)

MlpConfig ['model']:

  --model.layers int
  --model.hidden_size int

GptConfig ['model']:

  --model.layers int
  --model.attn_pdrop float
"""
    print(Something.get_help_text())
    assert Something.get_help_text().strip() == target.strip()
