# ----------------------------------------------------------------------
# |
# |  AlignAssignmentsPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-29 10:24:07
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

import CommonEnvironment
from CommonEnvironment.BitFlagEnum import BitFlagEnum, auto
from CommonEnvironment import Interface

from PythonFormatterImpl.Impl.BlackImports import black, python_symbols              # <Unable to import> pylint: disable = E0401
from PythonFormatterImpl.Impl.HorizontalAlignmentImpl import HorizontalAlignmentImpl # <Unable to import> pylint: disable = E0401

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Plugin(HorizontalAlignmentImpl):
    """Horizontally aligns assignment statements within a block"""

    # ----------------------------------------------------------------------
    # |  Types
    class Flag(BitFlagEnum):
        ModuleLevel                         = auto()    # Align assignments at the module level
        ClassLevel                          = auto()    # Align assignments at the class level
        InitLevel                           = auto()    # Align self-based assignments in __init__ methods
        InitAnyLevel                        = auto()    # Align any assignment in __init__ methods
        MethodLevel                         = auto()    # Align assignments in methods other than __init__

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("AlignAssignments")
    Priority                                = Interface.DerivedProperty(HorizontalAlignmentImpl.STANDARD_PRIORITY)

    # ----------------------------------------------------------------------
    # |  Methods
    # <Keyword argument before variable positional arguments> pylint: disable = W1113
    def __init__(
        self,
        alignment_flags=None,
        *args,
        **kwargs
    ):
        if alignment_flags is None:
            alignment_flags = self.Flag.ModuleLevel | self.Flag.ClassLevel | self.Flag.InitLevel

        self._alignment_flags               = alignment_flags

        super(Plugin, self).__init__(*args, **kwargs)

    # ----------------------------------------------------------------------
    # |  Private Properties
    _AlignToLinesWithoutAlignmentToken      = Interface.DerivedProperty(False)

    # ----------------------------------------------------------------------
    # |  Private Methods
    @Interface.override
    def _GetAlignmentToken(
        self,
        line,
        is_initial_line,                    # <Unused argument> pylint: disable = W0613
    ):
        tokens = line.leaves

        assignment_index = self._GetRootTokenIndex(tokens, "=")
        if assignment_index is None:
            return None

        token = tokens[assignment_index]

        parent = token.parent
        while parent:
            if parent.type in black.VARARGS_PARENTS or parent.type in [python_symbols.parameters # <invalid member> pylint: disable = E1101
            ]:
                return None

            if parent.type == python_symbols.classdef:  # <invalid member> pylint: disable = E1101
                return token if self._alignment_flags & self.Flag.ClassLevel else None

            if parent.type == python_symbols.funcdef:   # <invalid member> pylint: disable = E1101
                # This code will be hit on the first token of a line
                # that is a function def. Look at the function definition's
                # name to determine what kind of method it is.
                assert len(parent.children) > 2, parent.children
                if parent.children[1].value == "__init__":
                    if self._alignment_flags & self.Flag.InitAnyLevel:
                        return token

                    if (
                        self._alignment_flags & self.Flag.InitLevel
                        and len(tokens) > 2
                        and tokens[0].value == "self"
                        and tokens[1].value == "."
                    ):
                        return token

                    return None

                else:
                    return token if self._alignment_flags & self.Flag.MethodLevel else None

            parent = parent.parent

        return token if self._alignment_flags & self.Flag.ModuleLevel else None
