# ----------------------------------------------------------------------
# |  
# |  GenericTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-10-14 14:55:43
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the GenericTypeInfo object"""

import os

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@staticderived
class GenericTypeInfo(TypeInfo):
    """Type information that can apply to any type"""

    Desc                                    = DerivedProperty("Generic")
    ConstraintsDesc                         = DerivedProperty('')
    ExpectedType                            = staticmethod(lambda item: True)
    ExpectedTypeIsCallable                  = True

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _ValidateItemNoThrowImpl(item):
        return
