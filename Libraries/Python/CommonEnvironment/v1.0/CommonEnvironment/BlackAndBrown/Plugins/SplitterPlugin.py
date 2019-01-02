# ----------------------------------------------------------------------
# |
# |  SplitterPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-01-01 11:17:44
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
from enum import Enum, auto

import black
from blib2to3.pygram import python_symbols, token as python_tokens
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
    """Splits function args, dictionaries, lists, and tuples"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("Splitter")
    Priority                                = Interface.DerivedProperty(PluginBase.STANDARD_PRIORITY)

    # ----------------------------------------------------------------------
    # |  Methods
    @classmethod
    @Interface.override
    def Decorate(
        cls,
        lines,
        max_func_line_length=100,
        split_dictionaries_num_args=2,
        split_funcs_num_args=None,
        split_func_args_with_default=True,
        split_lists_num_args=4,
        split_tuples_num_args=4,
    ):
        should_be_split_kwargs = {
            "split_dictionaries_num_args": split_dictionaries_num_args,
            "split_funcs_num_args": split_funcs_num_args,
            "split_func_args_with_default": split_func_args_with_default,
            "split_lists_num_args": split_lists_num_args,
            "split_tuples_num_args": split_tuples_num_args,
        }

        # ----------------------------------------------------------------------
        def ShouldBeSplit(line, clauses):
            offset = line.depth * 4

            for clause in clauses:
                offset += clause.OriginalLength(line)
                if offset > max_func_line_length:
                    return True

                if clause.ShouldBeSplit(**should_be_split_kwargs):
                    return True

            return False

        # ----------------------------------------------------------------------

        modifications = OrderedDict()

        for line_index, line in enumerate(lines):
            clauses = []
            leaf_index = 0

            while leaf_index < len(line.leaves):
                clauses.append(Clause(line, leaf_index))

                # Account for clause terminators
                if clauses[-1].EndingIndex < len(line.leaves) and line.leaves[clauses[-1].EndingIndex].value in Clause.TERMINATORS:
                    clauses[-1].EndingIndex += 1

                leaf_index = clauses[-1].EndingIndex

            # We only process balanced clauses
            is_balanced = True

            for clause in clauses:
                if not clause.IsBalanced():
                    is_balanced = False
                    break

            if not is_balanced:
                continue

            if not ShouldBeSplit(line, clauses):
                continue

            # If here, we are going to split
            new_lines = [black.Line(line.depth, [])]
            col_offset = line.depth * 4

            for clause in clauses:
                col_offset = clause.GenerateLines(
                    max_func_line_length,
                    line,
                    new_lines,
                    col_offset,
                    should_trim_prefix=False,
                    **should_be_split_kwargs
                )

            modifications[line_index] = new_lines

        if modifications:
            for line_index in reversed(list(six.iterkeys(modifications))):
                new_lines = modifications[line_index]
                new_lines[-1].comments = lines[line_index].comments

                del lines[line_index]

                for new_line in reversed(new_lines):
                    lines.insert(line_index, new_line)

        return lines

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class _TokenParser(Interface.Interface):
    """Abstract base class for all token parsers"""

    # ----------------------------------------------------------------------
    @Interface.abstractmethod
    def OriginalLength(self, line):
        """Returns the length of the original tokens"""
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @Interface.abstractmethod
    def IsBalanced(self):
        """Returns True if the token collection contains zero or more opening/closing pairs"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @Interface.abstractmethod
    def ShouldBeSplit(self, **should_be_split_kwargs):
        """Returns True if the collection of tokens should be split"""
        raise Exception("Abstract method")
    
    # ----------------------------------------------------------------------
    @Interface.abstractmethod
    def GenerateLines(
        self,
        max_func_line_length,
        line,
        new_lines,
        col_offset,
        should_trim_prefix,
        **should_be_split_kwargs
    ):
        """Generates new lines for the token collection when it has been determined that they should be split"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)
    
    # ----------------------------------------------------------------------
    # |  Protected Methods
    @staticmethod
    def _OriginalLengthImpl(line, starting_index, ending_index):
        length = 0

        for index in range(starting_index, ending_index):
            leaf = line.leaves[index]

            length += len(leaf.prefix)
            length += len(leaf.value)

        return length

# ----------------------------------------------------------------------
class _OpenCloseImpl(_TokenParser):

    # ----------------------------------------------------------------------
    # |  Properties
    @Interface.abstractproperty
    def OpenTokenValue(self):
        """Token value that opens the pair"""
        raise Exception("Abstract property")
    
    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def CloseTokenValue(self):
        """Token value that closes the pair"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  Methods
    def __init__(self, line, index):
        assert line.leaves[index].value == self.OpenTokenValue, line.leaves[index]

        open_index = index
        close_index = None

        children = []

        index += 1
        while index < len(line.leaves):
            leaf = line.leaves[index]

            if leaf.value == self.CloseTokenValue:
                close_index = index
                index += 1

                break

            elif leaf.value == ",":
                index += 1

            else:
                children.append(Clause(line, index))
                index = children[-1].EndingIndex

        self.OpenIndex                      = open_index
        self.CloseIndex                     = close_index
        self.EndingIndex                    = index
        self.Children                       = children

    # ----------------------------------------------------------------------
    @Interface.override
    def OriginalLength(self, line):
        return self._OriginalLengthImpl(line, self.OpenIndex, self.EndingIndex)

    # ----------------------------------------------------------------------
    @Interface.override
    def IsBalanced(self):
        return self.OpenIndex is not None and self.CloseIndex is not None

    # ----------------------------------------------------------------------
    @Interface.override
    def GenerateLines(
        self,
        max_func_line_length,
        line,
        new_lines,
        col_offset,
        should_trim_prefix,
        **should_be_split_kwargs
    ):
        if should_trim_prefix:
            line.leaves[self.OpenIndex].prefix = ""

        if (
            ( 
                self._ShouldSplitBasedOnLineLength() and 
                col_offset + self.OriginalLength(line) > max_func_line_length
            ) or self.ShouldBeSplit(**should_be_split_kwargs)
        ):
            # Open token
            new_lines[-1].leaves.append(line.leaves[self.OpenIndex])

            # Content
            new_depth = new_lines[-1].depth + 1
            col_offset = new_depth * 4

            has_multiple_children = len(self.Children) > 1

            for child in self.Children:
                new_lines.append(black.Line(new_depth, []))

                child.GenerateLines(
                    max_func_line_length,
                    line,
                    new_lines,
                    col_offset,
                    should_trim_prefix=True,
                    **should_be_split_kwargs
                )

                if has_multiple_children and child.AllowTrailingComma():
                    new_lines[-1].leaves.append(black.Leaf(python_tokens.COMMA, ","))

            # Close token
            leaf = line.leaves[self.CloseIndex]
            leaf.prefix = ""

            new_lines.append(black.Line(new_depth - 1, [leaf]))

            col_offset = (new_depth - 1) * 4 + len(leaf.value)

        else:
            # Copy as it currently exists
            for index in range(self.OpenIndex, self.EndingIndex):
                leaf = line.leaves[index]

                new_lines[-1].leaves.append(leaf)

                col_offset += len(leaf.prefix)
                col_offset += len(leaf.value)

        return col_offset

    # ----------------------------------------------------------------------
    # |  Private Methods
    @Interface.extensionmethod
    def _ShouldSplitBasedOnLineLength(self):
        return False

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class Clause(_TokenParser):

    TERMINATORS                             = [",", ")", "}", "]"]

    # ----------------------------------------------------------------------
    def __init__(self, line, index):
        starting_index = index

        children = []

        is_default_arg = False
        is_kwargs = False

        while index < len(line.leaves):
            leaf = line.leaves[index]

            if leaf.value in self.TERMINATORS:
                break

            elif leaf.value == "(":
                children.append(Parens(line, index))
                index = children[-1].EndingIndex

            elif leaf.value == "{":
                children.append(Braces(line, index))
                index = children[-1].EndingIndex

            elif leaf.value == "[":
                children.append(Brackets(line, index))
                index = children[-1].EndingIndex

            else:
                if leaf.value == "=":
                    assert is_default_arg is False
                    is_default_arg = True
                elif leaf.value == "**":
                    assert is_kwargs is False
                    is_kwargs = True

                index += 1

        self.StartingIndex                  = starting_index
        self.EndingIndex                    = index
        self.Children                       = children
        self.IsDefaultArg                   = is_default_arg
        self.IsKwargs                       = is_kwargs

    # ----------------------------------------------------------------------
    @Interface.override
    def OriginalLength(self, line):
        return self._OriginalLengthImpl(line, self.StartingIndex, self.EndingIndex)

    # ----------------------------------------------------------------------
    @Interface.override
    def IsBalanced(self):
        return not any(child for child in self.Children if not child.IsBalanced())

    # ----------------------------------------------------------------------
    @Interface.override
    def ShouldBeSplit(self, **should_be_split_kwargs):
        return self.IsDefaultArg or any(child for child in self.Children if child.ShouldBeSplit(**should_be_split_kwargs))

    # ----------------------------------------------------------------------
    @Interface.override
    def GenerateLines(
        self,
        max_func_line_length,
        line,
        new_lines,
        col_offset,
        should_trim_prefix,
        **should_be_split_kwargs
    ):
        # ----------------------------------------------------------------------
        def GenerateIndexAndChild():
            for child in self.Children:
                yield child.OpenIndex, child

            yield self.EndingIndex, None

        # ----------------------------------------------------------------------

        index = self.StartingIndex
        for ending_index, child in GenerateIndexAndChild():
            assert index <= ending_index, (index, ending_index)

            while index != ending_index:
                leaf = line.leaves[index]
                index += 1

                if should_trim_prefix:
                    leaf.prefix = ""
                    should_trim_prefix = False

                new_lines[-1].leaves.append(leaf)

                col_offset += len(leaf.prefix)
                col_offset += len(leaf.value)

            if child is None:
                continue

            col_offset = child.GenerateLines(
                max_func_line_length,
                line,
                new_lines,
                col_offset,
                should_trim_prefix,
                **should_be_split_kwargs
            )

            should_trim_prefix = False

            assert child.EndingIndex == child.CloseIndex + 1, child
            index = child.EndingIndex

        return col_offset

    # ----------------------------------------------------------------------
    def AllowTrailingComma(self):
        return not self.IsKwargs

