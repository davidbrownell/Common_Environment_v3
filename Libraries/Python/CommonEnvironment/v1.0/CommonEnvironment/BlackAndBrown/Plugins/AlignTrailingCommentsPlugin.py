# ----------------------------------------------------------------------
# |
# |  AlignTrailingCommentsPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-12-17 17:38:39
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

from CommonEnvironment.BlackAndBrown.Plugins.Impl.HorizontalAlignmentPluginImpl import HorizontalAlignmentPluginImpl

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(HorizontalAlignmentPluginImpl):
    Name                                    = Interface.DerivedProperty("AlignTrailingComments")
    Priority                                = Interface.DerivedProperty(HorizontalAlignmentPluginImpl.STANDARD_PRIORITY)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def _GetAlignmentLeaf(line, is_initial_line):
        if line.comments:
            assert len(line.comments) == 1
            assert isinstance(line.comments[0], tuple), line.comments[0]

            return line.comments[0][1]

        for index, leaf in enumerate(line.leaves):
            if getattr(leaf, "value", '').startswith('#') and \
               (not is_initial_line or index != 0):
                return leaf

        return None
