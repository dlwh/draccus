from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from .testutils import TestSetup


def test_optional_union():
    @dataclass
    class Config(TestSetup):
        path: Union[Path, str, None] = None

    config = Config.setup("--path bob")
    assert config.path == Path("bob")

    config = Config.setup("")
    assert config.path is None

    config = Config.setup("--path null")
    assert config.path is None
