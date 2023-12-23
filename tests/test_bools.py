from dataclasses import dataclass

import pytest

from draccus import ParsingError
from draccus.utils import DecodingError

from .testutils import TestSetup


@dataclass
class Base(TestSetup):
    """Some extension of base-class `Base`"""

    a: int = 5
    f: bool = False


def test_bool_attributes_work():
    true_strings = ["True", "true"]
    for s in true_strings:
        ext = Base.setup(f"--a 5 --f {s}")
        assert ext.f is True

    false_strings = ["False", "false"]
    for s in false_strings:
        ext = Base.setup(f"--a 5 --f {s}")
        assert ext.f is False


def test_bool_doesnt_parse_non_bools():
    with pytest.raises(DecodingError) as e:
        Base.setup("--a 5 --f 5")

    assert e.value.key_path == ("f",)

    with pytest.raises(DecodingError):
        Base.setup("--a 5 --f foo")
