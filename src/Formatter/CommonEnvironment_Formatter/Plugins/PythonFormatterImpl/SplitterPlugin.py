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

from PluginBase import PluginBase

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

    IS_FIRST_FUNC_ARG_ATTRIBUTE_NAME        = "_is_first_func_arg"
    IS_LAST_FUNC_ARG_ATTRIBUTE_NAME         = "_is_last_func_arg"

    # ----------------------------------------------------------------------
    # |  Methods
    @classmethod
    @Interface.override
    def PreprocessLines(cls, lines):
        # Decorate all parens that are associated with function calls. We must do this
        # here, as black may move all of the parameters to their own line (since it
        # prefers to split after an opening paren and before a closing paren). With this
        # decoration, plugins can apply argument formatting even if the parens that
        # delimit the arguments appear on different lines.
        for line in lines:
            nested_count = 0
            paren_pairs = {}

            for leaf_index, leaf in enumerate(line.leaves):
                if leaf.value == "(":
                    if cls.IsFunc(line, leaf_index):
                        assert nested_count not in paren_pairs, nested_count
                        paren_pairs[nested_count] = leaf_index

                    nested_count += 1

                elif leaf.value == ")":
                    nested_count -= 1

                    if nested_count in paren_pairs:
                        # Make sure that there is at least 1 arg
                        if paren_pairs[nested_count] + 1 != leaf_index:
                            setattr(
                                line.leaves[paren_pairs[nested_count] + 1],
                                cls.IS_FIRST_FUNC_ARG_ATTRIBUTE_NAME,
                                True,
                            )
                            setattr(
                                line.leaves[leaf_index - 1],
                                cls.IS_LAST_FUNC_ARG_ATTRIBUTE_NAME,
                                True,
                            )

                        del paren_pairs[nested_count]

        return lines

    # ----------------------------------------------------------------------
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

        for line_index, line in cls.EnumerateLines(lines):
            clauses = []

            leaf_index = 0
            while leaf_index < len(line.leaves):
                clauses.append(Clause(line, leaf_index))

                if clauses[-1].EndingIndex < len(line.leaves) and line.leaves[clauses[-1].EndingIndex].value == ",":
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

            # This is a hack to work around an apparent bug in Black -
            # it doesn't seem to properly group arguments when invoking
            # a method that contains a long number of parameters.
            are_func_args = (
                line.leaves[0].parent
                and line.leaves[0].parent.type == python_symbols.atom           # <Instance of 'Symbols' has no 'atom' member> pylint: disable = E1101
                and line.leaves[0].parent.parent
                and line.leaves[0].parent.parent.type == python_symbols.arglist # <Instance of 'Symbols' has no 'arglist' member> pylint: disable = E1101
            )

            if are_func_args:
                new_lines = []
                should_trim_prefix = True
            else:
                new_lines = [black.Line(line.depth, [])]
                should_trim_prefix = False

            col_offset = line.depth * 4

            for clause in clauses:
                if are_func_args:
                    new_lines.append(black.Line(line.depth, []))
                    col_offset = line.depth * 4

                col_offset = clause.GenerateLines(
                    max_func_line_length,
                    line,
                    new_lines,
                    col_offset,
                    should_trim_prefix=should_trim_prefix,
                    **should_be_split_kwargs
                )

            if are_func_args and clauses[-1].AllowTrailingComma() and new_lines[-1].leaves[-1].type != python_tokens.COMMA:
                new_lines[-1].leaves.append(black.Leaf(python_tokens.COMMA, ","))

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
    @staticmethod
    def IsFunc(line, leaf_index):
        # <Instance of 'Symbols' has no 'trailer' member> pylint: disable = E1101

        # Function invocation
        if line.leaves[leaf_index].parent is not None and line.leaves[leaf_index].parent.type == python_symbols.trailer:
            return True

        # Function definition
        if (
            leaf_index + 1 != len(line.leaves)
            and line.leaves[leaf_index + 1].parent is not None
            and (line.leaves[leaf_index + 1].parent.type in black.VARARGS_PARENTS or line.leaves[leaf_index + 1].parent.type in [python_symbols.parameters])
        ):
            return True

        return False


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
    @Interface.abstractmethod
    def AllowTrailingComma(self):
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
class _OpenCloseTokenImpl(_TokenParser):

    # ----------------------------------------------------------------------
    # |  Properties
    @Interface.abstractproperty
    def OpenTokenValue(self):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def CloseTokenValue(self):
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  Methods
    def __init__(self, line, leaf_index):
        assert line.leaves[leaf_index].value == self.OpenTokenValue, line.leaves[leaf_index]

        open_index = leaf_index
        close_index = None

        children = []

        leaf_index += 1
        while leaf_index < len(line.leaves):
            leaf = line.leaves[leaf_index]

            if leaf.value == self.CloseTokenValue:
                close_index = leaf_index
                leaf_index += 1

                break

            elif line.leaves[leaf_index].value == ",":
                leaf_index += 1

            else:
                children.append(
                    Clause(
                        line,
                        leaf_index,
                        is_terminated_func=lambda line,
                        leaf_index: line.leaves[leaf_index].value == self.CloseTokenValue,
                    ),
                )

                leaf_index = children[-1].EndingIndex

        self.OpenIndex                      = open_index
        self.CloseIndex                     = close_index
        self.EndingIndex                    = leaf_index
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
        suppress_final_comma,
        **should_be_split_kwargs
    ):
        if should_trim_prefix:
            line.leaves[self.OpenIndex].prefix = ""

        if (self._ShouldSplitBasedOnLineLength() and col_offset + self.OriginalLength(line) > max_func_line_length) or self.ShouldBeSplit(
            **should_be_split_kwargs
        ):
            # Open token
            new_lines[-1].leaves.append(line.leaves[self.OpenIndex])

            # Content
            new_depth = new_lines[-1].depth + 1
            col_offset = new_depth * 4

            for child_index, child in enumerate(self.Children):
                new_lines.append(black.Line(new_depth, []))

                child.GenerateLines(
                    max_func_line_length,
                    line,
                    new_lines,
                    col_offset,
                    should_trim_prefix=True,
                    **should_be_split_kwargs
                )

                if child.AllowTrailingComma() and (not suppress_final_comma or child_index != len(self.Children) - 1):
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
    # |  Protected Methods
    def _IsComprehension(self, line):
        # Comprehensions will only have a single child
        if len(self.Children) != 1:
            return False

        clause = self.Children[0]

        # Enumerate the children of the clause

        # ----------------------------------------------------------------------
        def GenerateIndexRange():
            start = clause.StartingIndex

            if not clause.Children:
                yield start, clause.EndingIndex
                return

            for child in clause.Children:
                if child.OpenIndex != start:
                    yield start, child.OpenIndex

                start = child.CloseIndex

            if start != clause.EndingIndex:
                yield start, clause.EndingIndex

        # ----------------------------------------------------------------------

        for start, end in GenerateIndexRange():
            for index in range(start, end):
                leaf = line.leaves[index]

                # <Instance of 'Symbols' has no '___' member> pylint: disable = E1101
                if leaf.parent and leaf.parent.type in [python_symbols.old_comp_for, python_symbols.comp_for]:
                    return True

        return False

    # ----------------------------------------------------------------------
    # |  Private Methods
    @Interface.extensionmethod
    def _ShouldSplitBasedOnLineLength(self):
        return False


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class Clause(_TokenParser):

    # ----------------------------------------------------------------------
    def __init__(
        self,
        line,
        leaf_index,
        is_terminated_func=None,
        process_single_line_func_args=True,
    ):
        is_terminated_func = is_terminated_func or (lambda line, leaf_index: False)

        starting_index = leaf_index

        children = []

        is_default_arg = False
        allow_trailing_comma = True

        while leaf_index < len(line.leaves) and not is_terminated_func(line, leaf_index):
            # <Instance of 'Symbols' has no 'exprlist' member> pylint: disable = E1101

            leaf = line.leaves[leaf_index]

            # Treat commas as delimiters unless the commas are part of an expression list
            # (tuple assignment)
            if leaf.value == "," and (leaf.parent is None or leaf.parent.type != python_symbols.exprlist):
                break

            elif leaf.value == "(":
                children.append(Parens(line, leaf_index))
                leaf_index = children[-1].EndingIndex

            elif leaf.value == "{":
                children.append(Braces(line, leaf_index))
                leaf_index = children[-1].EndingIndex

            elif leaf.value == "[":
                children.append(Brackets(line, leaf_index))
                leaf_index = children[-1].EndingIndex

            elif process_single_line_func_args and leaf_index == 0 and SingleLineFuncArguments.IsSingleLineFuncArguments(
                line,
            ):
                children.append(SingleLineFuncArguments(line))
                leaf_index = len(line.leaves)

            else:
                if leaf.value == "=" and leaf.parent.type in [python_symbols.argument, python_symbols.typedargslist]:
                    is_default_arg = True

                elif leaf.value == "*":
                    # Do not allow a comma if this is the last arg
                    assert allow_trailing_comma is True

                    # The next leaf if the arg name and the next might be a parent
                    if leaf_index + 2 < len(line.leaves) and line.leaves[leaf_index + 2].value == ")":
                        allow_trailing_comma = False

                elif leaf.value == "**":
                    assert allow_trailing_comma is True
                    allow_trailing_comma = False

                leaf_index += 1

        self.StartingIndex                  = starting_index
        self.EndingIndex                    = leaf_index
        self.Children                       = children
        self.IsDefaultArg                   = is_default_arg
        self._allow_trailing_comma          = allow_trailing_comma

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

        leaf_index = self.StartingIndex
        for ending_index, child in GenerateIndexAndChild():
            assert leaf_index <= ending_index, (leaf_index, ending_index)

            while leaf_index != ending_index:
                leaf = line.leaves[leaf_index]
                leaf_index += 1

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
                suppress_final_comma=not child.AllowTrailingComma(),
                **should_be_split_kwargs
            )

            should_trim_prefix = False
            leaf_index = child.EndingIndex

        return col_offset

    # ----------------------------------------------------------------------
    @Interface.override
    def AllowTrailingComma(self):
        return self._allow_trailing_comma


