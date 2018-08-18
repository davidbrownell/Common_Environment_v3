# ----------------------------------------------------------------------
# |  
# |  DateTimeTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 22:45:34
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the DateTimeTypeInfo object."""

import datetime
import os
import sys

from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@staticderived
class DateTimeTypeInfo(TypeInfo):
    """Type information for a datetime value."""

    Desc                                    = DerivedProperty("Datetime")
    ConstraintsDesc                         = DerivedProperty('')
    ExpectedType                            = datetime.datetime

    # ----------------------------------------------------------------------
    @staticmethod
    def Create(microseconds=True):
        result = datetime.datetime.now()

        if not microseconds:
            result = result.replace(microsecond=0)

        return result

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _ValidateItemNoThrowImpl(item):
        return
    