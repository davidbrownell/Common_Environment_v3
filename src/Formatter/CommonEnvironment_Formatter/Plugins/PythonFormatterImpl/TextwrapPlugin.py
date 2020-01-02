# ----------------------------------------------------------------------
# |
# |  TextwrapPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-29 10:00:08
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

from PythonFormatterImpl.Plugin import PluginBase       # <Unable to import> pylint: disable = E0401
from PythonFormatterImpl.Tokenizer import Tokenizer     # <Unable to import> pylint: disable = E0401

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(PluginBase):
    """Formats textwrap.dedent invocations with multiline strings"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("Textwrap")
    Priority                                = Interface.DerivedProperty(PluginBase.STANDARD_PRIORITY)

    ORIGINAL_TEXT_ATTRIBUTE_NAME            = "_textwrap_plugin_original_value"

    # ----------------------------------------------------------------------
    # |  Methods
    @classmethod
    @Interface.override
    def PreprocessTokens(
        cls,
        tokenizer,
        tokenize_func,                      # <Unused argument> pylint: disable = W0613
        recurse_count,                      # <Unused argument> pylint: disable = W0613
    ):
        # ----------------------------------------------------------------------
        def GenerateTokens():
            for token in tokenizer.Tokens:
                if token not in Tokenizer.FAKE_TOKENS:
                    yield token

        # ----------------------------------------------------------------------

        # Note that this technique won't work if the states contain
        # repeated tokens.
        states = [
            lambda value: value == "textwrap",
            lambda value: value == ".",
            lambda value: value == "dedent",
            lambda value: value == "(",
            lambda value: value.startswith('"""') or value.startswith("'''"),
        ]

        state_index = 0

        for token in GenerateTokens():
            if token.value.startswith("#"):
                continue

            if not states[state_index](token.value):
                state_index = 0
                continue

            state_index += 1
            if state_index != len(states):
                continue

            setattr(token, cls.ORIGINAL_TEXT_ATTRIBUTE_NAME, token.value)
            state_index = 0

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def PostprocessBlocks(cls, blocks):
        for block in blocks:
            for line in block:
                for token in line.leaves:
                    if not hasattr(token, cls.ORIGINAL_TEXT_ATTRIBUTE_NAME):
                        continue

                    string_lines = [
                        string_line.expandtabs(4).rstrip()
                        for string_line in getattr(token, cls.ORIGINAL_TEXT_ATTRIBUTE_NAME).split(
                            "\n",
                        )
                    ]
                    delattr(token, cls.ORIGINAL_TEXT_ATTRIBUTE_NAME)

                    if len(string_lines) == 1:
                        continue

                    # Calculate the minimum leading whitespace. Ignore the first line, as that is the
                    # opening token that will already be aligned correctly.
                    leading_whitespace = None

                    for string_line in string_lines[1:]:
                        if not string_line:
                            continue

                        string_index = 0
                        while string_index < len(string_line) and string_line[string_index] == " ":
                            string_index += 1

                        if leading_whitespace is None or string_index < leading_whitespace:
                            assert string_index
                            leading_whitespace = string_index

                    assert leading_whitespace is not None

                    # Remove this whitespace from each line and add a new, normalized prefix.
                    # Ignore the first line, as that is the opening token that will already be
                    # aligned correctly.
                    string_prefix = " " * (line.depth * 4)

                    for string_line_index in range(1, len(string_lines)):
                        string_line = string_lines[string_line_index]
                        if not string_line:
                            continue

                        string_lines[string_line_index] = "{}{}".format(
                            string_prefix,
                            string_line[leading_whitespace:],
                        )

                    token.value = "\n".join(string_lines)
