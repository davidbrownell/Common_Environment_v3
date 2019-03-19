# ----------------------------------------------------------------------
# |
# |  CommaAfterArgsPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-09 09:27:59
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
    """Ensures that single arg functions spanning multiple lines include a trailing comma"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("CommaAfterArgs")
    Priority                                = Interface.DerivedProperty(PluginBase.STANDARD_PRIORITY)

    # ----------------------------------------------------------------------
    # |  Methods
    @staticmethod
    @Interface.override
    def Decorate(lines):
        # Decoration activities are handled in PostprocessLines
        return lines

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def PostprocessLines(cls, lines):
        # Functions are guaranteed to fall within a single block
        for starting_line_index, block in cls.EnumerateBlocks(lines):
            # Use closing trailers rather than opening trailers as
            # closing trailers have a pointer to their opening trailer
            # while opening trailers do not have a pointer to their
            # closing trailer.
            closing_trailers = []
            leaf_map = {}

            for line_index, line in enumerate(block):
                for leaf in line.leaves:
                    leaf_map[id(leaf)] = line_index

                    if leaf.value == ")" and leaf.parent and leaf.parent.type == python_symbols.trailer: # <Instance of 'Symbols' has no 'trailer' member> pylint: disable = E1101
                        closing_trailers.append(leaf)

            for closing_trailer in closing_trailers:
                # Are there any args?
                assert closing_trailer.parent

                if len(closing_trailer.parent.children) == 2:
                    assert closing_trailer.parent.children[0].value == "(", closing_trailer.parent.children[0]
                    assert closing_trailer.parent.children[1].value == ")", closing_trailer.parent.children[1]
                    continue

                # Don't process functions whose args fall on the same line
                closing_line = leaf_map[id(closing_trailer)]
                opening_line = leaf_map[id(closing_trailer.opening_bracket)]

                if closing_line == opening_line:
                    continue

                # Ensure that the last arg has a trailing comma
                assert id(closing_trailer) == id(closing_trailer.parent.children[-1])

                last_leaf = closing_trailer.parent.children[-2]
                while not isinstance(last_leaf, black.Leaf):
                    if (
                        last_leaf.type == python_symbols.arglist            # <Instance of 'Symbols' has no 'arglist' member> pylint: disable = E1101
                        and len(last_leaf.children) == 2
                        and isinstance(last_leaf.children[1], black.Leaf)
                        and last_leaf.children[1].value == ","
                    ):
                        last_leaf = last_leaf.children[0]
                    else:
                        last_leaf = last_leaf.children[-1]

                # Don't add a trailing comma if there is already one there
                if last_leaf.value == ",":
                    continue

                # Don't add a trailing comma for single- or double-star args
                if last_leaf.prev_sibling and isinstance(last_leaf.prev_sibling, black.Leaf) and last_leaf.prev_sibling.value in ["*", "**"]:
                    continue

                # Don't add a trailing comma for comprehensions
                if (
                    last_leaf.parent
                    and last_leaf.parent.parent
                    and last_leaf.parent.parent.parent
                    and last_leaf.parent.parent.parent.parent
                    and last_leaf.parent.parent.parent.parent.type
                    in [python_symbols.old_comp_for, python_symbols.comp_for] # <Instance of 'Symbols' has no '___' member> pylint: disable = E1101
                ):
                    continue

                last_line = block[leaf_map[id(last_leaf)]]

                if id(last_leaf) != id(last_line.leaves[-1]):
                    continue

                last_line.leaves.append(black.Leaf(python_tokens.COMMA, ","))

        return lines
