"""Tests for literal type support in Draccus."""
import io
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Literal

import pytest

from draccus import ParsingError, decode, parse

from .testutils import TestSetup, raises


@dataclass
class StringLiteralConfig(TestSetup):
    mode: Literal["train", "test", "eval"] = field(default="train")
    size: Literal["small", "medium", "large"] = field(default="small")


@dataclass
class NumericLiteralConfig(TestSetup):
    mode: Literal[1, 2, 3] = field(default=1)
    size: Literal[10, 20, 30] = field(default=10)


@dataclass
class MixedLiteralConfig(TestSetup):
    mode: Literal["train", 1, True] = field(default="train")
    size: Literal["small", 20, False] = field(default="small")


def test_string_literal_valid():
    config = decode(StringLiteralConfig, {"mode": "train"})
    assert config.mode == "train"

    config = decode(StringLiteralConfig, {"mode": "eval"})
    assert config.mode == "eval"

    config = decode(StringLiteralConfig, {"mode": "test"})
    assert config.mode == "test"


def test_string_literal_invalid():
    with pytest.raises(Exception) as exc_info:
        decode(StringLiteralConfig, {"mode": "invalid"})
    assert "into one of" in str(exc_info.value)


def test_numeric_literal_valid():
    config = decode(NumericLiteralConfig, {"size": 10})
    assert config.size == 10

    config = decode(NumericLiteralConfig, {"size": 20})
    assert config.size == 20

    config = decode(NumericLiteralConfig, {"size": 30})
    assert config.size == 30


def test_numeric_literal_invalid():
    with pytest.raises(Exception) as exc_info:
        decode(NumericLiteralConfig, {"size": 15})
    assert "into one of" in str(exc_info.value)


def test_mixed_literal_valid():
    # Test string value
    config = decode(MixedLiteralConfig, {"mode": "train", "size": "small"})
    assert config.mode == "train"
    assert config.size == "small"

    # Test numeric value
    config = decode(MixedLiteralConfig, {"mode": 1, "size": 20})
    assert config.mode == 1
    assert config.size == 20

    # Test boolean value
    config = decode(MixedLiteralConfig, {"mode": True, "size": False})
    assert config.mode is True
    assert config.size is False


def test_mixed_literal_invalid():
    with pytest.raises(Exception) as exc_info:
        decode(MixedLiteralConfig, {"mode": "invalid", "size": "small"})
    assert "into one of" in str(exc_info.value)

    with pytest.raises(Exception) as exc_info:
        decode(MixedLiteralConfig, {"mode": "train", "size": 15})
    assert "into one of" in str(exc_info.value)


def test_literal_help_text():
    """Test that help text is generated correctly for literal types."""
    # Test string literal help
    config = StringLiteralConfig.get_help_text("--help")
    help_text = str(config)
    assert "mode" in help_text
    assert "train" in help_text
    assert "eval" in help_text
    assert "test" in help_text
    assert "{small,medium,large}" in help_text

    # Test numeric literal help
    config = NumericLiteralConfig.get_help_text("--help")
    help_text = str(config)
    assert "size" in help_text
    assert "10" in help_text
    assert "20" in help_text
    assert "30" in help_text
    assert "{10,20,30}" in help_text

    # Test mixed literal help
    config = MixedLiteralConfig.get_help_text("--help")
    help_text = str(config)
    assert "mode" in help_text
    assert "train" in help_text
    assert "1" in help_text
    assert "True" in help_text
    assert "size" in help_text
    assert "small" in help_text
    assert "20" in help_text
    assert "False" in help_text


def test_literal_argparse_valid():
    """Test that literal types work correctly with argparse."""
    # Test string literal
    config = parse(StringLiteralConfig, args=["--mode", "train"])
    assert config.mode == "train"

    config = parse(StringLiteralConfig, args=["--mode", "eval"])
    assert config.mode == "eval"

    # Test numeric literal
    config = parse(NumericLiteralConfig, args=["--size", "10"], exit_on_error=False)
    assert config.size == 10

    config = parse(NumericLiteralConfig, args=["--size", "30"])
    assert config.size == 30

    # Test mixed literals
    config = parse(MixedLiteralConfig, args=["--mode", "train", "--size", "small"])
    assert config.mode == "train"
    assert config.size == "small"

    config = parse(MixedLiteralConfig, args=["--mode", "1", "--size", "20"])
    assert config.mode == 1
    assert config.size == 20

    config = parse(MixedLiteralConfig, args=["--mode", "True", "--size", "False"])
    assert config.mode is True
    assert config.size is False


def test_literal_argparse_invalid():
    """Test that invalid literal values are caught by argparse."""
    # Test string literal
    with pytest.raises(SystemExit):
        parse(StringLiteralConfig, args=["--mode", "invalid"])

    # Test numeric literal
    with pytest.raises(SystemExit):
        parse(NumericLiteralConfig, args=["--size", "15"])

    # Test mixed literals
    with pytest.raises(SystemExit):
        parse(MixedLiteralConfig, args=["--mode", "invalid", "--size", "20"])

    with pytest.raises(SystemExit):
        parse(MixedLiteralConfig, args=["--mode", "train", "--size", "3"])
