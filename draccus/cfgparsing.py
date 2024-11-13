from typing import Type

from draccus import utils
from draccus.options import Options, config_type
from draccus.parsers.decoding import decode
from draccus.parsers.encoding import encode
from draccus.utils import Dataclass


def parse_string(s):
    parser = Options.get_config_type().value
    return parser.parse_string(s)


def load_config(stream, *, file=None):
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
    return parser.load_config(stream)


def save_config(d, stream=None, **kwargs):
    parser = Options.get_config_type().value
    return parser.save_config(d, stream, **kwargs)


def load(t: Type[Dataclass], stream):
    dictionary = load_config(stream)
    return decode(t, dictionary)


def dump(config: Dataclass, stream=None, omit_defaults: bool = False, **kwargs):
    """
    Dump the config object to yaml.
    optionally omit any value that still has a default value
    """
    config_dict = encode(config)
    if omit_defaults:
        defaults_dict = encode(utils.get_defaults_dict(config))
        config_dict = utils.remove_matching(config_dict, defaults_dict)
    return save_config(config_dict, stream, **kwargs)
