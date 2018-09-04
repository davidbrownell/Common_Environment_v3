# ----------------------------------------------------------------------
# |  
# |  BoolTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 22:27:58
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the BoolTypeInfo object"""

import os
import sys

from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@staticderived
class BoolTypeInfo(TypeInfo):
    """Type information for a boolean value"""

    Desc                                    = DerivedProperty("Boolean")
    ConstraintsDesc                         = DerivedProperty('')
    ExpectedType                            = bool

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _ValidateItemNoThrowImpl(item):
        return
