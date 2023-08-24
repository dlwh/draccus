"""Simple, extendable mechanism for encoding pracitaclly anything to string.

Just register a new encoder for a given type like so:

import draccus
import numpy as np
@draccus.encode.register
def encode_ndarray(obj: np.ndarray) -> str:
    return obj.tostring()
"""
import json
import typing
from argparse import Namespace
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from functools import singledispatch
from logging import getLogger
from os import PathLike
from typing import Any, Dict, Hashable, List, Tuple, Union

from draccus.choice_types import CHOICE_TYPE_KEY, ChoiceType

logger = getLogger(__name__)


class SimpleJsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        return encode(o)


"""
# NOTE: This code is commented because of static typing check error.
# The problem is incompatibility of mypy and singledispatch.
# See mypy issues for more info:
# https://github.com/python/mypy/issues/8356
# https://github.com/python/mypy/issues/2904
# https://github.com/python/mypy/issues/9112#issuecomment-725316936

class Dataclass(Protocol):
    # see dataclasses.is_dataclass implementation with _FIELDS
    __dataclass_fields__: Dict[str, Field[Any]]


T = TypeVar("T", bool, int, None, str)


@overload
def encode(obj: Dataclass) -> Dict[str, Any]: ...

@overload
def encode(obj: Union[List[Any], Set[Any], Tuple[Any, ...]]) -> List[Any]:
    ...

@overload
def encode(obj: Mapping[Any, Any]) -> Dict[Any, Any]: ...

@overload
def encode(obj: T) -> T: ...
"""


@singledispatch
def encode(obj: Any) -> Any:
    """Encodes an object into a json/yaml-compatible primitive type."""
    try:
        if isinstance(obj, ChoiceType):
            return encode_choice(obj)
        elif is_dataclass(obj):
            return encode_dataclass(obj)
        elif obj is None:
            return None
        else:
            raise Exception(f"No parser for object {obj} of type {type(obj)}, consider using draccus.encode.register")
    except Exception as e:
        logger.debug(f"Cannot encode object {obj}: {e}")
        raise e


def encode_dataclass(obj: Any):
    d: Dict[str, Any] = dict()
    for field in fields(obj):
        value = getattr(obj, field.name)
        try:
            d[field.name] = encode(value)
        except TypeError as e:
            logger.error(f"Unable to encode field {field.name}: {e}")
            raise e
    return d


def encode_choice(obj: ChoiceType):
    encoded = encode_dataclass(obj)

    if not isinstance(encoded, dict):
        raise Exception(f"Choice Class {obj} is not encoded as a dict: {encoded}")

    encoded = {CHOICE_TYPE_KEY: obj.get_choice_name(type(obj)), **encoded}

    return encoded


@encode.register(Mapping)
def encode_dict(obj: Mapping) -> Union[typing.Mapping[Any, Any], List[Tuple[Any, Any]]]:
    constructor = type(obj)
    result: Union[Mapping, List[Tuple[Any, Any]]] = constructor()
    for k, v in obj.items():
        k_ = encode(k)
        v_ = encode(v)
        if isinstance(result, list):
            result.append((k_, v_))
        elif isinstance(k_, Hashable):
            result[k_] = v_  # type: ignore
        else:
            # If the encoded key isn't "Hashable", then we store it as a list of tuples
            if isinstance(result, Mapping):
                result = list(result.items())
            result.append((k_, v_))
    return result


@encode.register(Enum)
def encode_enum(obj: Enum) -> str:
    return obj.name


for t in [str, float, int, bool, bytes]:
    encode.register(t, lambda x: x)

for t in [list, tuple, set]:
    encode.register(t, lambda x: list(map(encode, x)))

encode.register(PathLike, lambda x: x.__fspath__())

encode.register(Namespace, lambda x: encode(vars(x)))
