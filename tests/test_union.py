from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Union

import pytest

from draccus import utils
from draccus.utils import DecodingError

from .testutils import *


def test_union_type():
    @dataclass
    class Foo(TestSetup):
        x: Union[float, str] = 0

    Foo.get_help_text()

    foo = Foo.setup("--x 1.2")
    assert foo.x == 1.2

    foo = Foo.setup("--x bob")
    assert foo.x == "bob"


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_union_types_39():
    assert utils.is_union(float | str)

    @dataclass
    class Foo(TestSetup):
        x: float | str = 0

    foo = Foo.setup("--x 1.2")
    assert foo.x == 1.2

    foo = Foo.setup("--x bob")
    assert foo.x == "bob"


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_union_types_39_optional():
    @dataclass
    class Foo(TestSetup):
        x: Optional[float | str] = 0

    foo = Foo.setup("--x 1.2")
    assert foo.x == 1.2

    foo = Foo.setup("--x bob")
    assert foo.x == "bob"

    foo = Foo.setup("--x null")
    assert foo.x is None


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_union_types_39_optional_nested():
    @dataclass
    class Foo(TestSetup):
        x: Union[float, int | str] = 0

    foo = Foo.setup("--x 1.2")
    assert foo.x == 1.2

    foo = Foo.setup("--x bob")
    assert foo.x == "bob"


def test_union_error_message_atomics():
    @dataclass
    class Foo(TestSetup):
        x: Union[float, bool] = 0

    with pytest.raises(DecodingError) as e:
        Foo.setup("--x 1.2.3")

    assert """`x`: Could not decode the value into any of the given types:
    float: Couldn't parse '1.2.3' into a float
    bool: Couldn't parse '1.2.3' into a bool""" in str(
        e.value
    )


def test_union_error_message_nested():
    @dataclass
    class Foo(TestSetup):
        x: Union[float, Union[int, bool]] = 0

    with pytest.raises(DecodingError) as e:
        Foo.setup("--x 1.2.3")

    assert """`x`: Could not decode the value into any of the given types:
    float: Couldn't parse '1.2.3' into a float
    int: Couldn't parse '1.2.3' into an int
    bool: Couldn't parse '1.2.3' into a bool""" in str(
        e.value
    )


@dataclass(frozen=True)
class Baz_u:
    z: int


@dataclass
class Foo_u(TestSetup):
    x: Union[bool, Baz_u]


def test_decode_union_with_dataclass_and_atomic():
    foo = Foo_u.setup("--x false")
    assert foo.x is False

    foo = Foo_u.setup("--x.z 1")
    assert foo.x == Baz_u(z=1)

    try:
        foo = Foo_u.setup("--x.z 1.2")
        raise AssertionError()
    except DecodingError:
        pass


@dataclass(frozen=True)
class Baz_e:
    z: int
    y: str


@dataclass(frozen=True)
class Bar_e:
    z: bool


@dataclass
class Foo_e(TestSetup):
    x: Union[Baz_e, Bar_e] = Bar_e(False)


def test_union_error_message_dataclasses():
    with pytest.raises(DecodingError) as e:
        Foo_e.setup("--x.z 1.2.3")

    assert """`x`: Could not decode the value into any of the given types:
    Baz_e: `z`: Couldn't parse '1.2.3' into an int
    Bar_e: `z`: Couldn't parse '1.2.3' into a bool""".strip() in str(
        e.value
    )

    with pytest.raises(DecodingError) as e:
        Foo_e.setup("--x.y foo")

    assert """`x`: Could not decode the value into any of the given types:
    Baz_e: Missing required field(s) `z` for Baz_e
    Bar_e: The fields `y` are not valid for Bar_e""".strip() in str(
        e.value
    )


@dataclass
class Bar:
    y: int


@dataclass
class Foo(TestSetup):
    x: Optional[Union[Bar, Dict[str, Bar]]] = field(default=None)


def test_union_argparse_dict():
    foo = Foo.setup('--x \'{"a": {"y": 1}, "b": {"y": 2}}\'')
    assert foo.x == {"a": Bar(y=1), "b": Bar(y=2)}
