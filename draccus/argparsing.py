"""Simple, Elegant Argument parsing.
@author: Fabrice Normandin
"""
import argparse
import dataclasses
import inspect
import os
import sys
import warnings
from argparse import HelpFormatter, Namespace
from collections import defaultdict
from functools import wraps
from gettext import gettext
from logging import getLogger
from pathlib import Path
from typing import Dict, Generic, Optional, Sequence, Text, Type, TypeVar, Union

import mergedeep

from draccus import cfgparsing, utils
from draccus.help_formatter import SimpleHelpFormatter
from draccus.parsers import decoding
from draccus.utils import Dataclass, DraccusException
from draccus.wrappers import DataclassWrapper
from draccus.wrappers.docstring import HelpOrder
from draccus.wrappers.suppressing_argparse import SuppressingArgumentParser

logger = getLogger(__name__)

T = TypeVar("T")


class ArgumentParser(Generic[T]):
    def __init__(
        self,
        config_class: Type[T],
        config_path: Optional[Union[Path, str]] = None,
        formatter_class: Type[HelpFormatter] = SimpleHelpFormatter,
        preferred_help: str = HelpOrder.inline,
        *args,
        **kwargs,
    ):
        """Creates an ArgumentParser instance."""
        kwargs = kwargs.copy()
        kwargs["formatter_class"] = formatter_class
        if "exit_on_error" in kwargs:
            # only available in python 3.9+, remove arg if not supported
            if sys.version_info < (3, 9):
                # behavior was functionally True before 3.9
                if not kwargs["exit_on_error"]:
                    warnings.warn(
                        "ArgumentParser exit_on_error is only available in python 3.9+, removing argument", stacklevel=2
                    )
                del kwargs["exit_on_error"]

        self.parser = SuppressingArgumentParser(*args, **kwargs)

        # constructor arguments for the dataclass instances.
        # (a Dict[dest, [attribute, value]])
        self.constructor_arguments: Dict[str, Dict] = defaultdict(dict)

        self.config_path = config_path
        self.config_class = config_class
        self.preferred_help = preferred_help
        self._assert_preferred_help()

        self._assert_no_conflicts()
        self.parser.add_argument(
            f"--{utils.CONFIG_ARG}",
            type=str,
            help="Path for a config file to parse with draccus",
        )
        self._set_dataclass(config_class)  # type: ignore

    def _set_dataclass(
        self,
        dataclass: Union[Type[Dataclass], Dataclass],
        default: Optional[Union[Dataclass, Dict]] = None,
        dataclass_wrapper_class: Type[DataclassWrapper] = DataclassWrapper,
    ):
        """Adds command-line arguments for the fields of `dataclass`."""
        if not isinstance(dataclass, type):
            default = dataclass if default is None else default
            dataclass = type(dataclass)

        new_wrapper = dataclass_wrapper_class(dataclass, default=default, preferred_help=self.preferred_help)
        new_wrapper.register_actions(parser=self.parser)

    def _assert_preferred_help(self):
        """Checks that `self.prefer_help` is valid."""
        if self.preferred_help not in {"inline", "above", "below"}:
            raise DraccusException(
                f"Value `prefer_help = {self.preferred_help}` not supported; must be one of < inline | above | below >"
            )

    def _assert_no_conflicts(self):
        """Checks for a field name that conflicts with utils.CONFIG_ARG"""
        if utils.CONFIG_ARG in [field.name for field in dataclasses.fields(self.config_class)]:
            raise DraccusException(f"{utils.CONFIG_ARG} is a reserved word for draccus")

    def parse_args(self, args=None, namespace=None) -> T:
        args, _ = self.parse_known_args(args, namespace, is_parse_args=True)
        return args

    def parse_known_args(
        self,
        args: Optional[Sequence[Text]] = None,
        namespace: Optional[Namespace] = None,
        *,
        is_parse_args: bool = False,
    ):
        # NOTE: since the usual ArgumentParser.parse_args() calls
        # parse_known_args, we therefore just need to overload the
        # parse_known_args method to support both.
        if args is None:
            # args default to the system args
            args = sys.argv[1:]
        else:
            # make sure that args are mutable
            args = list(args)

        if "--help" not in args:
            for action in self.parser._actions:
                # TODO(dlwh): this is so gross
                # TODO: Find a better way to do that?
                action.default = argparse.SUPPRESS  # To avoid setting of defaults in actual run
                action.type = str  # In practice, we want all processing to happen with yaml
        parsed_args, unparsed_args = self.parser.parse_known_args(args, namespace)
        if is_parse_args and unparsed_args:
            msg = gettext("unrecognized arguments: %s")
            self.parser.error(msg % " ".join(unparsed_args))

        parsed_t = self._postprocessing(parsed_args)
        return parsed_t, unparsed_args

    def print_help(self, file=None):
        return super().print_help(file)

    def _postprocessing(self, parsed_args: Namespace) -> T:
        logger.debug("\nPOST PROCESSING\n")
        logger.debug(f"(raw) parsed args: {parsed_args}")

        parsed_arg_values = vars(parsed_args)

        for key in parsed_arg_values:
            parsed_value = cfgparsing.parse_string(parsed_arg_values[key])
            if isinstance(parsed_value, str) and parsed_value.startswith("include"):
                try:
                    parsed_arg_values[key] = cfgparsing.load_config(open(parsed_value[8:], "r"))
                except FileNotFoundError as e:
                    raise FileNotFoundError(f"{e}. Include is a reserved cli keyword. "
                                            f"If your argument uses include, "
                                            f"Please refer to https://github.com/dlwh/draccus/issues/17")
            else:
                parsed_arg_values[key] = parsed_value

        config_path = self.config_path  # Could be NONE

        if utils.CONFIG_ARG in parsed_arg_values:
            new_config_path = parsed_arg_values[utils.CONFIG_ARG]
            if config_path is not None:
                warnings.warn(UserWarning(f"Overriding default {config_path} with {new_config_path}"), stacklevel=2)
            config_path = new_config_path
            del parsed_arg_values[utils.CONFIG_ARG]

        if config_path is not None:
            file_args = cfgparsing.load_config(open(config_path, "r"), file=config_path)
        else:
            file_args = {}

        deflat_d = utils.deflatten(parsed_arg_values, sep=".")
        deflat_d = mergedeep.merge(file_args, deflat_d)
        cfg = decoding.decode(self.config_class, deflat_d)

        return cfg


