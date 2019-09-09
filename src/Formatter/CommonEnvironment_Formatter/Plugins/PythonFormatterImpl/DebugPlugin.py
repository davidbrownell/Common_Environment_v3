# ----------------------------------------------------------------------
# |
# |  DebugPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-27 16:47:43
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

import inflect as inflect_mod

import CommonEnvironment
from CommonEnvironment.BitFlagEnum import BitFlagEnum, auto
from CommonEnvironment import Interface

from PythonFormatterImpl.Plugin import PluginBase       # <Unable to import> pylint: disable = E0401
from PythonFormatterImpl.Tokenizer import Tokenizer     # <Unable to import> pylint: disable = E0401

from PythonFormatterImpl.Impl.BlackImports import black

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
class Plugin(PluginBase):
    """Writes content output"""

    # ----------------------------------------------------------------------
    # |  Types
    class Flag(BitFlagEnum):
        PreprocessTokens                    = auto()
        PreprocessBlocks                    = auto()
        DecorateTokens                      = auto()
        DecorateBlocks                      = auto()
        PostprocessTokens                   = auto()
        PostprocessBlocks                   = auto()

        PreprocessFlags                     = PreprocessTokens | PreprocessBlocks
        DecorateFlags                       = DecorateTokens | DecorateBlocks
        PostprocessFlags                    = PostprocessTokens | PostprocessBlocks

        AllFlags                            = PreprocessFlags | DecorateFlags | PostprocessFlags

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("Debug")

    @Interface.DerivedProperty
    def Priority(self):
        return self._priority

    # ----------------------------------------------------------------------
    def __init__(
        self,
        flags=Flag.AllFlags,
        priority=1,
    ):
        self._flags                         = flags
        self._priority                      = priority

    # ----------------------------------------------------------------------
    @Interface.override
    def PreprocessTokens(self, tokenizer, tokenize_func, recurse_count):
        if recurse_count != 0:
            return

        if not self._flags & self.Flag.PreprocessTokens:
            return

        self._DisplayTokens("PreprocessTokens", tokenizer.Tokens)

    # ----------------------------------------------------------------------
    @Interface.override
    def PreprocessBlocks(self, blocks):
        if not self._flags & self.Flag.PreprocessBlocks:
            return

        self._DisplayBlocks("PreprocessBlocks", blocks)

    # ----------------------------------------------------------------------
    @Interface.override
    def DecorateTokens(self, tokenizer, tokenize_func, recurse_count):
        if recurse_count != 0:
            return

        if not self._flags & self.Flag.DecorateTokens:
            return

        self._DisplayTokens("DecorateTokens", tokenizer.Tokens)

    # ----------------------------------------------------------------------
    @Interface.override
    def DecorateBlocks(self, blocks):
        if not self._flags & self.Flag.DecorateBlocks:
            return

        self._DisplayBlocks("DecorateBlocks", blocks)

    # ----------------------------------------------------------------------
    @Interface.override
    def PostprocessTokens(self, tokenizer, tokenize_func, recurse_count):
        if recurse_count != 0:
            return

        if not self._flags & self.Flag.PostprocessTokens:
            return

        self._DisplayTokens("PostprocessTokens", tokenizer.Tokens)

    # ----------------------------------------------------------------------
    @Interface.override
    def PostprocessBlocks(self, blocks):
        if not self._flags & self.Flag.PostprocessBlocks:
            return

        self._DisplayBlocks("PostprocessBlocks", blocks)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _DisplayTokens(cls, header, tokens):
        sys.stdout.write(
            textwrap.dedent(
                """\

                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # |
                # |  {}
                # |
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                """,
            ).format(header),
        )

        line_index = 1

        start_index = 0
        while start_index < len(tokens):
            end_index = start_index

            while end_index < len(tokens) and tokens[end_index] != Tokenizer.NEWLINE:
                end_index += 1

            end_index += 1

            cls._DisplayLine(
                tokens[start_index:end_index],
                line_index,
                display_tokens=True,
            )

            start_index = end_index
            line_index += 1

            sys.stdout.write("\n")

    # ----------------------------------------------------------------------
    @classmethod
    def _DisplayBlocks(cls, header, blocks):
        sys.stdout.write(
            textwrap.dedent(
                """\

                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # |
                # |  {}
                # |
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                # ----------------------------------------------------------------------
                """,
            ).format(header),
        )

        for block_index, block in enumerate(blocks):
            sys.stdout.write(
                "Block {}) {}\n\n".format(block_index + 1, inflect.no("line", len(block))),
            )

            for line_index, line in enumerate(block):
                cls._DisplayLine(
                    line.leaves,
                    line_index + 1,
                    display_tokens=False,
                    display_prefix="    ",
                )

            sys.stdout.write("\n")

    # ----------------------------------------------------------------------
    @staticmethod
    def _DisplayLine(
        line_tokens,
        line_index,
        display_tokens=True,
        display_prefix="",
    ):
        symbol_table = black.pygram.python_grammar.number2symbol

        # Create the line's content for display
        line_template = "{}Line {{}}){{}}\n{}".format(
            display_prefix,
            "\n" if display_tokens else "",
        )

        line_content = []

        for token in line_tokens:
            if token in [Tokenizer.INDENT, Tokenizer.DEDENT, Tokenizer.NEWLINE]:
                continue

            line_content.append("{}{}".format(token.prefix, token.value))

        line_content = "".join(line_content)
        if line_content and line_content[0] != "\n":
            line_content = " {}".format(line_content)

        sys.stdout.write(line_template.format(line_index, line_content))

        if display_tokens:
            for token_index, token in enumerate(line_tokens):
                if token == Tokenizer.INDENT:
                    value = symbol = "INDENT"
                    prefix = ""
                elif token == Tokenizer.DEDENT:
                    value = symbol = "DEDENT"
                    prefix = ""
                elif token == Tokenizer.NEWLINE:
                    value = symbol = "NEWLINE"
                    prefix = ""
                else:
                    value = token.value
                    prefix = token.prefix

                    if token.parent is not None:
                        symbol = symbol_table[token.parent.type]
                    else:
                        symbol = "<None>"

                sys.stdout.write(
                    "    Token {0:>3}) {1:25}  {2:>2}  {3}\n".format(
                        token_index,
                        value,
                        len(prefix),
                        symbol,
                    ),
                )
