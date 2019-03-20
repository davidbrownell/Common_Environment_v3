# ----------------------------------------------------------------------
# |
# |  GroupEmptyParensPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-08 11:40:52
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

from PluginBase import PluginBase

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(PluginBase):
    """Ensures that empty parens are not split across multiple lines"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("GroupEmptyParens")
    Priority                                = Interface.DerivedProperty(PluginBase.STANDARD_PRIORITY)

    # ----------------------------------------------------------------------
    # |  Methods
    @staticmethod
    @Interface.override
    def Decorate(lines):
        # Decoration activities are handled in PostprocessLines
        return lines

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def PostprocessLines(cls, lines):
        new_lines = []

        for index, line in enumerate(lines):
            if (
                index != 0
                and cls.FirstLeafValue(line) == ")"
                and cls.LastLeafValue(new_lines[-1]) == "("
                and (len(line.leaves) == 1 or (len(line.leaves) == 2 and line.leaves[1].value == ","))
            ):
                # Merge the contents of this line with the previous
                # line.
                new_lines[-1].leaves += line.leaves
                continue

            new_lines.append(line)

        return new_lines
