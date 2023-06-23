import dataclasses
from argparse import ArgumentError

import pytest

import draccus
from draccus import ParsingError
from draccus.choice_types import ChoiceRegistry

from .testutils import TestSetup


@dataclasses.dataclass
class Person(ChoiceRegistry):
    name: str


@dataclasses.dataclass
class Adult(Person):
    age: int


@dataclasses.dataclass
class Child(Person):
    favorite_toy: str


Person.register_subclass("adult", Adult)
Person.register_subclass("child", Child)


def test_choice_registry_argparse():
    @dataclasses.dataclass
    class Something(TestSetup):
        person: Person = Adult("bob", 10)

    s = Something.setup("")
    assert s.person == Adult("bob", 10)

    s = Something.setup("--person.type child --person.name bob --person.favorite_toy truck")
    assert s.person == Child("bob", "truck")

    with pytest.raises(ArgumentError):
        Something.setup("--person.type baby --person.name bob")

    with pytest.raises(ParsingError):
        Something.setup("--person.type adult --person.name bob --person.age 10 --person.favorite_toy truck")

    with pytest.raises(ParsingError):
        Something.setup("--person.name hi")


def test_choice_registry_encode():
    assert draccus.encode(Adult("bob", 10)) == {"type": "adult", "name": "bob", "age": 10}
    assert draccus.encode(Child("bob", "truck")) == {"type": "child", "name": "bob", "favorite_toy": "truck"}