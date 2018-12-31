# ----------------------------------------------------------------------
# |
# |  AlignAssignmentsPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-12-17 21:18:10
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

import os

import CommonEnvironment
from CommonEnvironment import Interface

from CommonEnvironment.BlackAndBrown.Plugins.AlignTrailingCommentsPlugin import Plugin as AlignTrailingCommentsPlugin
from CommonEnvironment.BlackAndBrown.Plugins.Impl.HorizontalAlignmentPluginImpl import HorizontalAlignmentPluginImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(HorizontalAlignmentPluginImpl):
    # ----------------------------------------------------------------------
    # |  Types

    # Not using Python3 enum to maintain compatibility with Python2
    ModuleLevel                             = 1         # Align assignments at the module level
    ClassLevel                              = 2         # Align assignments at the class level
    InitLevel                               = 4         # Align self-based assignments in __init__ methods
    InitAnyLevel                            = 8         # Align (any) assignments in __init__ methods
    MethodLevel                             = 16        # Align assignments in modules (except __init__)

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("AlignAssignments")
    Priority                                = Interface.DerivedProperty(
        AlignTrailingCommentsPlugin.Priority - 1
    )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def _GetAlignmentLeaf(
        cls,
        line,
        is_initial_line,
        flags=None,
    ):
        # Importing here as black isn't supported by python2
        from blib2to3.pygram import python_symbols

        if flags is None:
            flags = cls.ModuleLevel | cls.ClassLevel | cls.InitLevel

        nested = 0

        for leaf in line.leaves:
            if leaf.value == "(":
                nested += 1

            elif leaf.value == ")":
                nested -= 1

            elif leaf.value == "=" and nested == 0:

                node = leaf.parent

                while node:
                    if node.type == python_symbols.classdef:
                        return leaf if flags & cls.ClassLevel else None

                    if node.type == python_symbols.funcdef:
                        # This code will be hit on the first leaf of a line
                        # that is a function def. Look at the function
                        # definition's name to determine what kind of method
                        # it is.
                        assert len(node.children) > 2, node.children
                        if node.children[1].value == "__init__":
                            if flags & cls.InitAnyLevel:
                                return leaf

                            if flags & cls.InitLevel and line.leaves[0].value == "self" and line.leaves[1].value == ".":
                                return leaf

                            return None

                        return leaf if flags & cls.MethodLevel else None

                    node = node.parent

                return leaf if flags & cls.ModuleLevel else None

        return None
