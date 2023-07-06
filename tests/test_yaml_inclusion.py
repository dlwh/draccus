import tempfile
from enum import Enum, auto
from pathlib import Path


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
