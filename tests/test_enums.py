from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List

from draccus import ParsingError, encode, decode

from .testutils import TestSetup, raises


class Color(str, Enum):
    blue: str = auto()  # type: ignore
    red: str = auto()  # type: ignore
    green: str = auto()  # type: ignore
    orange: str = auto()  # type: ignore


class BigColor(str, Enum):
    BLUE: str = "blue"
    RED: str = "red"
    GREEN: str = "green"
    TRICKY: str = "orange"

class Option(int, Enum):
    ONE: int = 1
    TWO: int = 2
    THREE: int = 3

def test_encode_decode():
    @dataclass
    class Something(TestSetup):
        favorite_color: Color = field(default=Color.green)
        favorite_big_color: BigColor = field(default=BigColor.GREEN)
        option: Option = field(default=Option.ONE)
        colors: List[Color] = field(default_factory=[Color.green].copy)

    s = Something.setup("")
    s_decoded = decode(Something, encode(s))
    assert s_decoded.favorite_color == s.favorite_color
    assert s_decoded.favorite_big_color == s.favorite_big_color
    assert s_decoded.option == s.option
    assert s_decoded.colors == s.colors

def test_passing_enum_to_choice():
    @dataclass
    class Something(TestSetup):
        favorite_color: Color = field(default=Color.green)
        colors: List[Color] = field(default_factory=[Color.green].copy)

    s = Something.setup("")
    assert s.favorite_color == Color.green
    assert s.colors == [Color.green]

    s = Something.setup("--colors [blue,red]")
    assert s.colors == [Color.blue, Color.red]


def test_passing_enum_to_choice_from_value():
    @dataclass
    class Something(TestSetup):
        favorite_color: BigColor = field(default=BigColor.GREEN)
        colors: List[BigColor] = field(default_factory=[BigColor.GREEN].copy)

    s = Something.setup("")
    assert s.favorite_color == BigColor.GREEN
    assert s.colors == [BigColor.GREEN]

    s = Something.setup("--colors '[blue, red]'")
    assert s.colors == [BigColor.BLUE, BigColor.RED]

    # try tricky
    s = Something.setup("--colors '[blue,orange]'")
    assert s.colors == [BigColor.BLUE, BigColor.TRICKY]


#
#
def test_passing_enum_to_choice_no_default_makes_required_arg():
    @dataclass
    class Something(TestSetup):
        favorite_color: Color = field()

    with raises(ParsingError):
        s = Something.setup("")

    s = Something.setup("--favorite_color blue")
    assert s.favorite_color == Color.blue


def test_passing_enum_to_choice_is_same_as_enum_attr():
    @dataclass
    class Something1(TestSetup):
        favorite_color: Color = Color.orange

    @dataclass
    class Something2(TestSetup):
        favorite_color: Color = field(default=Color.orange)

    s1 = Something1.setup("--favorite_color green")
    s2 = Something2.setup("--favorite_color green")
    assert s1.favorite_color == s2.favorite_color

    s = Something1.setup("--favorite_color blue")
    assert s.favorite_color == Color.blue
    s = Something2.setup("--favorite_color blue")
    assert s.favorite_color == Color.blue
