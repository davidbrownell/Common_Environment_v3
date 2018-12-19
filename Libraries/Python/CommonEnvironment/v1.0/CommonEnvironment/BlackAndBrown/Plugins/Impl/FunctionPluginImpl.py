# ----------------------------------------------------------------------
# |
# |  FunctionPluginImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-12-18 15:36:23
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the FunctionPluginImpl object"""

import os

from collections import OrderedDict

import black
from blib2to3.pygram import python_symbols, token as python_tokens
import six

import CommonEnvironment
from CommonEnvironment import Interface

from CommonEnvironment.BlackAndBrown.Plugins import Plugin as PluginBase

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class FunctionPluginImpl(PluginBase):
    """Contains functionality common to plugins that process functions or function calls"""

    # ----------------------------------------------------------------------
    # |  Public Methods
    @classmethod
    @Interface.override
    def Decorate(cls, lines, *args, **kwargs):
        modifications = OrderedDict()

        for line_index, line in enumerate(lines):
            if not line.leaves:
                continue

            if not line.leaves[0].parent:
                continue
            
            # Function definition
            if line.leaves[0].parent.type == python_symbols.funcdef:
                if not cls._ShouldSplitFunctionArgs(line, *args, **kwargs):
                    continue
            
                # Account for the 'def'
                leaf_offset = 1

            # Function call
            elif line.leaves[0].parent.type == python_symbols.power:
                # Ensure that the closing paren falls on this line.
                # If not, the function has already been split
                # (and will have one argument per line).
                if not any(leaf for leaf in line.leaves if leaf.value == ')') or \
                   not cls._ShouldSplitFunctionArgs(line, *args, **kwargs):
                    continue
            
                leaf_offset = 0

            else:
                continue
                
            # If here, we are going to split the function arguments across multiple
            # lines. Get a list of the arguments.

            # At the least, there is a func name, '(', and ')'
            assert len(line.leaves) > 3 + (leaf_offset * 2), (leaf_offset, line.leaves)
            
            if line.leaves[1 + leaf_offset].value != '(' or \
               line.leaves[-1 - leaf_offset].value != ')':
                continue

            # Construct the new argument list
            all_arg_leafs = []
            arg_leafs = []

            # ----------------------------------------------------------------------
            def CommitArg():
                assert arg_leafs

                if arg_leafs[-1].value != ',' and \
                   (len(arg_leafs) < 2 or not arg_leafs[-2].value == "**"):
                        arg_leafs.append(black.Leaf(python_tokens.COMMA, ','))

                all_arg_leafs.append(list(arg_leafs))
                arg_leafs[:] = []

            # ----------------------------------------------------------------------

            for leaf in line.leaves[2 + leaf_offset : -1 - leaf_offset]:
                arg_leafs.append(leaf)

                if leaf.value == ',':
                    CommitArg()
                
            if arg_leafs:
                CommitArg()

            new_lines = [ black.Line(line.depth, line.leaves[:2 + leaf_offset]), ]

            for arg_leafs in all_arg_leafs:
                assert arg_leafs
                arg_leafs[0].prefix = ''

                new_lines.append(black.Line(line.depth + 1, arg_leafs))

            new_lines.append(black.Line(line.depth, line.leaves[-1 -leaf_offset :]))

            modifications[line_index] = new_lines

        # Process modifications
        if modifications:
            for line_index in reversed(list(six.iterkeys(modifications))):
                new_lines = modifications[line_index]
                new_lines[-1].comments = lines[line_index].comments

                del lines[line_index]

                for new_line in reversed(new_lines):
                    lines.insert(line_index, new_line) 

        return lines

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @Interface.abstractmethod
    def _ShouldSplitFunctionArgs(line, *args, **kwargs):
        """\
        Returns True if arguments associated with the function call or definition 
        on line should be split across multiple lines.
        """
        raise Exception("Abstract method")
