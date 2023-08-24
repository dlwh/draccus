import argparse
from argparse import ONE_OR_MORE, OPTIONAL, PARSER, REMAINDER, ZERO_OR_MORE, Action
from logging import getLogger
from typing import Type

from draccus.wrappers.field_metavar import get_metavar

logger = getLogger(__name__)


class SimpleHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.MetavarTypeHelpFormatter,
    argparse.RawDescriptionHelpFormatter,
):
    """Little shorthand for using some useful HelpFormatters from argparse.

    This class inherits from argparse's `ArgumentDefaultHelpFormatter`,
    `MetavarTypeHelpFormatter` and `RawDescriptionHelpFormatter` classes.

    This produces the following resulting actions:
    - adds a "(default: xyz)" for each argument with a default
    - uses the name of the argument type as the metavar. For example, gives
      "-n int" instead of "-n N" in the usage and description of the arguments.
    - Conserves the format of the class and argument docstrings, if given.
    """

    def _format_args(self, action: Action, default_metavar: str):
        _get_metavar = self._metavar_formatter(action, default_metavar)
        action_type = action.type

        metavar = action.metavar or get_metavar(action_type)  # type: ignore
        if metavar and not action.choices:
            result = metavar
        elif action.nargs is None:
            result = "%s" % _get_metavar(1)
        elif action.nargs == OPTIONAL:
            result = "[%s]" % _get_metavar(1)
        elif action.nargs == ZERO_OR_MORE:
            result = "[%s [%s ...]]" % _get_metavar(2)
        elif action.nargs == ONE_OR_MORE:
            result = "%s [%s ...]" % _get_metavar(2)
        elif action.nargs == REMAINDER:
            result = "..."
        elif action.nargs == PARSER:
            result = "%s ..." % _get_metavar(1)
        else:
            assert isinstance(action.nargs, int)
            formats = ["%s" for _ in range(action.nargs)]
            result = " ".join(formats) % _get_metavar(action.nargs)

        logger.debug(
            f"action type: {action_type}, Result: {result}, nargs: {action.nargs}, default metavar: {default_metavar}"
        )
        return result

    def _get_default_metavar_for_optional(self, action: argparse.Action):
        try:
            return super()._get_default_metavar_for_optional(action)
        except BaseException:
            logger.debug(f"Getting metavar for action with dest {action.dest}.")
            metavar = self._get_metavar_for_action(action)
            logger.debug(f"Result metavar: {metavar}")
            return metavar

    def _get_default_metavar_for_positional(self, action: argparse.Action):
        try:
            return super()._get_default_metavar_for_positional(action)
        except BaseException:
            logger.debug(f"Getting metavar for action with dest {action.dest}.")
            metavar = self._get_metavar_for_action(action)
            logger.debug(f"Result metavar: {metavar}")
            return metavar

    def _get_metavar_for_action(self, action: argparse.Action) -> str:
        return self._get_metavar_for_type(action.type)  # type: ignore

    def _get_metavar_for_type(self, t: Type) -> str:
        return get_metavar(t) or str(t)


Formatter = SimpleHelpFormatter
