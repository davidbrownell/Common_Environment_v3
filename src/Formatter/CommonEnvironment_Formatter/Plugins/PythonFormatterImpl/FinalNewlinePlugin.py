# ----------------------------------------------------------------------
# |
# |  FinalNewlinePlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-30 14:31:09
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

from PythonFormatterImpl.Plugin import PluginBase       # <Unable to import> pylint: disable = E0401

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(PluginBase):
    """Removes the final newline from the file"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("FinalNewline")
    Priority                                = Interface.DerivedProperty(9999999999999999999)

    # ----------------------------------------------------------------------
    # |  Methods
    @staticmethod
    @Interface.override
    def PostprocessLines(lines):
        if lines and not lines[-1].leaves:
            lines = lines[:-1]

        return lines
