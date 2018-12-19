# ----------------------------------------------------------------------
# |
# |  SplitFunctionsWithDefaultsPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-12-18 15:42:51
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

from CommonEnvironment.BlackAndBrown.Plugins.Impl.FunctionPluginImpl import FunctionPluginImpl

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(FunctionPluginImpl):
    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("SplitFunctionsWithDefaults")
    Priority                                = Interface.DerivedProperty(FunctionPluginImpl.STANDARD_PRIORITY)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def _ShouldSplitFunctionArgs(line):
        for leaf in line.leaves:
            if leaf.value == '=':
                return True

        return False
