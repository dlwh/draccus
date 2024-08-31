import tempfile
from enum import Enum, auto
from pathlib import Path

from tests.conftest import Optimizers


class Color(Enum):
    blue: str = auto()  # type: ignore
    red: str = auto()  # type: ignore


def test_load_hyperparameters_with_include(HyperParameters):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        config_path = tmpdir / "config.yaml"
        config_path.write_text(
            """
age_group: !include ./age_group.yaml
batch_size: 1234
            """
        )

        age_group_path = tmpdir / "age_group.yaml"
        age_group_path.write_text(
            """
name: age_group
num_units: 16
"""
        )

        age_group_path_cli = tmpdir / "age_group_cli.yaml"
        age_group_path_cli.write_text(
            """
name: age_group_cli
num_units: 16
"""
        )


        config = HyperParameters.setup(f"--config_path {config_path} "
                                       f"--age_group 'include {age_group_path_cli}' "
                                       f"--age_group.num_units 32")

        assert config.age_group.name == "age_group_cli"
        assert config.age_group.num_units == 32


def test_merge_include_hyperparameters(HyperParameters):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        config_path = tmpdir / "config.yaml"
        config_path.write_text(
            """
age_group: 
  name: age_group_1
  num_units: 16
batch_size: 1234
            """
        )

        age_group_path_cli = tmpdir / "age_group_cli.yaml"
        age_group_path_cli.write_text(
            """
name: age_group_cli
num_units: 678
"""
        )

        config = HyperParameters.setup(f"--config_path {config_path} "
                                       f"--age_group 'include {age_group_path_cli}' ")

        assert config.age_group.name == "age_group_cli"
        assert config.age_group.num_units == 678

