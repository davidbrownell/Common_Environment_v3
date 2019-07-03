# ----------------------------------------------------------------------
# |
# |  DictSplitterPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-29 09:27:21
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

import black
from blib2to3.pygram import python_symbols

import CommonEnvironment
from CommonEnvironment import Interface

from PythonFormatterImpl.Impl.SplitterImpl import SplitterImpl, SimpleInitialTokenMixin

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(SimpleInitialTokenMixin, SplitterImpl):
    """Splits dictionaries that contain more than N args"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("DictSplitter")

    # ----------------------------------------------------------------------
    # |  Private Properties
    _DefaultSplitArgsValue                  = Interface.DerivedProperty(3)
    _InitialTokenType                       = Interface.DerivedProperty(python_symbols.dictsetmaker)

    # ----------------------------------------------------------------------
    # |  Private Methods
    @Interface.override
    @staticmethod
    def _InsertTrailingComma(args):
        for arg in args:
            if arg.parent and arg.parent.type == python_symbols.comp_for:
                return False

        return True
