import dataclasses

import pytest

import draccus
from draccus import ParsingError
from draccus.choice_types import ChoiceRegistry


@dataclasses.dataclass
class Person(ChoiceRegistry):
    name: str  # Person's name


@dataclasses.dataclass
class Adult(Person):
    age: int


@dataclasses.dataclass
class Child(Person):
    favorite_toy: str


Person.register_subclass("adult", Adult)
Person.register_subclass("child", Child)


def test_choice_registry_decode():
    assert draccus.decode(Person, {"type": "adult", "name": "bob", "age": 10}) == Adult("bob", 10)
    assert draccus.decode(Person, {"type": "child", "name": "bob", "favorite_toy": "truck"}) == Child("bob", "truck")

    with pytest.raises(ParsingError):
        draccus.decode(Person, {"type": "baby", "name": "bob"})

    with pytest.raises(ParsingError):
        draccus.decode(Person, {"type": "adult", "name": "bob", "age": 10, "favorite_toy": "truck"})

    with pytest.raises(ParsingError):
        draccus.decode(Person, {"type": "adult", "name": 3})


def test_choice_registry_encode():
    assert draccus.encode(Adult("bob", 10)) == {"type": "adult", "name": "bob", "age": 10}
    assert draccus.encode(Child("bob", "truck")) == {"type": "child", "name": "bob", "favorite_toy": "truck"}
