# test_optional_choice_type.py

import argparse
from dataclasses import dataclass
from typing import Optional

import pytest

import draccus
from draccus.choice_types import ChoiceRegistry
from draccus.utils import DecodingError
from tests.testutils import TestSetup


@dataclass
class Person(ChoiceRegistry):
    name: str


@dataclass
class Adult(Person):
    age: int


@dataclass
class Child(Person):
    favorite_toy: str


Person.register_subclass("adult", Adult)
Person.register_subclass("child", Child)


@dataclass
class Profile(TestSetup):
    person: Optional[Person] = None


def test_optional_choice_empty():
    profile = Profile.setup("")
    assert profile.person is None


def test_optional_choice_adult():
    profile = Profile.setup("--person.type adult --person.name Bob --person.age 30")
    assert profile.person == Adult(name="Bob", age=30)


def test_optional_choice_child():
    profile = Profile.setup("--person.type child --person.name Alice --person.favorite_toy truck")
    assert profile.person == Child(name="Alice", favorite_toy="truck")


def test_invalid_choice():
    with pytest.raises(argparse.ArgumentError):
        Profile.setup("--person.type invalid_type --person.name Jill")


def test_invalid_fields_adult():
    with pytest.raises(DecodingError):
        Profile.setup("--person.type adult --person.name Bob --person.age 30 --person.favorite_toy truck")


def test_encode_optional_none():
    profile = Profile()
    assert draccus.encode(profile) == {"person": None}


def test_encode_optional_child():
    profile = Profile(person=Child(name="Kevin", favorite_toy="ball"))
    encoded = draccus.encode(profile)
    assert encoded == {
        "person": {
            "type": "child",
            "name": "Kevin",
            "favorite_toy": "ball",
        }
    }


def test_encode_optional_adult():
    profile = Profile(person=Adult(name="Bob", age=42))
    encoded = draccus.encode(profile)
    assert encoded == {
        "person": {
            "type": "adult",
            "name": "Bob",
            "age": 42,
        }
    }
