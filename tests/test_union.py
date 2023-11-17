from dataclasses import dataclass
from typing import Union

import pytest

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
