# ----------------------------------------------------------------------
# |
# |  ListSplitterPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-29 09:01:27
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

from PythonFormatterImpl.Impl.BlackImports import python_symbols                        # <Unable to import> pylint: disable = E0401
from PythonFormatterImpl.Impl.SplitterImpl import SplitterImpl, SimpleInitialTokenMixin # <Unable to import> pylint: disable = E0401

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(SimpleInitialTokenMixin, SplitterImpl):
    """Splits lists that contain more than N args"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("ListSplitter")

    # ----------------------------------------------------------------------
    # |  Private Properties
    _DefaultSplitArgsValue                  = Interface.DerivedProperty(3)
    _InitialTokenType                       = Interface.DerivedProperty(python_symbols.listmaker) # <No member> pylint: disable = E1101

    # ----------------------------------------------------------------------
    # |  Private Methods
    @Interface.override
    @staticmethod
    def _InsertTrailingComma(args):
        for arg in args:
            if arg.parent and arg.parent.type == python_symbols.old_comp_for: # <No member> pylint: disable = E1101
                return False

        return True
