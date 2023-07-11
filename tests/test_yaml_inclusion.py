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
            """
        )

        age_group_path = tmpdir / "age_group.yaml"
        age_group_path.write_text(
            """
name: age_group
num_units: 16
"""
        )

        config = HyperParameters.setup(f"--config_path {config_path}")

        assert config.age_group.name == "age_group"
        assert config.age_group.num_units == 16


def test_merge_include_hyperparameters(HyperParameters):
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        config_path = tmpdir / "config.yaml"
        config_path.write_text(
            """
<<: !include ./base_config.yaml
age_group: !include ./age_group.yaml
embedding_dim: 32
            """,
        )

        base_config_path = tmpdir / "base_config.yaml"
        base_config_path.write_text(
            """
batch_size: 13
optimizer: ADAM
embedding_dim: 16
"""
        )

        age_group_path = tmpdir / "age_group.yaml"
        age_group_path.write_text(
            """
name: age_group
num_units: 16
"""
        )

        config = HyperParameters.setup(f"--config_path {config_path}")

        assert config.batch_size == 13
        assert config.optimizer == Optimizers.ADAM
        assert config.embedding_dim == 32
        assert config.age_group.name == "age_group"
        assert config.age_group.num_units == 16
