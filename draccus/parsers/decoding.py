""" Functions for decoding dataclass fields from "raw" values (e.g. from json).
"""
import functools
import typing
from collections import OrderedDict
from dataclasses import MISSING, fields, is_dataclass
from functools import lru_cache, partial
from logging import getLogger
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Protocol, Sequence, Set, Tuple, Type, TypeVar, Union

from draccus.choice_types import CHOICE_TYPE_KEY, ChoiceType
from draccus.parsers.registry_utils import RegistryFunc, withregistry
from draccus.utils import (
    DecodingError,
    ParsingError,
    canonicalize_union,
    format_error,
    get_type_arguments,
    has_generic_arg,
    is_choice_type,
    is_dict,
    is_enum,
    is_list,
    is_set,
    is_tuple,
    is_union,
    stringify_type,
)

logger = getLogger(__name__)

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
K = TypeVar("K")
V = TypeVar("V")
Dataclass = TypeVar("Dataclass")


class DecodingFunction(Protocol[T_co]):
    def __call__(self, raw_value: Any, path: Sequence[str]) -> T_co:
        ...


@withregistry
def decode(cls: Type[T], raw_value: Any) -> T:
    cls = canonicalize_union(cls)
    return get_decoding_fn(cls)(raw_value, ())  # type: ignore


def decode_from_init(cls: Type[T], raw_value: Any, path: Sequence[str]) -> T:
    """Decodes a value into an atomic type (e.g. str, int, float, etc.)."""
    try:
        return cls(raw_value)  # type: ignore
    except Exception as e:
        raise DecodingError(path, f"Couldn't parse '{raw_value}' into a {stringify_type(cls)}") from e


for t in [str, float, bytes]:
    decode.register(t, partial(decode_from_init, t))


@decode.register(bool)
def decode_bool(raw_value: Any, path) -> bool:
    # only accept yaml 1.2 bools
    if raw_value is True or raw_value == "true":
        return True
    elif raw_value is False or raw_value == "false":
        return False
    else:
        raise DecodingError(path, f"Couldn't parse '{raw_value}' into a bool")


@decode.register(int)
def decode_int(raw_value: Any, path) -> int:
    try:
        # reject floats etc:
        if isinstance(raw_value, float):
            raise ValueError(f"Expected an int, got a float: {raw_value}")
        return int(raw_value)
    except ValueError as e:
        raise DecodingError(path, f"Couldn't parse '{raw_value}' into an int") from e


def decode_dataclass(cls: Type[Dataclass], d: Dict[str, Any], path: Sequence[str] = ()) -> Dataclass:
    """Parses an instance of the dataclass `cls` from the dict `d`."""
    # if d is None:
    #     return None

    path = tuple(path)

    obj_dict: Dict[str, Any] = d.copy()

    init_args: Dict[str, Any] = {}
    non_init_args: Dict[str, Any] = {}

    logger.debug(f"from_dict for {cls}")

    for field in fields(cls):  # type: ignore
        name = field.name
        if name not in obj_dict:
            if field.default is MISSING and field.default_factory is MISSING:
                logger.warning(f"Couldn't find the field '{name}' in the dict with keys {list(d.keys())}")
            continue

        raw_value = obj_dict.pop(name)
        try:
            field_type = field.type
            logger.debug(f"Decode name = {name}, type = {field_type}")
            field_value = get_decoding_fn(field_type)(raw_value, (*path, name))  # type: ignore
        except ParsingError as e:
            raise e
        except DecodingError as e:
            raise e
        except Exception as e:
            raise DecodingError(
                (*path, name),
                f"Failed when parsing value='{raw_value}' into field \"{cls}.{name}\" of type"
                f' {field.type}.\n\tUnderlying error is "{format_error(e)}"',
            ) from e

        if field.init:
            init_args[name] = field_value
        else:
            non_init_args[name] = field_value

    extra_args = obj_dict

    # If there are arguments left over in the dict after taking all fields.
    if extra_args:
        formatted_keys = ", ".join(f"`{k}`" for k in extra_args.keys())
        raise DecodingError(path, f"The fields {formatted_keys} are not valid for {stringify_type(cls)}")

    # see if there are missing required fields
    missing_fields = []
    for field in fields(cls):  # type: ignore
        if field.init and field.name not in init_args and field.default is MISSING and field.default_factory is MISSING:
            missing_fields.append(field.name)

    if missing_fields:
        formatted_keys = ", ".join(f"`{k}`" for k in missing_fields)
        raise DecodingError(path, f"Missing required field(s) {formatted_keys} for {stringify_type(cls)}")

    init_args.update(extra_args)
    try:
        instance = cls(**init_args)  # type: ignore
    except TypeError as e:
        raise ParsingError(f"Couldn't instantiate class {stringify_type(cls)} using the given arguments.") from e
    except ValueError as e:
        raise ParsingError(f"Couldn't instantiate class {stringify_type(cls)} using the given arguments.") from e

    for name, value in non_init_args.items():
        logger.debug(f"Setting non-init field '{name}' on the instance.")
        setattr(instance, name, value)
    return instance


