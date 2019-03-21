# ----------------------------------------------------------------------
# |
# |  SplitLogicalClausesPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-03-20 16:04:11
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

from collections import OrderedDict

import black
from blib2to3.pygram import python_symbols

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
    """Splits logical clauses across multiple lines if any are on a single line"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("SplitLogicalClauses")
    Priority                                = Interface.DerivedProperty(PluginBase.STANDARD_PRIORITY)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def Decorate(cls, lines):
        if not any(line for line in lines if (line.leaves and line.leaves[0].value in ["and", "or"])):
            return lines

        logical_symbols = set([python_symbols.and_test, python_symbols.or_test]) # <Instance of 'Symbols' has no 'and_test' member> pylint: disable = E1101
        logical_values = set(["and", "or"])

        # Create a map of lines and leaves
        leaves = {}

        for line_index, line in enumerate(lines):
            for leaf in line.leaves:
                leaves[id(leaf)] = line_index

        # ----------------------------------------------------------------------
        def EnumLeaves(first_line, last_line):
            while first_line < last_line:
                for leaf in lines[first_line].leaves:
                    yield first_line, leaf

                first_line += 1

        # ----------------------------------------------------------------------
        def IsSubexpressionDelimiter(leaf):
            # <Instance of 'Symbols' has no 'and_test' member> pylint: disable = E1101
            return (
                leaf.value in ["(", ")"]
                and leaf.parent
                and leaf.parent.type == python_symbols.atom
                and len(leaf.parent.children) > 2
                and leaf.parent.children[1].type in logical_symbols
            )

        # ----------------------------------------------------------------------

        # Process the lines
        modifications = OrderedDict()
        altered_subexpressions = set()

        line_index = 0

        while line_index < len(lines):
            line = lines[line_index]
            if line.leaves and line.leaves[0].value in logical_values:
                # Get the extent of the lines that we should process
                parent = line.leaves[0].parent
                while parent.type in logical_symbols:
                    parent = parent.parent
                    assert parent

                assert len(parent.children) >= 2

                open_paren_leaf = parent.children[0]
                close_paren_leaf = parent.children[-1]

                if not isinstance(open_paren_leaf, black.Leaf):
                    open_paren_leaf = parent.prev_sibling
                    close_paren_leaf = parent.next_sibling

                assert open_paren_leaf.value == "(", open_paren_leaf
                assert close_paren_leaf.value == ")", close_paren_leaf

                first_line = leaves[id(open_paren_leaf)]
                last_line = leaves[id(close_paren_leaf)]

                assert first_line <= last_line, (first_line, last_line)

                if first_line != last_line:
                    assert id(lines[first_line].leaves[-1]) == id(open_paren_leaf), lines[first_line]

                    # The last paren in the last line should correspond to the opening leaf
                    last_paren = None
                    for leaf in lines[last_line].leaves:
                        if leaf.value == ")":
                            last_paren = leaf

                    assert id(last_paren) == id(close_paren_leaf), lines[last_line]

                    # Move beyond the opening paren
                    first_line += 1

                    # Rather than try to modify the lines in place, we are going
                    # to create entirely new lines.
                    new_lines = []

                    # ----------------------------------------------------------------------
                    def AppendLine(
                        original_line_index,
                        indentation_delta,
                        copy_comments=True,
                    ):
                        new_lines.append(
                            black.Line(lines[original_line_index].depth + indentation_delta, []),
                        )

                        if copy_comments:
                            new_lines[-1].comments = lines[original_line_index].comments

                    # ----------------------------------------------------------------------

                    prev_line_index = None
                    indentation_delta = 0

                    # We don't want to split if looking at logical operators
                    # within a function.
                    suppress_split_until_id = None

                    for line_index, leaf in EnumLeaves(first_line, last_line):
                        if line_index != prev_line_index:
                            AppendLine(line_index, indentation_delta)
                            prev_line_index = line_index

                        is_subexpression_delimiter = IsSubexpressionDelimiter(leaf)

                        # Ignore the content in functions
                        # <Instance of 'Symbols' has no 'and_test' member> pylint: disable = E1101
                        if suppress_split_until_id is None and leaf.parent and leaf.parent.type == python_symbols.power:
                            assert len(leaf.parent.children) >= 2, leaf.parent.children
                            suppress_split_until_id = id(leaf.parent.children[-1])
                        elif suppress_split_until_id is not None and id(leaf) == suppress_split_until_id:
                            suppress_split_until_id = None

                        if is_subexpression_delimiter and leaf.value == ")" and leaf.opening_bracket:
                            # Continued on next line to prevent wonky line split from the black formatter
                            if id(leaf.opening_bracket) in altered_subexpressions:
                                altered_subexpressions.remove(id(leaf.opening_bracket))

                                assert indentation_delta
                                indentation_delta -= 1

                                AppendLine(
                                    line_index,
                                    indentation_delta,
                                    copy_comments=False,
                                )

                        if suppress_split_until_id is None and leaf.value in logical_values and new_lines[-1].leaves:
                            AppendLine(line_index, indentation_delta)

                        if not new_lines[-1].leaves:
                            leaf.prefix = ""

                        new_lines[-1].leaves.append(leaf)

                        if is_subexpression_delimiter and leaf.value == "(" and lines[line_index].leaves:
                            # Continued on next line to prevent wonky line split from the black formatter
                            if id(leaf) != id(lines[line_index].leaves[-1]):
                                indentation_delta += 1
                                AppendLine(line_index, indentation_delta)

                                altered_subexpressions.add(id(leaf))

                    modifications[(first_line, last_line)] = new_lines

                    line_index = last_line

            line_index += 1

        # Insert new content
        return cls.ReplaceLines(lines, modifications)