# ----------------------------------------------------------------------
class SingleLineFuncArguments(_TokenParser):

    # ----------------------------------------------------------------------
    @staticmethod
    def IsSingleLineFuncArguments(line):
        return line.leaves and getattr(
            line.leaves[0],
            Plugin.IS_FIRST_FUNC_ARG_ATTRIBUTE_NAME,
            None,
        ) and getattr(line.leaves[-1], Plugin.IS_LAST_FUNC_ARG_ATTRIBUTE_NAME, None)

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def ShouldBeSplit(**should_be_split_kwargs):
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def IsBalanced():
        return True

    # ----------------------------------------------------------------------
    def __init__(self, line):
        children = []

        leaf_index = 0
        while leaf_index < len(line.leaves):
            if line.leaves[leaf_index].value == ",":
                leaf_index += 1

            children.append(
                Clause(
                    line,
                    leaf_index,
                    process_single_line_func_args=False,
                ),
            )
            leaf_index = children[-1].EndingIndex

        self.Children                       = children
        self.OpenIndex                      = 0
        self.EndingIndex                    = len(line.leaves)

    # ----------------------------------------------------------------------
    @Interface.override
    def OriginalLength(self, line):
        return self._OriginalLengthImpl(line, 0, len(line.leaves))

    # ----------------------------------------------------------------------
    @Interface.override
    def GenerateLines(
        self,
        max_func_line_length,
        line,
        new_lines,
        col_offset,
        should_trim_prefix,
        suppress_final_comma,
        **should_be_split_kwargs
    ):
        new_depth = new_lines[-1].depth
        col_offset = new_depth * 4

        for child_index, child in enumerate(self.Children):
            if child_index != 0:
                new_lines.append(black.Line(new_depth, []))

            child.GenerateLines(
                max_func_line_length,
                line,
                new_lines,
                col_offset,
                should_trim_prefix=True,
                **should_be_split_kwargs
            )

            if child.AllowTrailingComma() and (not suppress_final_comma or child_index != len(self.Children) - 1):
                new_lines[-1].leaves.append(black.Leaf(python_tokens.COMMA, ","))

        return col_offset

    # ----------------------------------------------------------------------
    @Interface.override
    def AllowTrailingComma(self):
        return True


