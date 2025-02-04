import json
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Tuple

import yaml

from draccus.utils import DraccusException

from .testutils import *


class Color(Enum):
    blue = auto()
    red = auto()


def test_encode_something(simple_attribute):
    some_type, _, expected_value = simple_attribute

    @dataclass(frozen=True)
    class SomeClass:
        d: Dict[str, some_type] = field(default_factory=dict)
        l: List[Tuple[some_type, some_type]] = field(default_factory=list)
        t: Dict[str, Optional[some_type]] = field(default_factory=dict)

    b = SomeClass()
    b.d.update({"hey": expected_value})
    b.l.append((expected_value, expected_value))
    b.t.update({"hey": None, "hey2": expected_value})

    assert draccus.decode(SomeClass, draccus.encode(b)) == b


@parametrize("config_type", ["", "yaml", "json", "toml"])
def test_dump_load(simple_attribute, config_type, tmp_path):
    some_type, _, expected_value = simple_attribute

    if config_type != "":
        draccus.set_config_type(config_type)

    @dataclass(frozen=True)
    class SomeClass:
        val: Optional[some_type] = None

    b = SomeClass(val=expected_value)

    tmp_file = tmp_path / "config"
    draccus.dump(b, tmp_file.open("w"))

    new_b = draccus.parse(config_class=SomeClass, config_path=tmp_file, args="")
    assert new_b == b

    arguments = shlex.split(f"--config_path {tmp_file}")
    new_b = draccus.parse(config_class=SomeClass, args=arguments)
    assert new_b == b

    new_b = draccus.parse(config_class=SomeClass, args="")
    assert new_b != b

    draccus.set_config_type("yaml")


def test_dump_load_context():
    @dataclass
    class SomeClass:
        val: str = "hello"

    b = SomeClass()

    yaml_str = draccus.dump(b)
    assert yaml_str == yaml.dump(draccus.encode(b))

    with draccus.config_type("json"):
        json_str = draccus.dump(b)
        assert json_str == json.dumps(draccus.encode(b))

    yaml_str = draccus.dump(b)
    assert yaml_str == yaml.dump(draccus.encode(b))

    assert draccus.get_config_type() is draccus.ConfigType.YAML


def test_dump_load_dicts(simple_attribute, tmp_path):
    some_type, _, expected_value = simple_attribute

    @dataclass(frozen=True)
    class SomeClass:
        d: Dict[str, some_type] = field(default_factory=dict)
        l: List[Tuple[some_type, some_type]] = field(default_factory=list)
        t: Dict[str, Optional[some_type]] = field(default_factory=dict)

    b = SomeClass()
    b.d.update({"hey": expected_value})
    b.l.append((expected_value, expected_value))
    b.t.update({"hey": None, "hey2": expected_value})

    tmp_file = tmp_path / "config"
    draccus.dump(b, tmp_file.open("w"))

    new_b = draccus.parse(config_class=SomeClass, config_path=tmp_file, args="")
    assert new_b == b
    arguments = shlex.split(f"--config_path {tmp_file}")
    new_b = draccus.parse(config_class=SomeClass, args=arguments)
    assert new_b == b


def test_dump_load_enum(tmp_path):
    @dataclass
    class SomeClass:
        color: Color = Color.red

    b = SomeClass()
    tmp_file = tmp_path / "config.yaml"
    draccus.dump(b, tmp_file.open("w"))

    new_b = draccus.parse(config_class=SomeClass, config_path=tmp_file, args="")
    assert new_b == b


def test_reserved_config_word():
    @dataclass
    class MainClass:
        config_path: str = ""

    with raises(DraccusException):
        draccus.parse(MainClass)


def test_super_nesting():
    @dataclass
    class Complicated:
        x: List[List[List[Dict[int, Tuple[int, float, str, List[float]]]]]] = field(default_factory=list)

    c = Complicated()
    c.x = [[[{0: (2, 1.23, "bob", [1.2, 1.3])}]]]
    assert draccus.decode(Complicated, draccus.encode(c)) == c
