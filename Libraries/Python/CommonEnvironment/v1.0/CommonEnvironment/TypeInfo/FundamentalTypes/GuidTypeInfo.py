# ----------------------------------------------------------------------
# |  
# |  GuidTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 00:32:33
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the GuidTypeInfo object."""

import os
import sys
import uuid

from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@staticderived
class GuidTypeInfo(TypeInfo):
    """Type info for a guid value."""

    Desc                                    = DerivedProperty("Guid")
    ConstraintsDesc                         = DerivedProperty('')
    ExpectedType                            = uuid.UUID

    # ----------------------------------------------------------------------
    @staticmethod
    def Create():
        return uuid.uuid4()

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _ValidateItemNoThrowImpl(item):
        return
