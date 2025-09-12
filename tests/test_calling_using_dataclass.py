# SPDX-License-Identifier: MIT
# Copyright 2019 Fabrice Normandin
# Copyright 2021 Elad Richardson
# Copyright 2022-2025 The Draccus Authors

from dataclasses import dataclass, field

import draccus


@dataclass
class TrainConfig:
    workers: int


@draccus.wrap()
def function_with_draccus_wrap(cfg: TrainConfig):
    assert cfg.workers == 8


def test_calling_using_dataclasses():
    config = TrainConfig(workers=8)
    function_with_draccus_wrap(config)
