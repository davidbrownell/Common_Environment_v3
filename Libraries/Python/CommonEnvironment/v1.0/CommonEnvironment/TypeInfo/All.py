# ----------------------------------------------------------------------
# |  
# |  All.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 21:22:52
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""All items from this module"""

import os
import sys

from CommonEnvironment.TypeInfo.AnyOfTypeInfo import AnyOfTypeInfo
from CommonEnvironment.TypeInfo.ClassTypeInfo import ClassTypeInfo, MethodTypeInfo, ClassMethodTypeInfo, StaticMethodTypeInfo
from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo
from CommonEnvironment.TypeInfo.ListTypeInfo import ListTypeInfo

# <Unused import> pylint: disable = W0614

from CommonEnvironment.TypeInfo.FundamentalTypes.All import *               # <Wildcard import> pylint: disable = W0401

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
ALL_NON_FUNDAMENTAL_TYPES                   = [ AnyOfTypeInfo,
                                                ClassTypeInfo,
                                                MethodTypeInfo,
                                                ClassMethodTypeInfo,
                                                StaticMethodTypeInfo,
                                                DictTypeInfo,
                                                ListTypeInfo,
                                              ]

ALL_TYPES                                     = ALL_FUNDAMENTAL_TYPES + ALL_NON_FUNDAMENTAL_TYPES
