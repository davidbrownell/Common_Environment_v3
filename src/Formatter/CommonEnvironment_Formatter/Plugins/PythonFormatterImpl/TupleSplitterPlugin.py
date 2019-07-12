# ----------------------------------------------------------------------
# |
# |  TupleSplitterPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-29 09:23:16
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

from blib2to3.pygram import python_symbols

import CommonEnvironment
from CommonEnvironment import Interface

from PythonFormatterImpl.Impl.SplitterImpl import SplitterImpl, SimpleInitialTokenMixin # <Unable to import> pylint: disable = E0401

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(SimpleInitialTokenMixin, SplitterImpl):
    """Splits tuples that contain more than N args"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("TupleSplitter")

    # ----------------------------------------------------------------------
    # |  Private Properties
    _DefaultSplitArgsValue                  = Interface.DerivedProperty(3)
    _InitialTokenType                       = Interface.DerivedProperty(python_symbols.testlist_gexp) # <No member> pylint: disable = E1101

    # ----------------------------------------------------------------------
    # |  Private Methods
    @Interface.override
    @staticmethod
    def _InsertTrailingComma(
        args,                               # <Unused argument> pylint: disable = W0613
    ):
        return True
