__version__ = "0.8.0"

from . import utils, wrappers
from .argparsing import parse, wrap
from .cfgparsing import dump, load
from .choice_types import CHOICE_TYPE_KEY, ChoiceRegistry, ChoiceType, PluginRegistry
from .fields import field
from .options import ConfigType, Options, config_type
from .parsers.decoding import decode
from .parsers.encoding import encode
from .utils import ParsingError

get_config_type = Options.get_config_type
set_config_type = Options.set_config_type
