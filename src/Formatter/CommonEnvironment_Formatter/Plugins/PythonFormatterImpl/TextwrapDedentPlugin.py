# ----------------------------------------------------------------------
# |
# |  TextwrapDedentPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-10 15:11:03
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os

import black
from blib2to3.pygram import python_symbols, token as python_tokens

import CommonEnvironment
from CommonEnvironment import Interface

from PluginBase import PluginBase

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(PluginBase):
    """Properly indents args to textwrap.dedent"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("TextwrapDedent")
    Priority                                = Interface.DerivedProperty(PluginBase.STANDARD_PRIORITY)

    ORIGINAL_TEXT_ATTRIBUTE_NAME            = "_original_value"

    # ----------------------------------------------------------------------
    # |  Methods
    @classmethod
    @Interface.override
    def PreprocessLines(cls, lines):
        # ----------------------------------------------------------------------
        def LeafGenerator():
            line_index = 0
            leaf_index = 0

            while line_index < len(lines):
                line = lines[line_index]

                while leaf_index < len(line.leaves):
                    yield line.leaves[leaf_index]
                    leaf_index += 1

                line_index += 1
                leaf_index = 0

        # ----------------------------------------------------------------------
        def Apply(leaf):
            setattr(leaf, cls.ORIGINAL_TEXT_ATTRIBUTE_NAME, leaf.value)

        # ----------------------------------------------------------------------

        states = [
            lambda leaf: leaf.value == "textwrap",
            lambda leaf: leaf.value == ".",
            lambda leaf: leaf.value == "dedent",
            lambda leaf: leaf.value == "(",
            lambda leaf: leaf.value.startswith('"""') or leaf.value.startswith("'''"),
        ]

        state_index = 0

        for leaf in LeafGenerator():
            if leaf.value.startswith("#"):
                continue

            if states[state_index](leaf):
                state_index += 1

                if state_index != len(states):
                    continue

                Apply(leaf)

            state_index = 0

        return lines

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def Decorate(lines):
        # Decoration activities are handled in PostprocessLines
        return lines

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def PostprocessLines(cls, lines):
        for line_index, line in enumerate(lines):
            if not line.leaves or not hasattr(line.leaves[0], cls.ORIGINAL_TEXT_ATTRIBUTE_NAME):
                continue

            # Manually dedent the original string

            string_lines = [string_line.expandtabs(4).rstrip() for string_line in getattr(line.leaves[0], cls.ORIGINAL_TEXT_ATTRIBUTE_NAME).split("\n")]
            if len(string_lines) == 1:
                continue

            # Calculate the min whitespace prefix
            leading_whitespace = None

            for string_line in string_lines[1:]:
                if not string_line:
                    continue

                string_index = 0
                while string_index < len(string_line) and string_line[string_index] == " ":
                    string_index += 1

                if leading_whitespace is None or string_index < leading_whitespace:
                    leading_whitespace = string_index

            assert leading_whitespace

            # Remove this whitespace from each line and reapply it based on the
            # current indentation level.
            whitespace = " " * (line.depth * 4)

            for string_line_index, string_line in enumerate(string_lines[1:]):
                if not string_line:
                    continue

                string_lines[string_line_index + 1] = "{}{}".format(
                    whitespace,
                    string_line[leading_whitespace:],
                )

            line.leaves[0].value = "\n".join(string_lines)

        return lines