# ----------------------------------------------------------------------
class Parens(_OpenCloseImpl):

    # ----------------------------------------------------------------------
    # |  Types
    class Type(Enum):
        Func                                = auto()
        Tuple                               = auto()

    # ----------------------------------------------------------------------
    # |  Properties
    OpenTokenValue                          = Interface.DerivedProperty("(")
    CloseTokenValue                         = Interface.DerivedProperty(")")

    # ----------------------------------------------------------------------
    # |  Methods
    def __init__(self, line, index):
        super(Parens, self).__init__(line, index)
        
        # ----------------------------------------------------------------------
        def GetType():
            if not self.IsBalanced:
                return None

            # Function invocation
            if line.leaves[index].parent is not None and line.leaves[index].parent.type == python_symbols.trailer:
                return self.__class__.Type.Func

            # Function definition
            if (
                index + 1 != len(line.leaves)
                and line.leaves[index + 1].parent is not None
                and (line.leaves[index + 1].parent.type in black.VARARGS_PARENTS or line.leaves[index + 1].parent.type in [python_symbols.parameters])
            ):
                return self.__class__.Type.Func

            # Empty tuple
            if self.CloseIndex == self.OpenIndex + 1:
                return self.__class__.Type.Tuple

            first_leaf = line.leaves[self.OpenIndex + 1]
            if first_leaf.parent and first_leaf.parent.type == python_symbols.testlist_gexp:
                return self.__class__.Type.Tuple

            return None

        # ----------------------------------------------------------------------

        self.Type                           = GetType()

    # ----------------------------------------------------------------------
    @Interface.override
    def ShouldBeSplit(
        self, 
        split_funcs_num_args,
        split_func_args_with_default,
        split_tuples_num_args,
        **should_be_split_kwargs
    ):
        if self.Type == self.__class__.Type.Func:
            if split_funcs_num_args is not None and len(self.Children) >= split_funcs_num_args:
                return True

            if split_func_args_with_default and len(self.Children) > 1 and any(child for child in self.Children if child.IsDefaultArg):
                return True
               
        elif self.Type == self.__class__.Type.Tuple:
            if split_tuples_num_args is not None and len(self.Children) >= split_tuples_num_args:
                return True

        if any(child for child in self.Children if child.ShouldBeSplit(
            split_funcs_num_args=split_funcs_num_args,
            split_func_args_with_default=split_func_args_with_default,
            split_tuples_num_args=split_tuples_num_args,
            **should_be_split_kwargs
        )):
            return True
        
        return False

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @Interface.override
    def _ShouldSplitBasedOnLineLength(self):
        return self.Type == self.__class__.Type.Func

