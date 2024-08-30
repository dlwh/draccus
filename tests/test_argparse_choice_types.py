import dataclasses

import pytest

from draccus import ParsingError
from draccus.choice_types import ChoiceRegistry

from .testutils import TestSetup


@dataclasses.dataclass
class Person(ChoiceRegistry):
    name: str  # Person's name


@dataclasses.dataclass
class Adult(Person):
    age: int


@dataclasses.dataclass
class Child(Person):
    favorite_toy: str  # Child's favorite toy


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

    with pytest.raises(SystemExit):
        Something.setup("--person.type baby --person.name bob")

    with pytest.raises(ParsingError):
        Something.setup("--person.type adult --person.name bob --person.age 10 --person.favorite_toy truck")

    with pytest.raises(ParsingError):
        Something.setup("--person.name hi")


@dataclasses.dataclass
class Something(TestSetup):
    person: Person = Adult("bob", 10)


def test_choice_registry_examine_help():
    # TODO: why is the default: None here?
    target = """
    usage: draccus [-h] [--config_path str] [--person str]
               [--person.type {adult,child}] [--person.age int]
               [--person.name str] [--person.favorite_toy str]

options:
  -h, --help            show this help message and exit
  --config_path str     Path for a config file to parse with draccus (default:
                        None)
  --person str          Config file for person (default: None)

Something:

Person ['person']:

  --person.type {adult,child}
                        Which type of Person ['person'] to use (default: None)

Adult ['person']:

  --person.name str     Person's name (default: None)
  --person.age int

Child ['person']:

  --person.name str     Person's name (default: None)
  --person.favorite_toy str
                        Child's favorite toy (default: None)
"""
    print(Something.get_help_text().strip())
    assert Something.get_help_text().strip() == target.strip()
