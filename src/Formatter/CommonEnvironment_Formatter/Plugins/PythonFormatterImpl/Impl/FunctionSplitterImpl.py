# ----------------------------------------------------------------------
# |
# |  FunctionSplitterImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-29 09:45:40
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the FunctionSplitterImpl object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

from PythonFormatterImpl.Impl.SplitterImpl import SplitterImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class FunctionSplitterImpl(SplitterImpl):
    """Helps when implementing function-based splitters"""

    # ----------------------------------------------------------------------
    # |  Properties
    Priority                                = Interface.DerivedProperty(SplitterImpl.STANDARD_PRIORITY * 2)

    # ----------------------------------------------------------------------
    # |  Private Properties
    _DefaultSplitArgsValue                  = Interface.DerivedProperty(10)

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @Interface.override
    def _ShouldSplitBasedOnArgs(args):
        for arg in args:
            if arg.value == "=":
                return True

        return False

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def _InsertTrailingComma(args):
        for arg in args:
            if arg.value.startswith("*"):
                return False

        return True
