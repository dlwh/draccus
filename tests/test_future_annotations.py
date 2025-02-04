from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

import draccus

# it seems like typing.gettypehints doesn't really work with locals so, we just make these module scope


@dataclass(frozen=True)
class A:
    b: int = 1


@dataclass(frozen=True)
class C:
    a: A = A()
    elems: List[A] = field(default_factory=list)


def test_future_annotations():
    an_a: A = draccus.parse(config_class=A, args="")
    assert an_a.b == 1


def test_nested_future_annotations():
    c: C = draccus.parse(config_class=C, args="")
    assert c.a.b == 1
