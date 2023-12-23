from dataclasses import dataclass
from typing import Tuple

import pytest

from draccus import ParsingError
from draccus.utils import DecodingError
from tests.testutils import TestSetup


def test_tuple_with_n_items_takes_only_n_values():
    @dataclass
    class Container(TestSetup):
        ints: Tuple[int, int] = (1, 5)

    c = Container.setup("")
    assert c.ints == (1, 5)
    c = Container.setup("--ints [4,8]")
    assert c.ints == (4, 8)
    with pytest.raises(DecodingError) as e:
        c = Container.setup("--ints [4,5,6,7,8]")

    assert "Expected 2 items, got 5" in str(e.value)
    assert e.value.key_path == ("ints",)


def test_tuple_elipsis_takes_any_number_of_args():
    @dataclass
    class Container(TestSetup):
        ints: Tuple[int, ...] = (1, 2, 3)

    c = Container.setup("")
    assert c.ints == (1, 2, 3)
    c = Container.setup("--ints '[4, 5, 6, 7, 8]'")
    assert c.ints == (4, 5, 6, 7, 8)


def test_each_type_is_used_correctly():
    @dataclass
    class Container(TestSetup):
        """A container with mixed items in a tuple."""

        mixed: Tuple[int, str, bool, float] = (1, "bob", False, 1.23)

    c = Container.setup("")
    assert c.mixed == (1, "bob", False, 1.23)

    c = Container.setup("--mixed [1,2,false,1]")
    assert c.mixed == (1, "2", False, 1.0)
