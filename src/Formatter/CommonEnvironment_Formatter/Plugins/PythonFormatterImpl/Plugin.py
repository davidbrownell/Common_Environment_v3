# ----------------------------------------------------------------------
# |
# |  Plugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-22 12:50:54
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the PluginBase object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class PluginBase(Interface.Interface):
    """Abstract base class for all plugins"""

    # ----------------------------------------------------------------------
    # |  Types

    # Plugins are invoked from highest- (lowest number) to lowest- (highest number) priority
    STANDARD_PRIORITY                       = 10000

    # ----------------------------------------------------------------------
    # |  Properties
    @Interface.abstractproperty
    def Name(self):
        """Name of the plugin"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def Priority(self):
        """Integer priority value; plugins with higher priority have lower numerical values."""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |
    # |  Methods
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def PreprocessTokens(tokenizer, tokenize_func, recurse_count):
        """Opportunity to modify tokens before black is called.

        Args:
            tokenizer (Tokenizer):
                The input tokenizer.

            tokenize_func (Callable[[Tokenizer], Tokenizer]):
                Function that is able to tokenize a sub-clause.

            recurse_count (int):
                Current recurse level.

        Returns (None):
            None.

        """

        # Default implementation is a noop
        pass

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def PreprocessBlocks(blocks):
        """Opportunity to modify blocks before black is called.

        Args:
            blocks (List[List[black.Line]]):
                A collection blocks, where a block is a collection of lines delimited by one or more blank lines.

        Returns (None):
            None.

        """

        # Default implementation is a noop
        pass

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def PreprocessLines(lines):
        """Opportunity to modify lines before black is called.

        Args:
            lines (List[black.Line]):
                Black Lines.

        Returns (List[black.Line]):
            The return value.

        """

        # Default implementation is a noop
        return lines

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def DecorateTokens(tokenizer, tokenize_func, recurse_count):
        """Opportunity to modify tokens after black is called.

        Args:
            tokenizer (Tokenizer):
                The input tokenizer.

            tokenize_func (Callable[[Tokenizer], Tokenizer]):
                Function that is able to tokenize a sub-clause.

            recurse_count (int):
                Current recurse level.

        Returns (None):
            None.

        """

        # Default implementation is a noop
        pass

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def DecorateBlocks(blocks):
        """Opportunity to modify blocks after black is called.

        Args:
            blocks (List[List[black.Line]]):
                A collection blocks, where a block is a collection of lines delimited by one or more blank lines.

        Returns (None):
            None.

        """

        # Default implementation is a noop
        pass

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def DecorateLines(lines):
        """Opportunity to modify lines after black is called.

        Args:
            lines (List[black.Line]):
                Black Lines.

        Returns (List[black.Line]):
            The return value.

        """

        # Default implementation is a noop
        return lines

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def PostprocessTokens(tokenizer, tokenize_func, recurse_count):
        """Opportunity to modify tokens after plugin decoration is complete.

        Args:
            tokenizer (Tokenizer):
                The input tokenizer.

            tokenize_func (Callable[[Tokenizer], Tokenizer]):
                Function that is able to tokenize a sub-clause.

            recurse_count (int):
                Current recurse level.

        Returns (None):
            None.

        """

        # Default implementation is a noop
        pass

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def PostprocessBlocks(blocks):
        """Opportunity to modify blocks after plugin decoration is complete.

        Args:
            blocks (List[List[black.Line]]):
                A collection blocks, where a block is a collection of lines delimited by one or more blank lines.

        Returns (None):
            None.

        """

        # Default implementation is a noop
        pass

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def PostprocessLines(lines):
        """Opportunity to modify lines after plugin decoration is complete.

        Args:
            lines (List[black.Line]):
                Black Lines.

        Returns (List[black.Line]):
            The return value.

        """

        # Default implementation is a noop
        return lines

    # ----------------------------------------------------------------------
    # |
    # |  Protected Methods
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    def _GetRootTokenIndex(
        tokens,
        root_token_value,
        first_index=None,
        last_index=None,
    ):
        """Returns the first index of a token whose value matches the specified value.

        Args:
            tokens (List[black.Leaf]):
                Tokens to search.

            root_token_value (str):
                Value to search for.

            first_index=None (Optional[int]):
                Optional starting index.

            last_index=None (Optional[int]):
                Optional ending index.

        Returns (Optional[int]):
            Index or None.

        """

        index = first_index or 0
        last_index = last_index or len(tokens)
        assert index <= last_index, (index, last_index)

        paren_count = 0
        bracket_count = 0
        brace_count = 0

        while index != last_index:
            token = tokens[index]
            token_value = token.value

            if token_value == "(":
                paren_count += 1
            elif token_value == ")":
                paren_count -= 1
            elif token_value == "[":
                paren_count += 1
            elif token_value == "]":
                paren_count -= 1
            elif token_value == "{":
                brace_count += 1
            elif token_value == "}":
                brace_count -= 1

            if (
                token_value == root_token_value
                and paren_count == 0
                and bracket_count == 0
                and brace_count == 0
            ):
                return index

            index += 1

        return None

    # ----------------------------------------------------------------------
    @classmethod
    def _GetMatchingTokenNoThrow(
        cls,
        tokens,
        first_index=None,
        last_index=None,
    ):
        """Returns the index of the token that matches the current token"""

        first_index = first_index or 0
        last_index = last_index or len(tokens)

        token = tokens[first_index]

        if token.value == "(":
            matching_token_value = ")"
        elif token.value == "[":
            matching_token_value = "]"
        elif token.value == "{":
            matching_token_value = "}"
        else:
            raise Exception("'{}' is not a supported token".format(token.value))

        return cls._GetRootTokenIndex(
            tokens,
            matching_token_value,
            first_index=first_index,
            last_index=last_index,
        )

    # ----------------------------------------------------------------------
    @classmethod
    def _GetMatchingToken(
        cls,
        tokens,
        first_index=None,
        last_index=None,
    ):
        result = cls._GetMatchingTokenNoThrow(
            tokens,
            first_index=first_index,
            last_index=last_index,
        )

        if result is None:
            raise Exception("The matching token could not be found")

        return result