def decode_choice_class(cls: Type[T], raw_value: Any, path: Sequence[str]) -> T:
    """Decodes a value into an subtype of a choice class following the ChoiceType protocol."""
    assert issubclass(cls, ChoiceType)

    try:
        cls.get_choice_name(cls)
        # we already know what type we're looking for, so we can just use that
        return decode_dataclass(cls, raw_value)  # type: ignore
    except ValueError:
        pass

    if not isinstance(raw_value, dict):
        raise ParsingError(f"Expected a dict for a choice class, got {raw_value}")

    if CHOICE_TYPE_KEY not in raw_value:
        default = cls.default_choice_name()
        if default is None:
            raise ParsingError(f"Expected a dict with a '{CHOICE_TYPE_KEY}' key for {cls}, got {raw_value}")

        choice_type = default
    else:
        choice_type = raw_value[CHOICE_TYPE_KEY]

    try:
        subcls = cls.get_choice_class(choice_type)
    except KeyError as e:
        raise DecodingError(path, f"Couldn't find a choice class for '{choice_type}' in {cls}") from e

    raw_value = raw_value.copy()
    if CHOICE_TYPE_KEY in raw_value:
        raw_value.pop(CHOICE_TYPE_KEY)

    # return decode(subcls, raw_value)
    return decode_dataclass(subcls, raw_value, path)


def has_custom_decoder(cls: Type[T]):
    cached_func: RegistryFunc = decode.dispatch(cls)

    return cached_func is not None


