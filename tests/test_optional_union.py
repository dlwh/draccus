# SPDX-License-Identifier: MIT
# Copyright 2019 Fabrice Normandin
# Copyright 2021 Elad Richardson
# Copyright 2022-2025 The Draccus Authors

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
