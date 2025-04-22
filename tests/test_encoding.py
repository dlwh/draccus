import enum
import sys
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Generic, Literal, Tuple, Union

from draccus import ChoiceRegistry, decode, encode

from .testutils import *


class Color(Enum):
    blue = auto()
    red = auto()


def test_encode_basic_types():
    # Test basic types
    assert encode(42) == 42
    assert encode(3.14) == 3.14
    assert encode("hello") == "hello"
    assert encode(True) is True
    assert encode(None) is None


def test_encode_enum():
    assert encode(Color.blue) == "blue"
    assert encode(Color.red) == "red"


def test_encode_list():
    # Test list with and without type parameters
    assert encode([1, 2, 3]) == [1, 2, 3]
    assert encode(["a", "b", "c"]) == ["a", "b", "c"]
    assert encode([Color.blue, Color.red]) == ["blue", "red"]


def test_encode_tuple():
    # Test tuple with and without type parameters
    assert encode((1, 2, 3)) == [1, 2, 3]
    assert encode(("a", "b", "c")) == ["a", "b", "c"]
    assert encode((Color.blue, Color.red)) == ["blue", "red"]


def test_encode_dict():
    # Test dict with and without type parameters
    assert encode({"a": 1, "b": 2}) == {"a": 1, "b": 2}
    assert encode({"a": Color.blue, "b": Color.red}) == {"a": "blue", "b": "red"}
    assert encode({1: "a", 2: "b"}) == {1: "a", 2: "b"}


def test_encode_dataclass():
    @dataclass
    class SimpleClass:
        x: int
        y: str
        z: Optional[Color] = None

    obj = SimpleClass(42, "hello", Color.blue)
    expected = {"x": 42, "y": "hello", "z": "blue"}
    assert encode(obj) == expected

    obj = SimpleClass(42, "hello")
    expected = {"x": 42, "y": "hello", "z": None}
    assert encode(obj) == expected


def test_encode_nested_dataclass():
    @dataclass
    class Inner:
        a: int
        b: str

    @dataclass
    class Outer:
        inner: Inner
        c: List[Inner]

    obj = Outer(Inner(1, "a"), [Inner(2, "b"), Inner(3, "c")])
    expected = {"inner": {"a": 1, "b": "a"}, "c": [{"a": 2, "b": "b"}, {"a": 3, "b": "c"}]}
    assert encode(obj) == expected


def test_encode_generic_dataclass():
    @dataclass
    class Container(Generic[T]):
        value: T
        items: List[T]

    obj = Container[int](value=42, items=[1, 2, 3])
    expected = {"value": 42, "items": [1, 2, 3]}
    assert encode(obj) == expected

    obj = Container[str](value="hello", items=["a", "b"])
    expected = {"value": "hello", "items": ["a", "b"]}
    assert encode(obj) == expected


def test_encode_complex_nesting():
    @dataclass
    class Complicated:
        x: List[List[List[Dict[int, Tuple[int, float, str, List[float]]]]]]

    obj = Complicated([[[{0: (2, 1.23, "bob", [1.2, 1.3])}]]])
    expected = {"x": [[[{0: [2, 1.23, "bob", [1.2, 1.3]]}]]]}
    assert encode(obj) == expected


class Animal(ChoiceRegistry):
    pass


@Animal.register_subclass("dog")
@dataclass
class Dog(Animal):
    name: str
    age: int


@Animal.register_subclass("cat")
@dataclass
class Cat(Animal):
    name: str
    lives: int


@dataclass
class Zoo:
    animals: List[Animal]

    def __post_init__(self):
        assert all(isinstance(a, Animal) for a in self.animals)


def test_encode_choice_type():

    dog = Dog("Fido", 3)
    expected = {"type": "dog", "name": "Fido", "age": 3}
    assert encode(dog, Animal) == expected

    assert encode(dog) == {"name": "Fido", "age": 3}

    cat = Cat("Whiskers", 9)
    expected = {"type": "cat", "name": "Whiskers", "lives": 9}
    assert encode(cat, Animal) == expected
    expected = {"name": "Whiskers", "lives": 9}
    assert encode(cat) == expected


def test_encode_choice_type_in_generic():
    from draccus.choice_types import ChoiceRegistry

    dog = Dog("Fido", 3)
    cat = Cat("Whiskers", 9)

    zoo = Zoo([dog, cat])
    expected = {"animals": [{"type": "dog", "name": "Fido", "age": 3}, {"type": "cat", "name": "Whiskers", "lives": 9}]}
    assert encode(zoo) == expected

    @dataclass
    class Home:
        animals: List[Union[Dog, Cat]]

        def __post_init__(self):
            assert all(isinstance(a, Animal) for a in self.animals)

    home = Home([dog, cat])
    expected = {"animals": [{"name": "Fido", "age": 3}, {"name": "Whiskers", "lives": 9}]}
    assert encode(home) == expected


def test_encode_generic_union_member():
    @dataclass
    class Foo:
        x: Union[List[int], str]

        def __post_init__(self):
            assert isinstance(self.x, list) or isinstance(self.x, str)

    assert encode(Foo(x=[1, 2, 3])) == {"x": [1, 2, 3]}
    assert encode(Foo(x="hello")) == {"x": "hello"}


def test_encode_literal_union_member():
    @dataclass
    class Foo:
        x: Union[Literal["a", "b"], int]

        def __post_init__(self):
            assert isinstance(self.x, int) or self.x in ["a", "b"]

    assert encode(Foo(x=1)) == {"x": 1}
    assert encode(Foo(x="a")) == {"x": "a"}


def test_encode_path():
    from pathlib import Path

    assert encode(Path("/tmp")) == "/tmp"


class ActivationFunctionEnum(str, enum.Enum):
    relu = "relu"
    silu = "silu"
    swish = "swish"
    gelu = "gelu"
    gelu_new = "gelu_new"
    quick_gelu = "quick_gelu"
    tanh = "tanh"


def test_encode_enum_str():

    assert encode(ActivationFunctionEnum.relu) == "relu"
    assert encode(ActivationFunctionEnum.silu) == "silu"
    assert encode(ActivationFunctionEnum.swish) == "swish"
    assert encode(ActivationFunctionEnum.gelu) == "gelu"

    # test roundtrip
    assert decode(ActivationFunctionEnum, "relu") == ActivationFunctionEnum.relu


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_encode_dataclass_type_parameters_error():
    from dataclasses import dataclass

    from draccus.parsers.encoding import encode_dataclass

    @dataclass
    class ListHolder:
        x: list[int] | str

    encode_dataclass(ListHolder([1]), declared_type=ListHolder)

    @dataclass
    class ListHolder2:
        x: list[int] | str

    encode(ListHolder([1]), declared_type=ListHolder | ListHolder2)
