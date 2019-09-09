# ----------------------------------------------------------------------
# |
# |  FunctionDefSplitterPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-29 09:49:26
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
from CommonEnvironment import Interface

from PythonFormatterImpl.Impl.BlackImports import python_symbols               # <Unable to import> pylint: disable = E0401
from PythonFormatterImpl.Impl.FunctionSplitterImpl import FunctionSplitterImpl # <Unable import> pylint: disable = E0401
from PythonFormatterImpl.Impl.SplitterImpl import SimpleInitialTokenMixin      # <Unable import> pylint: disable = E0401

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(SimpleInitialTokenMixin, FunctionSplitterImpl):
    """Splits function definitions that contain more than N args or have keyword arguments"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("FunctionDefSplitter")

    # ----------------------------------------------------------------------
    # |  Private Properties
    _InitialTokenType                       = Interface.DerivedProperty(python_symbols.typedargslist) # <No member> pylint: disable = E1101
