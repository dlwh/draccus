from dataclasses import dataclass

import pytest

import draccus
from draccus.utils import Dataclass, DraccusException


@dataclass
class TestConfig:
    a: int = 1
    b: str = "test"
    c: float = 3.14


def test_load_from_file(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_path.write_text("a: 2\nb: hello\nc: 1.23")

    # Test with file path
    cfg = draccus.load(TestConfig, config_path)
    assert cfg.a == 2
    assert cfg.b == "hello"
    assert cfg.c == 1.23

    # Test with file object
    with open(config_path, "r") as f:
        cfg = draccus.load(TestConfig, f)
    assert cfg.a == 2
    assert cfg.b == "hello"
    assert cfg.c == 1.23


def test_loads_from_string():
    config_str = "a: 2\nb: hello\nc: 1.23"
    cfg = draccus.loads(TestConfig, config_str)
    assert cfg.a == 2
    assert cfg.b == "hello"
    assert cfg.c == 1.23


def test_load_backwards_compatibility():
    # Test that load still works with string content directly
    config_str = "a: 2\nb: hello\nc: 1.23"
    cfg = draccus.load(TestConfig, config_str)
    assert cfg.a == 2
    assert cfg.b == "hello"
    assert cfg.c == 1.23


def test_load_invalid_input():
    with pytest.raises(DraccusException):
        draccus.load(TestConfig, None)

    with pytest.raises(DraccusException):
        draccus.loads(TestConfig, None)