def parse(
    config_class: Type[T],
    config_path: Optional[Union[Path, str]] = None,
    args: Optional[Sequence[str]] = None,
    prog: Optional[str] = None,
    exit_on_error: bool = True,
    preferred_help: str = HelpOrder.inline,
) -> T:
    """
    Parses the command line arguments and returns an instance of the config class.

    Args:
        config_class: The config class to parse.
        config_path: The path to the config file to parse.
        args: The command line arguments to parse. If None, defaults to sys.argv[1:].
        prog: The name of the program (for the help message).
        exit_on_error: Whether to exit if an error occurs.
        preferred_help: Preferred location to parse help text for fields (< "inline" | "above" | "below" >)
    """
    parser = ArgumentParser(
        config_class=config_class,
        config_path=config_path,
        exit_on_error=exit_on_error,
        prog=prog,
        preferred_help=preferred_help,
    )
    return parser.parse_args(args)


def wrap(config_path: Optional[os.PathLike] = None, preferred_help: str = HelpOrder.inline):
    def wrapper_outer(fn):
        @wraps(fn)
        def wrapper_inner(*args, **kwargs):
            argspec = inspect.getfullargspec(fn)
            argtype = argspec.annotations[argspec.args[0]]
            if len(args) > 0 and type(args[0]) is argtype:
                cfg = args[0]
                args = args[1:]
            else:
                cfg = parse(config_class=argtype, config_path=config_path, preferred_help=preferred_help)
            response = fn(cfg, *args, **kwargs)
            return response

        return wrapper_inner

    return wrapper_outer
