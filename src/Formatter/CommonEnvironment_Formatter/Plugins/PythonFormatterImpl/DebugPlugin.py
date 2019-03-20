# ----------------------------------------------------------------------
# |
# |  DebugPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-07 12:56:40
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
import sys
import textwrap

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
    """Prints diagnostic information about the input code """

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("Debug")
    Priority                                = Interface.DerivedProperty(1)

    # ----------------------------------------------------------------------
    # |  Methods
    @classmethod
    @Interface.override
    def PreprocessLines(cls, lines):
        return cls._Display("Pre-Black", lines)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def Decorate(cls, lines):
        return cls._Display("Post-Black", lines)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def PostprocessLines(cls, lines):
        return cls._Display("Post-Decoration", lines)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _Display(header, lines):
        # Import black code here, as the import will fail in Python2
        import black

        symbol_table = black.pygram.python_grammar.number2symbol

        sys.stdout.write(
            textwrap.dedent(
                """\
                # ----------------------------------------------------------------------
                # |
                # |  {}
                # |
                """,
            ).format(header),
        )

        for line_index, line in enumerate(lines):
            sys.stdout.write(
                textwrap.dedent(
                    """\
                    # ----------------------------------------------------------------------
                    Line {0:>3}) {1}
                    """,
                ).format(line_index + 1, line),
            )

            for leaf_index, leaf in enumerate(line.leaves):
                symbol = "<None>"

                if leaf.parent is not None:
                    symbol = symbol_table[leaf.parent.type]

                sys.stdout.write(
                    textwrap.dedent(
                        """\
                        Leaf {0:>3}) {1:25}  {2:>2}  {3}
                        """,
                    ).format(leaf_index, leaf.value, len(leaf.prefix), symbol),
                )

            sys.stdout.write("\n")

        return lines
