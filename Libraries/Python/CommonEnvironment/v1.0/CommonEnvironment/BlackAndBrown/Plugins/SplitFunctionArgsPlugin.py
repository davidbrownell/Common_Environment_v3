# ----------------------------------------------------------------------
# |
# |  SplitFunctionArgsPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-12-19 15:36:04
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import itertools
import os

from collections import OrderedDict, namedtuple

import black
from blib2to3.pygram import python_symbols, token as python_tokens
from enum import Enum
import six

import CommonEnvironment
from CommonEnvironment import Interface

from CommonEnvironment.BlackAndBrown.Plugins import Plugin as PluginBase

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(PluginBase):
    """Splits the arguments of a function or function definition"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("SplitFunctionArgs")
    Priority                                = Interface.DerivedProperty(
        PluginBase.STANDARD_PRIORITY
    )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def Decorate(
        cls,
        lines,
        max_line_length=100,
        split_arg_with_default=True,
    ):
        # ----------------------------------------------------------------------
        def ShouldSplit(line, clauses):
            if split_arg_with_default and any(
                clause for clause in clauses if clause.HasDefaultArg()
            ):
                return True

            offset = line.depth * 4

            for clause in clauses:
                offset += clause.OriginalLength(line)

            return offset > max_line_length

        # ----------------------------------------------------------------------

        modifications = OrderedDict()

        for line_index, line in enumerate(lines):
            # A line is made up of one or more clauses
            clauses = []
            index = 0

            while index < len(line.leaves):
                clauses.append(cls._Clause.Parse(line, index))

                # Account for commas and parens at this root level
                if clauses[-1].EndingIndex < len(line.leaves) and line.leaves[clauses[-1].EndingIndex].value in [",", ")"]:
                    clauses[-1].EndingIndex += 1

                index = clauses[-1].EndingIndex

            # We only process balanced lines
            is_balanced = True

            for clause in clauses:
                if not clause.IsBalanced():
                    is_balanced = False
                    break

            if not is_balanced:
                continue

            # We only process clauses that have functions
            has_func = False

            for clause in clauses:
                if clause.HasFunc():
                    has_func = True
                    break

            if not has_func:
                continue

            # Is this a line that we should split
            if not ShouldSplit(line, clauses):
                continue

            # Create new lines
            new_lines = [black.Line(line.depth, [])]
            col_offset = line.depth * 4

            for clause in clauses:
                col_offset = clause.GenerateLines(
                    max_line_length,
                    split_arg_with_default,
                    line,
                    new_lines,
                    col_offset,
                )

            modifications[line_index] = new_lines

        # Update the content
        if modifications:
            for line_index in reversed(list(six.iterkeys(modifications))):
                new_lines = modifications[line_index]
                new_lines[-1].comments = lines[line_index].comments

                del lines[line_index]

                for new_line in reversed(new_lines):
                    lines.insert(line_index, new_line)

        return lines

    # ----------------------------------------------------------------------
    # |  Private Types
    class _ParenInfo(object):
        """Information about contents within a (hopefully) balanced set of parens"""

        # ----------------------------------------------------------------------
        @classmethod
        def Parse(cls, line, index):
            assert line.leaves[index].value == "(", line.leaves[index]

            open_index = index
            close_index = None

            parameters = []
            index += 1

            while index < len(line.leaves):
                leaf = line.leaves[index]

                if leaf.value == ")":
                    close_index = index
                    index += 1
                    break

                elif leaf.value == ",":
                    index += 1

                else:
                    parameters.append(Plugin._Clause.Parse(line, index))

                    index = parameters[-1].EndingIndex

            return cls(
                open_index,
                close_index,
                index,
                parameters,
                cls._AreFuncArgs(line, open_index),
            )

        # ----------------------------------------------------------------------
        def __init__(self, open_index, close_index, ending_index, parameters, are_func_args):
            self.OpenIndex                  = open_index
            self.CloseIndex                 = close_index
            self.EndingIndex                = ending_index
            self.Parameters                 = parameters
            self.AreFuncArgs                = are_func_args

        # ----------------------------------------------------------------------
        def __repr__(self):
            return CommonEnvironment.ObjectReprImpl(self)

        # ----------------------------------------------------------------------
        def IsBalanced(self):
            return self.OpenIndex and self.CloseIndex

        # ----------------------------------------------------------------------
        def HasDefaultArg(self):
            return any(param for param in self.Parameters if param.HasDefaultArg())

        # ----------------------------------------------------------------------
        def OriginalLength(self, line):
            return Plugin._CalculateLength(line, self.OpenIndex, self.EndingIndex)

        # ----------------------------------------------------------------------
        def GenerateLines(
            self,
            max_line_length,
            split_arg_with_default,
            line,
            new_lines,
            col_offset,
        ):
            if col_offset + self.OriginalLength(line) > max_line_length or (
                split_arg_with_default and any(
                    param for param in self.Parameters if param.HasDefaultArg()
                )
            ):
                # Open paren
                new_lines[-1].leaves.append(line.leaves[self.OpenIndex])

                new_depth = new_lines[-1].depth + 1
                col_offset = new_depth * 4
                multiple_parameters = len(self.Parameters) > 1

                for param in self.Parameters:
                    new_lines.append(black.Line(new_depth, []))

                    param.GenerateLines(
                        max_line_length,
                        split_arg_with_default,
                        line,
                        new_lines,
                        col_offset,
                        trim_prefix=True,
                    )

                    if multiple_parameters and not param.IsKwargs:
                        new_lines[-1].leaves.append(black.Leaf(python_tokens.COMMA, ","))

                # Close paren
                new_lines.append(black.Line(new_depth - 1, [line.leaves[self.CloseIndex]]))

            else:
                for index in range(self.OpenIndex, self.EndingIndex):
                    leaf = line.leaves[index]

                    new_lines[-1].leaves.append(leaf)

                    col_offset += len(leaf.prefix)
                    col_offset += len(leaf.value)

            return col_offset

        # ----------------------------------------------------------------------
        # ----------------------------------------------------------------------
        # ----------------------------------------------------------------------
        @staticmethod
        def _AreFuncArgs(line, index):
            # Function invocation...
            if line.leaves[index].parent is not None and line.leaves[index].parent.type == python_symbols.trailer:
                return True

            # Function definition...
            if (
                index + 1 != len(line.leaves)
                and line.leaves[index + 1].parent is not None
                and (line.leaves[index + 1].parent.type in black.VARARGS_PARENTS or line.leaves[index + 1].parent.type in [python_symbols.parameters])
            ):
                return True

            return False

    # ----------------------------------------------------------------------
    class _Clause(object):
        """Collection of tokens terminated by a comma, right-paren, or end of line"""

        # ----------------------------------------------------------------------
        @classmethod
        def Parse(cls, line, index):
            starting_index = index
            parens = []
            is_default_arg = False
            is_kwargs = False

            while index < len(line.leaves):
                leaf = line.leaves[index]

                if leaf.value in [",", ")"]:
                    break

                elif leaf.value == "(":
                    parens.append(Plugin._ParenInfo.Parse(line, index))
                    index = parens[-1].EndingIndex

                else:
                    if leaf.value == "=":
                        assert is_default_arg is False
                        is_default_arg = True
                    elif leaf.value == "**":
                        assert is_kwargs is False
                        is_kwargs = True

                    index += 1

            return cls(starting_index, index, parens, is_default_arg, is_kwargs)

        # ----------------------------------------------------------------------
        def __init__(self, starting_index, ending_index, parens, is_default_arg, is_kwargs):
            self.StartingIndex              = starting_index
            self.EndingIndex                = ending_index
            self.Parens                     = parens
            self.IsDefaultArg               = is_default_arg
            self.IsKwargs                   = is_kwargs

        # ----------------------------------------------------------------------
        def __repr__(self):
            return CommonEnvironment.ObjectReprImpl(self)

        # ----------------------------------------------------------------------
        def IsBalanced(self):
            return not any(paren for paren in self.Parens if not paren.IsBalanced())

        # ----------------------------------------------------------------------
        def HasDefaultArg(self):
            return self.IsDefaultArg or any(paren for paren in self.Parens if paren.HasDefaultArg())

        # ----------------------------------------------------------------------
        def HasFunc(self):
            return any(paren for paren in self.Parens if paren.AreFuncArgs)

        # ----------------------------------------------------------------------
        def OriginalLength(self, line):
            return Plugin._CalculateLength(line, self.StartingIndex, self.EndingIndex)

        # ----------------------------------------------------------------------
        def GenerateLines(
            self,
            max_line_length,
            split_arg_with_default,
            line,
            new_lines,
            col_offset,
            trim_prefix=False,
        ):
            # ----------------------------------------------------------------------
            def GenerateIndexAndParenInfo():
                for paren in self.Parens:
                    yield paren.OpenIndex, paren

                yield self.EndingIndex, None

            # ----------------------------------------------------------------------

            original_depth = new_lines[-1].depth

            index = self.StartingIndex

            for ending_index, paren in GenerateIndexAndParenInfo():
                assert index <= ending_index, (index, ending_index)

                is_first = True

                while index != ending_index:
                    leaf = line.leaves[index]
                    index += 1

                    if is_first:
                        is_first = False

                        # If we are looking at a chained method call, move this invocation
                        # to a newline...
                        if leaf.value == ".":
                            # ... unless there is only a trailing paren on the current line
                            if col_offset - (original_depth * 4) > 1:
                                new_lines[-1].leaves.append(
                                    black.Leaf(
                                        python_tokens.ENDMARKER,
                                        "\\",
                                        prefix=" ",
                                    )
                                )

                                new_lines.append(black.Line(original_depth + 1, []))
                                col_offset = new_lines[-1].depth * 4

                        if trim_prefix:
                            leaf.prefix = ""
                            trim_prefix = False

                    new_lines[-1].leaves.append(leaf)

                    col_offset += len(leaf.prefix)
                    col_offset += len(leaf.value)

                if paren is None:
                    continue

                col_offset = paren.GenerateLines(
                    max_line_length,
                    split_arg_with_default,
                    line,
                    new_lines,
                    col_offset,
                )

                assert paren.EndingIndex == paren.CloseIndex + 1, paren
                index = paren.EndingIndex

            return col_offset

    # ----------------------------------------------------------------------
    @staticmethod
    def _CalculateLength(line, start_index, end_index):
        length = 0

        for index in range(start_index, end_index):
            leaf = line.leaves[index]

            length += len(leaf.prefix)
            length += len(leaf.value)

        return length