# ----------------------------------------------------------------------
class Braces(_OpenCloseImpl):

    # ----------------------------------------------------------------------
    # |  Properties
    OpenTokenValue                          = Interface.DerivedProperty("{")
    CloseTokenValue                         = Interface.DerivedProperty("}")

    # ----------------------------------------------------------------------
    # |  Methods
    @Interface.override
    def ShouldBeSplit(
        self,
        split_dictionaries_num_args,
        **should_be_split_kwargs
    ):
        if split_dictionaries_num_args is not None and len(self.Children) >= split_dictionaries_num_args:
            return True

        if any(child for child in self.Children if child.ShouldBeSplit(
            split_dictionaries_num_args=split_dictionaries_num_args,
            **should_be_split_kwargs
        )):
            return True

        return False

# ----------------------------------------------------------------------
class Brackets(_OpenCloseImpl):

    # ----------------------------------------------------------------------
    # |  Properties
    OpenTokenValue                          = Interface.DerivedProperty("[")
    CloseTokenValue                         = Interface.DerivedProperty("]")

    # ----------------------------------------------------------------------
    # |  Methods
    def __init__(self, line, index):
        super(Brackets, self).__init__(line, index)

        # ----------------------------------------------------------------------
        def IsList():
            if not self.IsBalanced:
                return False

            # No args
            if self.CloseIndex == self.OpenIndex + 1:
                return True

            first_leaf = line.leaves[self.OpenIndex + 1]
            if first_leaf.parent and first_leaf.parent.type == python_symbols.listmaker:
                return True

            return False

        # ----------------------------------------------------------------------

        self.IsList                         = IsList()

    # ----------------------------------------------------------------------
    @Interface.override
    def ShouldBeSplit(
        self,
        split_lists_num_args,
        **should_be_split_kwargs
    ):
        if not self.IsList:
            return False

        if split_lists_num_args is not None and len(self.Children) >= split_lists_num_args:
            return True

        if any(child for child in self.Children if child.ShouldBeSplit(
            split_lists_num_args=split_lists_num_args,
            **should_be_split_kwargs
        )):
            return True

        return False