# ----------------------------------------------------------------------
class Parens(_OpenCloseTokenImpl):

    # ----------------------------------------------------------------------
    # |  Types
    class Type(Enum):
        Comprehension                       = auto()
        Func                                = auto()
        Tuple                               = auto()

    # ----------------------------------------------------------------------
    # |  Properties
    OpenTokenValue                          = Interface.DerivedProperty("(")
    CloseTokenValue                         = Interface.DerivedProperty(")")

    # ----------------------------------------------------------------------
    # |  Methods
    def __init__(self, line, leaf_index):
        super(Parens, self).__init__(line, leaf_index)

        # ----------------------------------------------------------------------
        def GetType():
            if not self.IsBalanced():
                return None

            if self._IsComprehension(line):
                return self.__class__.Type.Comprehension

            if Plugin.IsFunc(line, leaf_index):
                return self.__class__.Type.Func

            # Empty tuple
            if self.CloseIndex == self.OpenIndex + 1:
                return self.__class__.Type.Tuple

            first_leaf = line.leaves[self.OpenIndex + 1]
            if first_leaf.parent and first_leaf.parent.type == python_symbols.testlist_gexp: # <Instance of 'Symbols' has no 'testlist_gexp' member> pylint: disable = E1101
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

        if any(
            child
            for child in self.Children
            if child.ShouldBeSplit(
                split_funcs_num_args=split_funcs_num_args,
                split_func_args_with_default=split_func_args_with_default,
                split_tuples_num_args=split_tuples_num_args,
                **should_be_split_kwargs
            )
        ):
            return True

        return False

    # ----------------------------------------------------------------------
    @Interface.override
    def AllowTrailingComma(self):
        return self.Type != self.__class__.Type.Comprehension

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @Interface.override
    def _ShouldSplitBasedOnLineLength(self):
        return self.Type == self.__class__.Type.Func


