__version__ = "0.8.0"

from .argparsing import parse, wrap
from .cfgparsing import dump, load, loads
from .choice_types import CHOICE_TYPE_KEY, ChoiceRegistry, ChoiceType, PluginRegistry
from .fields import field
from .options import ConfigType, Options, config_type
from .parsers.decoding import decode
from .parsers.encoding import encode
from .utils import ParsingError

get_config_type = Options.get_config_type
set_config_type = Options.set_config_type

__all__ = [
    "CHOICE_TYPE_KEY",
    "ChoiceRegistry",
    "ChoiceType",
    "ConfigType",
    "Options",
    "ParsingError",
    "PluginRegistry",
    "config_type",
    "decode",
    "dump",
    "encode",
    "field",
    "get_config_type",
    "load",
    "parse",
    "set_config_type",
    "wrap",
]
