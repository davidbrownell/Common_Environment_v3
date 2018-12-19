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

from CommonEnvironment.BlackAndBrown.Plugins import Plugin as PluginBase

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class HorizontalAlignmentPluginImpl(PluginBase):
    """Contains functionality common to plugins that horizontally align content"""
    
    # ----------------------------------------------------------------------
    # |  Public Methods
    @classmethod
    @Interface.override
    def Decorate(cls, lines, alignment_columns, *args, **kwargs):
        line_index = 0
        while line_index < len(lines):
            line = lines[line_index]

            # Does this line have a leaf that should be aligned
            if cls._GetAlignmentLeaf(line, True, *args, **kwargs) is None:
                line_index += 1
                continue

            # Get the length of all leaves prior to the one that should be aligned
            is_initial_line = True
            
            alignment_leaves = []
            max_line_length = 0

            while True:
                if line_index == len(lines):
                    break

                line = lines[line_index]
                line_index += 1
                
                if not line.leaves:
                    break

                alignment_leaf = cls._GetAlignmentLeaf(line, is_initial_line, *args, **kwargs)
                is_initial_line = False

                contents = []

                for leaf in line.leaves:
                    if leaf == alignment_leaf:
                        break

                    contents += [ leaf.prefix, leaf.value ]

                line_length = len(''.join(contents)) + 4 * line.depth
                
                max_line_length = max(max_line_length, line_length)
                
                if alignment_leaf is not None:
                    alignment_leaves.append(( alignment_leaf, line_length ))
                
            # Calculate the alignment value
            alignment_column = max_line_length + 2

            for potential_column_value in alignment_columns:
                if potential_column_value > alignment_column:
                    alignment_column = potential_column_value
                    break

            # Align
            for leaf, line_length in alignment_leaves:
                assert line_length < alignment_column, (line_length, alignment_column)
                leaf.prefix = ' ' * (alignment_column - line_length - 1)

        return lines

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @Interface.abstractmethod
    def _GetAlignmentLeaf(line, is_initial_line, *args, **kwargs):
        """Returns a leaf that should be horizontally aligned or None if no leaf exists"""
        raise Exception("Abstract method")
