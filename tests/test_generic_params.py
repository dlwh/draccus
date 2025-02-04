# tests that draccus can correctly parse and use generic parameters
from dataclasses import dataclass
from typing import Generic, List, TypeVar

import draccus

T = TypeVar("T")


@dataclass
class ScheduleStep(Generic[T]):
    until: int
    value: T


@dataclass
class Schedule(Generic[T]):
    phases: List[ScheduleStep[T]]


def test_generic_params():
    decoded = draccus.decode(Schedule[int], {"phases": [{"until": 10, "value": 1}]})

    assert decoded == Schedule(phases=[ScheduleStep(until=10, value=1)])

    encoded = draccus.encode(Schedule[int](phases=[ScheduleStep(until=10, value=1)]))

    assert encoded == {"phases": [{"until": 10, "value": 1}]}

    list_decoded = draccus.decode(List[ScheduleStep[int]], [{"until": 10, "value": 1}])

    assert list_decoded == [ScheduleStep(until=10, value=1)]
