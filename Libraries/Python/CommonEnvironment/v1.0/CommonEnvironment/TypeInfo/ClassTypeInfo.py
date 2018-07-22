# ----------------------------------------------------------------------
# |  
# |  ClassTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 20:18:38
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the MethodTypeInfo, ClassMethodTypeInfo, StateMethodTypeInfo, and ClassTypeInfo objects"""

import os
import sys

from CommonEnvironment import Interface

from CommonEnvironment.TypeInfo import TypeInfo
from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class _MethodTypeInfo(TypeInfo):
    ConstraintsDesc                         = Interface.DerivedProperty('')
    ExpectedTypeIsCallable                  = True

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def _ValidateItemNoThrowImpl(item):
        return

# ----------------------------------------------------------------------
@Interface.staticderived
class MethodTypeInfo(_MethodTypeInfo):
    Desc                                    = Interface.DerivedProperty("Method")
    ExpectedType                            = staticmethod(Interface.IsStandardMethod)

# ----------------------------------------------------------------------
@Interface.staticderived
class ClassMethodTypeInfo(_MethodTypeInfo):
    Desc                                    = Interface.DerivedProperty("Class Method")
    ExpectedType                            = staticmethod(Interface.IsClassMethod)

# ----------------------------------------------------------------------
@Interface.staticderived
class StaticMethodTypeInfo(_MethodTypeInfo):
    Desc                                    = Interface.DerivedProperty("Static Method")
    ExpectedType                            = staticmethod(Interface.IsStaticMethod)

# ----------------------------------------------------------------------
class ClassTypeInfo(DictTypeInfo):
    """Type that validates a class object."""

    Desc                                    = Interface.DerivedProperty("Class")
    ExpectedTypeIsCallable                  = True
    ExpectedType                            = staticmethod(lambda item: True) # Everything is an object

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def _GetAttributes(item):
        return dir(item)

    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.override
    def _GetAttributeValue(item, name, type_info):
        if isinstance(type_info, _MethodTypeInfo):
            item = type(item)

        return getattr(item, name)
