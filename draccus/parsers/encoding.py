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
from logging import getLogger
from os import PathLike
from typing import Any, Dict, Hashable, List, Optional, Tuple, Type, Union

from draccus import utils
from draccus.choice_types import CHOICE_TYPE_KEY
from draccus.parsers.registry_utils import RegistryFunc, withregistry
from draccus.utils import is_choice_type

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


@withregistry
def encode(obj: Any, declared_type: Optional[Type] = None) -> Any:
    """Encodes an object into a json/yaml-compatible primitive type.

    Args:
        obj: The object to encode
        declared_type: Optional type annotation for the object. Used to determine if the object
                      should be encoded as a choice type based on its declared type rather than
                      its concrete type.
    """
    if declared_type is not None:
        underlying_type = typing.get_origin(declared_type) or declared_type
        # we have to handle unions specially for declared types:
        if utils.is_union(declared_type):
            # find the first type that matches the object's type
            for t in typing.get_args(declared_type):
                # we can't use subscripted generic types here
                if typing.get_origin(t) is typing.Literal:
                    for arg in typing.get_args(t):
                        if arg == obj:
                            underlying_type = t
                            declared_type = t
                            break
                elif isinstance(obj, typing.get_origin(t) or t):
                    underlying_type = typing.get_origin(t) or t
                    declared_type = t
                    break
    else:
        underlying_type = type(obj)
    cached_func: RegistryFunc = encode.dispatch(underlying_type)

    if cached_func is None:
        # see if the actual type has a custom encoder
        cached_func = encode.dispatch(type(obj))

    if cached_func is not None:
        fn = cached_func.func

        # we want to support the old interface where the decoding function
        # takes only one argument, so we wrap it here
        try:
            return fn(obj, declared_type)
        except TypeError:
            try:
                return fn(obj)
            except Exception as e:  # pylint: disable=broad-except
                raise Exception(f"Couldn't encode {obj}") from e

    try:
        if underlying_type is not None and is_choice_type(underlying_type):
            return encode_choice(obj, underlying_type)
        elif is_dataclass(obj):
            return encode_dataclass(obj, declared_type)
        elif obj is None:
            return None
        else:
            raise Exception(f"No parser for object {obj} of type {type(obj)}, consider using draccus.encode.register")
    except Exception as e:
        logger.debug(f"Cannot encode object {obj}: {e}")
        raise e


def encode_dataclass(obj: Any, declared_type: Optional[Type] = None):
    d: Dict[str, Any] = dict()

    # Handle type parameters if declared_type is provided
    type_map: Dict = {}
    if declared_type is not None:
        # Build a type_map only when declared_type's origin or itself defines real type parameters
        origin = typing.get_origin(declared_type) or declared_type
        type_vars = getattr(origin, "__parameters__", ()) or ()
        if isinstance(type_vars, tuple) and type_vars:
            type_args = typing.get_args(declared_type)
            type_map = dict(zip(type_vars, type_args))

    for field in fields(obj):
        value = getattr(obj, field.name)
        try:
            # If we have a type map, use it to resolve the field's type
            field_type = field.type
            if type_map and hasattr(field_type, "__parameters__"):
                field_type = field_type[tuple(type_map.get(p, p) for p in field_type.__parameters__)]
            d[field.name] = encode(value, field_type)
        except TypeError as e:
            logger.error(f"Unable to encode field {field.name}: {e}")
            raise e
    return d


def encode_choice(obj: Any, declared_type: Type) -> Dict[str, Any]:
    """Encodes an object as a choice type based on its declared type.

    Args:
        obj: The object to encode
        declared_type: The type annotation for the object, which must be a choice type
    """
    if not is_choice_type(declared_type):
        raise ValueError(f"Expected a choice type, got {declared_type}")

    encoded = encode_dataclass(obj, declared_type)

    if not isinstance(encoded, dict):
        raise Exception(f"Choice Class {obj} is not encoded as a dict: {encoded}")

    # Get the choice name from the declared type
    choice_name = obj.get_choice_name(type(obj))
    encoded = {CHOICE_TYPE_KEY: choice_name, **encoded}

    return encoded


@encode.register(Mapping, include_subclasses=True)
def encode_dict(
    obj: Mapping, declared_type: Optional[Type] = None
) -> Union[typing.Mapping[Any, Any], List[Tuple[Any, Any]]]:
    constructor = type(obj)
    result: Union[Mapping, List[Tuple[Any, Any]]] = constructor()

    # Handle type parameters if declared_type is provided
    key_type = None
    value_type = None
    if declared_type is not None:
        type_args = typing.get_args(declared_type)
        if len(type_args) >= 2:
            key_type, value_type = type_args[:2]

    for k, v in obj.items():
        k_ = encode(k, key_type)
        v_ = encode(v, value_type)
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


@encode.register(Enum, include_subclasses=True)
def encode_enum(obj: Enum, declared_type: Optional[Type] = None) -> str:
    return obj.name


for t in [str, float, int, bool, bytes]:
    # subclass enums
    encode.register(t, lambda x, _=None: x, include_subclasses=True)


@encode.register(list)
def encode_list(obj: list, declared_type: Optional[Type] = None) -> list:
    item_type = None
    if declared_type is not None:
        type_args = typing.get_args(declared_type)
        if type_args:
            item_type = type_args[0]
    return [encode(x, item_type) for x in obj]


@encode.register(tuple)
def encode_tuple(obj: tuple, declared_type: Optional[Type] = None) -> list:
    if declared_type is not None:
        type_args = typing.get_args(declared_type)
        if type_args and len(type_args) == len(obj):
            return [encode(x, t) for x, t in zip(obj, type_args)]
        elif type_args and len(type_args) == 2 and type_args[1] is Ellipsis:
            item_type = type_args[0]
            return [encode(x, item_type) for x in obj]
    return [encode(x) for x in obj]


@encode.register(set)
def encode_set(obj: set, declared_type: Optional[Type] = None) -> list:
    item_type = None
    if declared_type is not None:
        type_args = typing.get_args(declared_type)
        if type_args:
            item_type = type_args[0]
    return [encode(x, item_type) for x in obj]


encode.register(PathLike, lambda x, _=None: x.__fspath__(), include_subclasses=True)

encode.register(Namespace, lambda x, _=None: encode(vars(x)))
