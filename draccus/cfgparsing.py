import os
from pathlib import Path
from typing import Optional, TextIO, Type, Union

from draccus import utils
from draccus.options import Options, config_type
from draccus.parsers.decoding import decode
from draccus.parsers.encoding import encode
from draccus.utils import Dataclass


def parse_string(s: str) -> dict:
    """
    Parse a string into a dictionary using the current config type parser.

    Args:
        s: The string to parse

    Returns:
        A dictionary containing the parsed configuration
    """
    parser = Options.get_config_type().value
    return parser.parse_string(s)


def load_config(
    stream: Union[str, TextIO, os.PathLike], *, file: Optional[Union[str, Path, os.PathLike]] = None
) -> dict:
    """
    Load configuration from a stream (file object or string) or file path.

    Args:
        stream: Either a file object, string content, or file path
        file: Optional file path used to determine the config type based on extension

    Returns:
        A dictionary containing the loaded configuration

    Note:
        If file is provided, the config type will be determined by the file extension.
        Supported extensions: .toml, .json, .yaml, .yml
    """
    if file is not None:
        fpath = str(file)
        if fpath.endswith(".toml"):
            with config_type("toml"):
                return load_config(stream)
        elif fpath.endswith(".json"):
            with config_type("json"):
                return load_config(stream)
        elif fpath.endswith(".yaml") or fpath.endswith(".yml"):
            with config_type("yaml"):
                return load_config(stream)

    parser = Options.get_config_type().value
    try:
        return parser.load_config(stream)
    except Exception as e:  # pylint: disable=broad-except
        raise utils.ParsingError(f"Failed to load config from {stream}") from e


def save_config(d: dict, stream=None, **kwargs) -> Optional[str]:
    """
    Save a configuration dictionary to a stream or return as a string.

    Args:
        d: The configuration dictionary to save
        stream: Optional stream to write to. If None, returns the configuration as a string
        **kwargs: Additional arguments passed to the parser's save_config method

    Returns:
        If stream is None, returns the configuration as a string.
        Otherwise, returns None after writing to the stream.
    """
    parser = Options.get_config_type().value
    return parser.save_config(d, stream, **kwargs)


def load(t: Type[Dataclass], stream: Union[str, TextIO, os.PathLike]) -> Dataclass:
    """
    Load a config from a file path, file object, or string.

    Args:
        t: The dataclass type to load into
        stream: Either a file path, file object, or string content

    Returns:
        An instance of the specified dataclass with values loaded from the stream

    Note:
        For string content, consider using loads() instead for clarity.
        This method maintains backwards compatibility with previous versions.
    """
    if isinstance(stream, (str, os.PathLike)) and os.path.exists(stream):
        # If stream is a file path, open it
        with open(stream, "r") as f:
            dictionary = load_config(f, file=stream)
    else:
        # If stream is a file object or string content
        dictionary = load_config(stream)

    return decode(t, dictionary)


def loads(t: Type[Dataclass], s: str) -> Dataclass:
    """
    Load a config from a string.

    Args:
        t: The dataclass type to load into
        s: The string containing the configuration

    Returns:
        An instance of the specified dataclass with values loaded from the string
    """
    dictionary = load_config(s)
    return decode(t, dictionary)


def dump(config: Dataclass, stream=None, omit_defaults: bool = False, **kwargs) -> Optional[str]:
    """
    Dump the config object to a stream or return as a string.

    Args:
        config: The dataclass instance to dump
        stream: Optional stream to write to. If None, returns the configuration as a string
        omit_defaults: If True, omits any values that match their default values
        **kwargs: Additional arguments passed to the parser's save_config method

    Returns:
        If stream is None, returns the configuration as a string.
        Otherwise, returns None after writing to the stream.
    """
    config_dict = encode(config)
    if omit_defaults:
        defaults_dict = encode(utils.get_defaults_dict(config))
        config_dict = utils.remove_matching(config_dict, defaults_dict)
    return save_config(config_dict, stream, **kwargs)
