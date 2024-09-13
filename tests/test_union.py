from dataclasses import dataclass
from typing import Union

import pytest

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


def test_decode_union_with_dataclass_and_atomic():
    @dataclass
    class Baz:
        z: int

    @dataclass
    class Foo(TestSetup):
        x: Union[bool, Baz]

    foo = Foo.setup("--x false")
    assert foo.x is False

    foo = Foo.setup("--x.z 1")
    assert foo.x == Baz(z=1)

    try:
        foo = Foo.setup("--x.z 1.2")
        raise AssertionError()
    except DecodingError:
        pass


def test_union_error_message_dataclasses():
    @dataclass
    class Baz:
        z: int
        y: str

    @dataclass
    class Bar:
        z: bool

    @dataclass
    class Foo(TestSetup):
        x: Union[Baz, Bar] = 0

    with pytest.raises(DecodingError) as e:
        Foo.setup("--x.z 1.2.3")

    assert """`x`: Could not decode the value into any of the given types:
    Baz: `z`: Couldn't parse '1.2.3' into an int
    Bar: `z`: Couldn't parse '1.2.3' into a bool""".strip() in str(
        e.value
    )

    with pytest.raises(DecodingError) as e:
        Foo.setup("--x.y foo")

    assert """`x`: Could not decode the value into any of the given types:
    Baz: Missing required field(s) `z` for Baz
    Bar: The fields `y` are not valid for Bar""".strip() in str(
        e.value
    )