# ----------------------------------------------------------------------
class Braces(_OpenCloseTokenImpl):

    # ----------------------------------------------------------------------
    # |  Types
    class Type(Enum):
        Comprehension                       = auto()
        DictOrSet                           = auto()

    # ----------------------------------------------------------------------
    # |  Properties
    OpenTokenValue                          = Interface.DerivedProperty("{")
    CloseTokenValue                         = Interface.DerivedProperty("}")

    # ----------------------------------------------------------------------
    # |  Methods
    def __init__(self, line, leaf_index):
        super(Braces, self).__init__(line, leaf_index)

        # ----------------------------------------------------------------------
        def GetType():
            if not self.IsBalanced():
                return None

            if self._IsComprehension(line):
                return self.__class__.Type.Comprehension

            return self.__class__.Type.DictOrSet

        # ----------------------------------------------------------------------

        self.Type                           = GetType()

    # ----------------------------------------------------------------------
    @Interface.override
    def ShouldBeSplit(self, split_dictionaries_num_args, **should_be_split_kwargs):
        if split_dictionaries_num_args is not None and len(self.Children) >= split_dictionaries_num_args:
            return True

        if any(
            child for child in self.Children if child.ShouldBeSplit(
                split_dictionaries_num_args=split_dictionaries_num_args,
                **should_be_split_kwargs
            )
        ):
            return True

        return False

    # ----------------------------------------------------------------------
    @Interface.override
    def AllowTrailingComma(self):
        return self.Type == self.__class__.Type.DictOrSet


# ----------------------------------------------------------------------
class Brackets(_OpenCloseTokenImpl):

    # ----------------------------------------------------------------------
    # |  Types
    class Type(Enum):
        Index                               = auto()
        Comprehension                       = auto()
        List                                = auto()

    # ----------------------------------------------------------------------
    # |  Properties
    OpenTokenValue                          = Interface.DerivedProperty("[")
    CloseTokenValue                         = Interface.DerivedProperty("]")

    # ----------------------------------------------------------------------
    # |  Methods
    def __init__(self, line, leaf_index):
        super(Brackets, self).__init__(line, leaf_index)

        # ----------------------------------------------------------------------
        def GetType():
            if not self.IsBalanced():
                return None

            if self._IsComprehension(line):
                return self.__class__.Type.Comprehension

            if (
                line.leaves[self.OpenIndex].parent is None
                or line.leaves[self.OpenIndex].parent.type != python_symbols.atom  # <Instance of 'Symbols' has no 'atom' member> pylint: disable = E1101
                or line.leaves[self.CloseIndex].parent is None
                or line.leaves[self.CloseIndex].parent.type != python_symbols.atom # <Instance of 'Symbols' has no 'atom' member> pylint: disable = E1101
            ):
                return self.__class__.Type.Index

            return self.__class__.Type.List

        # ----------------------------------------------------------------------

        self.Type                           = GetType()

    # ----------------------------------------------------------------------
    @Interface.override
    def ShouldBeSplit(self, split_lists_num_args, **should_be_split_kwargs):
        if self.Type == self.__class__.Type.Index:
            return False

        if split_lists_num_args is not None and len(self.Children) >= split_lists_num_args:
            return True

        if any(
            child for child in self.Children if child.ShouldBeSplit(
                split_lists_num_args=split_lists_num_args,
                **should_be_split_kwargs
            )
        ):
            return True

        return False

    # ----------------------------------------------------------------------
    @Interface.override
    def AllowTrailingComma(self):
        return self.Type == self.__class__.Type.List