@lru_cache(maxsize=100)
def get_decoding_fn(cls: Type[T]) -> DecodingFunction[T]:
    """Fetches/Creates a decoding function for the given type annotation.

    This decoding function can then be used to create an instance of the type
    when deserializing dicts.

    This function inspects the type annotation and creates the right decoding
    function recursively in a "dynamic-programming-ish" fashion.
    NOTE: We cache the results in a `functools.lru_cache` decorator to avoid
    wasteful calls to the function. This makes this process pretty efficient.

    """
    # Start by trying the dispatch mechanism
    cached_func: RegistryFunc = decode.dispatch(cls)
    if cached_func is not None:
        # If supports subclasses, pass the actual type
        if cached_func.include_subclasses:
            return partial(cached_func.func, cls)
        else:
            fn = cached_func.func

            # we want to support the old interface where the decoding function
            # takes only one argument, so we wrap it here
            @functools.wraps(fn)
            def backwards_compat_call(raw_value: Any, path: Sequence[str] = ()) -> T:
                try:
                    return fn(raw_value, path)
                except TypeError:
                    try:
                        return fn(raw_value)
                    except Exception as e:  # pylint: disable=broad-except
                        raise DecodingError(
                            path, f"Couldn't parse '{raw_value}' into a {stringify_type(cls)}: {e}"
                        ) from e

            return backwards_compat_call

    elif is_choice_type(cls):
        return partial(decode_choice_class, cls)

    elif is_dataclass(cls):
        return partial(decode_dataclass, cls)

    elif cls is Any:
        logger.debug(f"Decoding an Any type: {cls}")
        return no_op

    elif is_dict(cls):
        logger.debug(f"Decoding a Dict field: {cls}")
        args = get_type_arguments(cls)
        if args is None or len(args) != 2 or has_generic_arg(args):
            args = (Any, Any)
        return decode_dict(*args)

    elif is_set(cls):
        logger.debug(f"Decoding a Set field: {cls}")
        args = get_type_arguments(cls)
        if args is None or len(args) != 1 or has_generic_arg(args):
            args = (Any,)
        return decode_set(args[0])

    elif is_tuple(cls):
        logger.debug(f"Decoding a Tuple field: {cls}")
        args = get_type_arguments(cls)
        if args is None:
            args = []
        return decode_tuple(*args)

    elif is_list(cls):  # NOTE: Looks like can't be written with a dictionary
        logger.debug(f"Decoding a List field: {cls}")
        args = get_type_arguments(cls)
        if args is None or len(args) != 1 or has_generic_arg(args):
            # Using a `List` or `list` annotation, so we don't know what do decode the
            # items into!
            args = (Any,)
        decode_fn = decode_list(args[0])

        return decode_fn

    elif is_union(cls):
        logger.debug(f"Decoding a Union field: {cls}")
        args = get_type_arguments(cls)
        return decode_union(*args)

    elif is_enum(cls):
        return partial(decode_enum, cls)

    import typing_inspect as tpi

    if tpi.is_typevar(cls):
        bound = tpi.get_bound(cls)
        logger.debug(f"Decoding a typevar: {cls}, bound type is {bound}.")
        if bound is not None:
            return get_decoding_fn(bound)

    raise Exception(f"No decoding function for type {cls}, consider using draccus.decode.register")


def decode_enum(cls: Type[T], raw_value: Any, path) -> T:
    """Decodes a value into an enum."""
    if not is_enum(cls):
        raise Exception(f"Expected an enum type, got {cls}")

    try:
        return cls(raw_value)  # type: ignore
    except ValueError:
        try:
            return cls[raw_value]  # type: ignore
        except ValueError as e:
            raise DecodingError(path, f"Couldn't parse '{raw_value}' into an enum of type {cls}") from e


def decode_optional(t: Type[T]) -> DecodingFunction[Optional[T]]:
    decode = get_decoding_fn(t)  # type: ignore

    def _decode_optional(raw_value: Any, path: Sequence[str] = ()) -> Optional[T]:
        return raw_value if raw_value is None else decode(raw_value, path)

    return _decode_optional


@typing.no_type_check
def decode_union(*types: Type[T]) -> DecodingFunction[T]:
    types = list(types)
    is_optional = type(None) in types
    # Partition the Union into None and non-None types.
    while type(None) in types:
        types.remove(type(None))

    decoding_fns = {t: get_decoding_fn(t) for t in types}
    # Try using each of the non-None types, in succession

    if len(decoding_fns) == 0:
        raise ValueError("Must provide at least one function to try")
    elif len(decoding_fns) == 1 and not is_optional:
        return next(iter(decoding_fns.values()))

    def _try_functions(val: Any, path: Sequence[str] = ()) -> T:
        if is_optional and val is None:
            return None

        exceptions = {}
        for descriptor, func in decoding_fns.items():
            try:
                return func(val, path)
            except Exception as e:
                exceptions[descriptor] = e

        message = "Could not decode the value into any of the given types:\n"
        for descriptor, ex in exceptions.items():
            if isinstance(ex, DecodingError):
                ex = ex.strip_prefix(path)
            descriptor = stringify_type(descriptor)
            submessage = str(ex).split("\n")
            # indent the submessage by (4 + len(descriptor) + 1) spaces
            first_line = True
            for line in submessage:
                if first_line:
                    first_line = False
                    message += f"    {descriptor}: {line.strip()}"
                    message += "\n"
                else:
                    message += f"{' ' * (5 + len(str(descriptor)))}{line}\n"

        exception_to_raise_from = next(iter(exceptions.values()))
        # we'd prefer to find the first exception with an interesting message (not a DecodingError)
        for ex in exceptions.values():
            if not isinstance(ex, DecodingError):
                exception_to_raise_from = ex
                break

        raise DecodingError(path, message) from exception_to_raise_from

    return _try_functions


