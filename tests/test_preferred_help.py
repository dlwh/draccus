from dataclasses import dataclass

from draccus.wrappers.docstring import HelpOrder, get_attribute_docstring, get_preferred_help_text

from .testutils import TestSetup


@dataclass
class PreferredHelpConfig(TestSetup):
    """A simple base-class example"""

    # fmt: off
    a: int                                      # Parameter (int) controlling number of iterations

    # Cache Parameter
    cache: str                                  # Path to cache directory (as string)

    # Sets the mode of miscellaneous parameter handling
    misc: str = "standard"
    misc2: str = "left-first"                   # Controls the behavior of `misc2`
    # fmt: on


def test_get_preferred_help_text():
    a_docstring = get_attribute_docstring(PreferredHelpConfig, "a")
    a_help_inline = get_preferred_help_text(a_docstring, "inline")
    assert a_help_inline == "Parameter (int) controlling number of iterations"

    a_help_above = get_preferred_help_text(a_docstring, HelpOrder.above)
    assert a_help_above != "# fmt: off"

    # If "preferred" doesn't exist, goes through "default" order --> "inline" --> "above" --> "below"
    a_help_below = get_preferred_help_text(a_docstring, "below")
    assert a_help_below == a_help_inline

    misc2_docstring = get_attribute_docstring(PreferredHelpConfig, "misc2")
    misc2_help_inline = get_preferred_help_text(misc2_docstring, preferred_help="inline")
    assert misc2_help_inline == "Controls the behavior of `misc2`"
    assert misc2_docstring.comment_above == misc2_docstring.docstring_below == ""

    misc2_help_above = get_preferred_help_text(misc2_docstring, preferred_help="above")
    assert misc2_help_above == misc2_help_inline


def test_default_help_inline():
    target = """
usage: draccus [-h] [--config_path str] [--a int] [--cache str] [--misc str]
               [--misc2 str]

options:
  -h, --help         show this help message and exit
  --config_path str  Path for a config file to parse with draccus (default:
                     None)

PreferredHelpConfig:
  A simple base-class example

  --a int            Parameter (int) controlling number of iterations
                     (default: None)
  --cache str        Path to cache directory (as string) (default: None)
  --misc str         Sets the mode of miscellaneous parameter handling
                     (default: standard)
  --misc2 str        Controls the behavior of `misc2` (default: left-first)
    """
    assert PreferredHelpConfig.get_help_text().strip() == target.strip()
