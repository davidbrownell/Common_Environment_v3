# ----------------------------------------------------------------------
# |  
# |  FloatTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 00:13:06
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the FloatTypeInfo object."""

import os
import sys

from CommonEnvironment.Interface import override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class FloatTypeInfo(TypeInfo):
    """Type info for a float value."""

    Desc                                    = DerivedProperty("Float")
    ExpectedType                            = (float, int)

    # ----------------------------------------------------------------------
    def __init__( self,
                  min=None,
                  max=None,
                  **type_info_args
                ):
        super(FloatTypeInfo, self).__init__(**type_info_args)

        if min is not None and max is not None and max < min:
            raise Exception("Invalid argument - 'max'")

        self.Min                            = float(min) if min is not None else None
        self.Max                            = float(max) if max is not None else None

    # ----------------------------------------------------------------------
    @property
    @override
    def ConstraintsDesc(self):
        constraints = []

        if self.Min is not None:
            constraints.append(">= {}".format(self.Min))

        if self.Max is not None:
            constraints.append("<= {}".format(self.Max))

        if not constraints:
            return ''

        return "Value must be {}".format(', '.join(constraints))

    # ----------------------------------------------------------------------
    @override
    def _ValidateItemNoThrowImpl(self, item, **custom_args):
        if self.Min is not None and item < self.Min:
            return "{} is not >= {}".format(item, self.Min)

        if self.Max is not None and item > self.Max:
            return "{} is not <= {}".format(item, self.Max)

        return None
        