def decode_list(t: Type[T]) -> DecodingFunction[List[T]]:
    decode_item = get_decoding_fn(t)  # type: ignore

    def _decode_list(raw_value: List[Any], path: Sequence[str]) -> List[T]:
        path = tuple(path)
        # assert type(val) == list
        if not isinstance(raw_value, list):
            raise Exception(f"The given value='{raw_value}' is not of a valid input for a list type")
        return [decode_item(v, (*path, str(i))) for i, v in enumerate(raw_value)]

    return _decode_list


def decode_tuple(*tuple_item_types: Type[T]) -> DecodingFunction[Tuple[T, ...]]:
    """Makes a parsing function for creating tuples."""
    # Get the decoding function for each item type
    has_ellipsis = False
    if Ellipsis in tuple_item_types:
        ellipsis_index = tuple_item_types.index(Ellipsis)
        decoding_fn_index = ellipsis_index - 1
        decoding_fn = get_decoding_fn(tuple_item_types[decoding_fn_index])  # type: ignore
        has_ellipsis = True
    elif len(tuple_item_types) == 0:
        has_ellipsis = True
        decoding_fn = no_op  # Functionality will be the same as Tuple[Any,...]
    else:
        decoding_fns = [get_decoding_fn(t) for t in tuple_item_types]  # type: ignore

    # Note, if there are more values than types in the tuple type, then the
    # last type is used.

    def _decode_tuple(raw_value: typing.Sequence[Any], path) -> Tuple[T, ...]:
        path = tuple(path)
        if raw_value is None:
            raise DecodingError("Value must not be None for conversion to a tuple", path)
        if has_ellipsis:
            return tuple(decoding_fn(v, (*path, str(i))) for i, v in enumerate(raw_value))
        else:
            if len(decoding_fns) != len(raw_value):
                # err_msg = f"Trying to decode {len(raw_value)} values for a predfined {len(decoding_fns)}-Tuple"
                err_msg = f"Expected {len(decoding_fns)} items, got {len(raw_value)}"
                raise DecodingError(path, err_msg)
            return tuple(decoding_fns[i](v, (*path, str(i))) for i, v in enumerate(raw_value))

    return _decode_tuple


def decode_set(item_type: Type[T]) -> DecodingFunction[Set[T]]:
    """Makes a parsing function for creating sets with items of type `item_type`."""
    # Get the parsers fn for a list of items of type `item_type`.
    parse_list_fn = decode_list(item_type)

    def _decode_set(raw_value: List[Any], path) -> Set[T]:
        return set(parse_list_fn(raw_value, path))

    return _decode_set


def decode_dict(K_: Type[K], V_: Type[V]) -> DecodingFunction[Dict[K, V]]:
    """Creates a decoding function for a dict type. Works with OrderedDict too."""
    decode_k = get_decoding_fn(K_)  # type: ignore
    decode_v: DecodingFunction[V] = get_decoding_fn(V_)  # type: ignore

    def _decode_dict(raw_value: Union[Dict[Any, Any], List[Tuple[Any, Any]]], path) -> Dict[K, V]:
        result: Dict[K, V] = {}
        items: Iterable[Tuple[Any, Any]]
        if isinstance(raw_value, list):
            result = OrderedDict()
            items = raw_value
        elif isinstance(raw_value, OrderedDict):
            # NOTE(ycho): Needed to propagate `OrderedDict` type
            result = OrderedDict()
            items = raw_value.items()
        else:
            items = raw_value.items()
        for k, v in items:
            k_ = decode_k(k, (*tuple(path), f"key={k}"))
            v_ = decode_v(v, (*tuple(path), k))
            result[k_] = v_
        return result

    return _decode_dict


def no_op(raw_value: T, path) -> T:
    """Decoding function that gives back the value as-is."""
    del path
    return raw_value


decode.register(Path, partial(decode_from_init, Path))
