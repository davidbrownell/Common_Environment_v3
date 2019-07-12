# ----------------------------------------------------------------------
# |
# |  DecoratorWhitespacePlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-07-01 17:47:55
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

from PythonFormatterImpl.Plugin import PluginBase       # <Unable to import> pylint: disable = E0401

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(PluginBase):
    """Removes whitespace introduced by black between function decorators and functions"""

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("DecoratorWhitespace")
    Priority                                = Interface.DerivedProperty(PluginBase.STANDARD_PRIORITY)

    # ----------------------------------------------------------------------
    # |  Methods
    @staticmethod
    @Interface.override
    def DecorateLines(lines):
        # ----------------------------------------------------------------------
        def IsDecorator(token):
            return token is not None and token.type == python_symbols.decorator # <no member> pylint: disable = E1101

        # ----------------------------------------------------------------------
        def IsFuncOrDecorator(token):
            return IsDecorator(token) or (
                token is not None and token.type == python_symbols.funcdef  # <no member> pylint: disable = E1101
            )

        # ----------------------------------------------------------------------
        def IsPrevLineADecorator(line_index):
            return (
                line_index != 0
                and lines[line_index].leaves
                and IsFuncOrDecorator(lines[line_index].leaves[0].parent)
                and lines[line_index - 1].leaves
                and IsDecorator(lines[line_index - 1].leaves[-1].parent)
            )

        # ----------------------------------------------------------------------

        for line_index in range(len(lines)):
            if IsPrevLineADecorator(line_index):
                lines[line_index].leaves[0].prefix = ""

        return lines
