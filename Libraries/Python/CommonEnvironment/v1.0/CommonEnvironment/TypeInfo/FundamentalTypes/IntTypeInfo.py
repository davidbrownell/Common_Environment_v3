# ----------------------------------------------------------------------
# |  
# |  IntTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 09:03:08
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the IntTypeInfo object."""

import math
import os
import sys

from CommonEnvironment.Interface import override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class IntTypeInfo(TypeInfo):
    """Type info for an integer value."""

    Desc                                    = DerivedProperty("Integer")
    ExpectedType                            = int

    # ----------------------------------------------------------------------
    def __init__( self,
                  min=None,
                  max=None,
                  bytes=None,
                  unsigned=False,
                  **type_info_args
                ):
        super(IntTypeInfo, self).__init__(**type_info_args)

        if min is not None and max is not None and max < min:
            raise Exception("Invalid argument - 'max'")

        if unsigned:
            if min is None:
                min = 0
            elif min < 0:
                raise Exception("Invalid argument - 'min'")

        if bytes is not None:
            if bytes not in [ 1, 2, 4, 8, ]:
                raise Exception("Invalid argument - 'bytes'")

            range = (1 << (bytes * 8)) - 1

            if min is None or max is None:
                if min is None:
                    assert not unsigned
                    min = -int(math.ceil(float(range) / 2))

                if max is None:
                    max = min + range

            if max - min > range:
                raise Exception("Invalid argument - 'min/max'")

        self.Min                            = min
        self.Max                            = max
        self.Bytes                          = bytes
        self.Unsigned                       = min is not None and min >= 0

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
    def _ValidateItemNoThrowImpl(self, item):
        if self.Min is not None and item < self.Min:
            return "{} is not >= {}".format(item, self.Min)

        if self.Max is not None and item > self.Max:
            return "{} is not <= {}".format(item, self.Max)

        return None
        