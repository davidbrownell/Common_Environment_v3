# ----------------------------------------------------------------------
# |
# |  SplitterImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-27 17:47:51
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the SplitterImpl object"""

import os
import sys

import black
from blib2to3.pygram import python_symbols, token as python_tokens
import six

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import Interface

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, ".."))
with CallOnExit(lambda: sys.path.pop(0)):
    from Plugin import PluginBase
    from Tokenizer import StandardTokenizer

# ----------------------------------------------------------------------
class SplitterImpl(PluginBase):
    """Splits elements of a container if necessary"""

    # ----------------------------------------------------------------------
    # |  Properties
    Priority                                = Interface.DerivedProperty(PluginBase.STANDARD_PRIORITY)

    # ----------------------------------------------------------------------
    # |  Methods
    def __init__(
        self,
        num_args=None,
    ):
        self._num_args                      = self._DefaultSplitArgsValue if num_args is None else num_args

    # ----------------------------------------------------------------------
    @Interface.override
    def PreprocessTokens(self, tokenizer, tokenize_func, recurse_count):
        # ----------------------------------------------------------------------
        def ShouldSplit(args_list):
            if len(args_list) > self._num_args:
                return True

            for args in args_list:
                if self._HasNewline(args):
                    return True

                if self._ShouldSplitBasedOnArgs(args):
                    return True

            return False

        # ----------------------------------------------------------------------

        return self._ProcessTokensImpl(tokenizer, tokenize_func, ShouldSplit)

    # ----------------------------------------------------------------------
    @Interface.override
    def DecorateTokens(self, tokenizer, tokenize_func, recurse_count):
        # ----------------------------------------------------------------------
        def ShouldSplit(args_list):
            for args in args_list:
                if self._HasNewline(args):
                    return True

            return False

        # ----------------------------------------------------------------------

        return self._ProcessTokensImpl(tokenizer, tokenize_func, ShouldSplit)

    # ----------------------------------------------------------------------
    # |  Private Properties
    @Interface.abstractproperty
    def _DefaultSplitArgsValue(self):
        """If no value is provided, split the item when it has more than this number of items"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @Interface.abstractmethod
    def _IsInitialToken(token):
        """Returns True if the token is the beginning of a group that should be processed.

        The definition of a 'group' depends on the context. For example, a beginning token
        is '[' for lists, '(' for tuples, '{' for dicts.
        """
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def _InsertTrailingComma(args):
        """Return True if a trailing comma should be inserted after the final argument"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.extensionmethod
    def _ShouldSplitBasedOnArgs(args):
        """Return True if data within the arguments should force all of the content to be split"""

        # By default, there is nothing inherent to the args that would cause a split.
        return False

    # ----------------------------------------------------------------------
    @staticmethod
    def _HasNewline(tokens):
        """Returns True if there is a newline in any of the tokens"""

        for token in tokens:
            if token == StandardTokenizer.NEWLINE:
                return True

            value = token.value
            if isinstance(value, six.string_types) and "\n" in value:
                return True

        return False

    # ----------------------------------------------------------------------
    def _ProcessTokensImpl(self, tokenizer, tokenize_func, should_split_func):
        token_index = 0

        while token_index < len(tokenizer.Tokens):
            token = tokenizer.Tokens[token_index]

            if self._IsInitialToken(token):
                last_index = self._GetMatchingToken(
                    tokenizer.Tokens,
                    first_index=token_index,
                )

                args_info = self._ExtractArgsInfo(
                    tokenizer.Tokens,
                    first_index=token_index + 1,
                    last_index=last_index,
                )

                if args_info:
                    # Tokenize the tokens
                    for (
                        args_info_index,
                        (args_info_tokens, args_info_comments),
                    ) in enumerate(args_info):
                        args_info[args_info_index][0] = tokenize_func(
                            StandardTokenizer(args_info_tokens),
                        ).Tokens

                    # ----------------------------------------------------------------------
                    def ShouldSplit():
                        # We need to split if there are embedded comments associated with more than one line
                        for _, arg_info_comments in args_info:
                            if arg_info_comments:
                                return True

                        # Do we need to split based on the args?
                        if should_split_func([tokens for tokens, _ in args_info]):
                            return True

                        return False

                    # ----------------------------------------------------------------------

                    if ShouldSplit():
                        new_tokens = [
                            token,
                            StandardTokenizer.NEWLINE,
                            StandardTokenizer.INDENT,
                        ]

                        arg_tokens_to_strip = [
                            StandardTokenizer.INDENT,
                            StandardTokenizer.DEDENT,
                            StandardTokenizer.NEWLINE,
                        ]

                        for index, (tokens, comments) in enumerate(args_info):
                            # Strip existing newlines, indents, and dedents from the content
                            strip_index = 0
                            while (
                                strip_index < len(tokens)
                                and tokens[strip_index] in arg_tokens_to_strip
                            ):
                                strip_index += 1

                            if strip_index != 0:
                                tokens = tokens[strip_index:]

                            while tokens and tokens[-1] in arg_tokens_to_strip:
                                tokens = tokens[:-1]

                            if tokens:
                                tokens[0].prefix = ""
                                new_tokens += tokens

                                if index != len(args_info) - 1 or self._InsertTrailingComma(
                                    tokens,
                                ):
                                    new_tokens.append(black.Leaf(python_tokens.COMMA, ","))

                            if comments:
                                new_tokens += comments

                            if tokens or comments:
                                new_tokens += [StandardTokenizer.NEWLINE]

                        new_tokens += [
                            StandardTokenizer.DEDENT,
                            tokenizer.Tokens[last_index],
                        ]

                        tokenizer.ReplaceTokens(token_index, last_index, new_tokens)

                token_index = last_index
            else:
                token_index += 1

    # ----------------------------------------------------------------------
    @classmethod
    def _ExtractArgsInfo(
        cls,
        tokens,
        first_index=None,
        last_index=None,
    ):
        first_index = first_index or 0
        last_index = last_index or len(tokens)

        # ----------------------------------------------------------------------
        def StartsWithLambda(initial_index):
            while (
                initial_index < last_index
                and tokens[initial_index] in StandardTokenizer.FAKE_TOKENS
            ):
                initial_index += 1

            return initial_index != last_index and tokens[initial_index].value == "lambda"

        # ----------------------------------------------------------------------

        results = []

        while first_index < last_index:
            if StartsWithLambda(first_index):
                # Move past all the commas within the lambda
                first_comma_search_index = cls._GetRootTokenIndex(
                    tokens,
                    ":",
                    first_index=first_index,
                    last_index=last_index,
                )
                assert first_comma_search_index
            else:
                first_comma_search_index = first_index

            comma_index = cls._GetRootTokenIndex(
                tokens,
                ",",
                first_index=first_comma_search_index,
                last_index=last_index,
            )

            # Get the args
            if comma_index is None:
                # Get the tokens and comments (where the comment comes
                # before the last index)
                these_tokens = tokens[first_index:last_index]
                first_index = last_index

            else:
                these_tokens = tokens[first_index:comma_index]
                first_index = comma_index + 1

                # Associate any trailing comments with this set of tokens
                while (
                    first_index < last_index
                    and tokens[first_index].type == python_tokens.COMMENT
                ):
                    these_tokens.append(tokens[first_index])
                    first_index += 1

            # Extract the comments associated with this arg
            these_comments = []

            token_index = 0
            while token_index < len(these_tokens):
                this_token = these_tokens[token_index]

                if this_token.type == python_tokens.COMMENT:
                    these_comments.append(these_tokens.pop(token_index))
                else:
                    token_index += 1

            results.append([these_tokens, these_comments])

        return results


# ----------------------------------------------------------------------
@Interface.mixin
class SimpleInitialTokenMixin(object):
    """Mixin that implements _IsInitialToken by looking at the token's sibling's type"""

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def _IsInitialToken(cls, token):
        if not hasattr(cls, "_IsInitialToken_IsTokenType"):
            if isinstance(cls._InitialTokenType, list):
                # ----------------------------------------------------------------------
                def IsTokenType(token_type):
                    return token_type in cls._InitialTokenType

                # ----------------------------------------------------------------------
            else:
                # ----------------------------------------------------------------------
                def IsTokenType(token_type):
                    return token_type == cls._InitialTokenType

                # ----------------------------------------------------------------------

            cls._IsInitialToken_IsTokenType = IsTokenType

        return (
            hasattr(token, "next_sibling")
            and token.next_sibling
            and cls._IsInitialToken_IsTokenType(token.next_sibling.type)
        )

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def _InitialTokenType(self):
        """Token type used to find arguments of the desired container type"""
        raise Exception("Abstract property")
