from logging import getLogger
from typing import Any, Dict, List, Optional, Type, TypeVar

from draccus.utils import get_type_arguments, is_optional, is_tuple, is_union

T = TypeVar("T")

logger = getLogger(__name__)

_new_metavars: Dict[Type, Optional[str]] = {
    # the 'primitive' types don't get a 'new' metavar.
    t: t.__name__
    for t in [str, float, int, bytes]
}


def get_metavar(t: Type, top_level: bool = True) -> Optional[str]:
    """Gets the metavar to be used for that type in help strings.

    This is crucial when using a `weird` auto-generated parsing functions for
    things like Union, Optional, Etc etc.

    type the type arguments that were passed to `get_parsing_fn` that
    produced the given parsing_fn.

    returns None if the name shouldn't be changed.
    """
    # TODO: Maybe we can create the name for each returned call, a bit like how
    # we dynamically create the parsing function itself?
    new_name: Optional[str] = getattr(t, "__name__", None)

    optional = is_optional(t)

    if t in _new_metavars:
        return _new_metavars[t]

    elif is_union(t):
        args = get_type_arguments(t)
        metavars: List[str] = []
        for type_arg in args:
            if type_arg is type(None):
                if top_level:
                    continue
                else:
                    metavars.append("None")
            else:
                metavars.append(get_metavar(type_arg) or "<unknown>")
        metavar = "|".join(map(str, metavars))
        if optional and top_level:
            return f"[{metavar}]"
        return metavar

    elif is_tuple(t):
        args = get_type_arguments(t)
        if not args:
            return get_metavar(Any)  # type: ignore
        logger.debug(f"Tuple args: {args}")
        metavars = []
        for arg in args:
            if arg is Ellipsis:
                metavars.append(f"[{metavars[-1]}, ...]")
                break
            else:
                metavars.append(get_metavar(arg) or "<unknown>")
        return " ".join(metavars)

    else:
        try:
            args = get_type_arguments(t)
            if args:
                # we want the name without type args
                # List[str]'s __name__ is List[str], but we want List
                new_name = t.__origin__.__name__
                return f"{new_name}[{','.join(get_metavar(arg, top_level=False) or str(arg) for arg in args)}]"
        except Exception:
            pass

    return new_name
