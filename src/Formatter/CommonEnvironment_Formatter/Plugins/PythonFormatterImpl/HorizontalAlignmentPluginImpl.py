# ----------------------------------------------------------------------
# |
# |  HorizontalAlignmentPluginImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-12-17 17:18:49
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the HorizontalAlignmentPluginImpl object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

from PluginBase import PluginBase

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class HorizontalAlignmentPluginImpl(PluginBase):
    """Contains functionality common to plugins that horizontally align content"""

    # ----------------------------------------------------------------------
    # |  Public Methods
    @classmethod
    @Interface.override
    def Decorate(
        cls,
        lines,
        alignment_columns=None,
        *args,
        **kwargs
    ):
        alignment_columns = alignment_columns or [45, 57, 77]

        for _, block_lines in cls.EnumerateBlocks(lines):
            alignment_leaves = []
            max_line_length = 0

            for line in block_lines:
                if cls.IgnoreLine(line):
                    continue

                alignment_leaf = cls._GetAlignmentLeaf(line, not alignment_leaves, *args, **kwargs)
                if alignment_leaf is None and not (cls._AlignToLinesWithoutAlignmentLeaf and alignment_leaves):
                    continue

                # Get the contents before the leaf
                contents = []

                for leaf in line.leaves:
                    if leaf == alignment_leaf:
                        break

                    # Comments don't count when calculating maximum line lengths
                    if leaf.value.startswith("#"):
                        continue

                    contents += [leaf.prefix, leaf.value]

                line_length = len("".join(contents)) + 4 * line.depth

                max_line_length = max(max_line_length, line_length)

                if alignment_leaf is not None:
                    alignment_leaves.append((alignment_leaf, line_length))

            if not alignment_leaves:
                continue

            # Calculate the alignment value
            alignment_column = max_line_length + 2

            for potential_column_value in alignment_columns:
                if potential_column_value > alignment_column:
                    alignment_column = potential_column_value
                    break

            # Align
            for leaf, line_length in alignment_leaves:
                assert line_length < alignment_column, (line_length, alignment_column)
                leaf.prefix = " " * (alignment_column - line_length - 1)

        return lines

    # ----------------------------------------------------------------------
    # |  Private Properties
    @Interface.abstractproperty
    def _AlignToLinesWithoutAlignmentLeaf(self):
        """\
        If True, the length of lines without alignment leaves are used to
        calculate the overall alignment length.
        """
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @Interface.abstractmethod
    def _GetAlignmentLeaf(line, is_initial_line, *args, **kwargs):
        """Returns a leaf that should be horizontally aligned or None if no leaf exists"""
        raise Exception("Abstract method")
