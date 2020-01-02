# ----------------------------------------------------------------------
# |
# |  HorizontalAlignmentImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-29 10:13:46
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the HorizontalAlignmentImpl object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

from PythonFormatterImpl.Plugin import PluginBase

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class HorizontalAlignmentImpl(PluginBase):

    # ----------------------------------------------------------------------
    # |  Methods
    def __init__(
        self,
        alignment_columns=None,
    ):
        self._alignment_columns             = alignment_columns or [45, 57, 77]

    # ----------------------------------------------------------------------
    @Interface.override
    def PostprocessBlocks(self, blocks):
        # Import here to avoid problems on python2.7
        from blib2to3.pygram import token as python_tokens

        for block in blocks:
            alignment_tokens = []
            max_line_length = 0

            for line in block:
                alignment_token = self._GetAlignmentToken(line, not alignment_tokens)
                if alignment_token is None and not (
                    self._AlignToLinesWithoutAlignmentToken and alignment_tokens
                ):
                    continue

                # Get the contents before the token
                contents = []

                for token in line.leaves:
                    if token == alignment_token:
                        break

                    # Comments don't count when calculating maximum line lengths
                    if token.value.startswith("#"):
                        continue

                    # Multiline strings don't count when calculating maximum line lengths
                    # (unless they appear on a line with the token itself)
                    if (
                        alignment_token is None
                        and token.type == python_tokens.STRING
                        and (token.value.startswith('"""') or token.value.startswith("'''"))
                    ):
                        continue

                    contents += [token.prefix, token.value]

                line_length = len(("".join(contents)).lstrip()) + 4 * line.depth
                max_line_length = max(max_line_length, line_length)

                if alignment_token is not None:
                    alignment_tokens.append((alignment_token, line_length))

            if not alignment_tokens:
                continue

            # Calculate the alignment value
            alignment_column = max_line_length + 2

            for potential_column_value in self._alignment_columns:
                if potential_column_value > alignment_column:
                    alignment_column = potential_column_value
                    break

            # Align
            for token, line_length in alignment_tokens:
                assert line_length < alignment_column, (line_length, alignment_column)
                token.prefix = " " * (alignment_column - line_length - 1)

    # ----------------------------------------------------------------------
    # |  Private Properties
    @Interface.abstractproperty
    def _AlignToLinesWithoutAlignmentToken(self):
        """If True, the length of lines without alignment tokens will participate in the
           calculation of the overall alignment value. If False, only lines with tokens will participate
           in this calculation."""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @Interface.abstractmethod
    def _GetAlignmentToken(line, is_initial_line):
        """Returns a token that should be horizontally aligned or None if no such token exists on this line"""
        raise Exception("Abstract method")
