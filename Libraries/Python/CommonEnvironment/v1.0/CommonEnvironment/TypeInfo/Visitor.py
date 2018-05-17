# ----------------------------------------------------------------------
# |  
# |  Visitor.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 21:28:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Visitor object"""

import os
import sys

from CommonEnvironment.Interface import *
from CommonEnvironment.TypeInfo.All import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Visitor import Visitor as FundamentalVisitor, \
                                                                CreateSimpleVisitor as FundamentalCreateSimpleVisitor

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Visitor(FundamentalVisitor):

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnAnyOf(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnClass(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnMethod(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnClassMethod(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnStaticMethod(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnDict(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnList(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    def Accept(cls, type_info, *args, **kwargs):
        """Calls the appropriate On___ method based on the type_info's type."""

        lookup = { AnyOfTypeInfo            : cls.OnAnyOf,
                   ClassTypeInfo            : cls.OnClass,
                   MethodTypeInfo           : cls.OnMethod,
                   ClassMethodTypeInfo      : cls.OnClassMethod,
                   StaticMethodTypeInfo     : cls.OnStaticMethod,
                   DictTypeInfo             : cls.OnDict,
                   ListTypeInfo             : cls.OnList,
                 }

        typ = type(type_info)

        if typ in lookup:
            return lookup[typ](type_info, *args, **kwargs)

        return super(Visitor, cls).Accept(type_info, *args, **kwargs)

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def CreateSimpleVisitor( onAnyOfFunc=None,              # def Func(type_info, *args, **kwargs)
                         onClassFunc=None,              # def Func(type_info, *args, **kwargs)
                         onMethodFunc=None,             # def Func(type_info, *args, **kwargs)
                         onClassMethodFunc=None,        # def Func(type_info, *args, **kwargs)
                         onStaticMethodFunc=None,       # def Func(type_info, *args, **kwargs)
                         onDictFunc=None,               # def Func(type_info, *args, **kwargs)
                         onListFunc=None,               # def Func(type_info, *args, **kwargs)

                         onDefaultFunc=None,            # def Func(type_info, *args, **kwargs)

                         **fundamental_funcs
                       ):
    """Creates a Visitor instance implemented in terms of the non-None function arguments."""

    onDefaultFunc = onDefaultFunc or (lambda type_info, *args, **kwargs: None)

    onAnyOfFunc = onAnyOfFunc or onDefaultFunc
    onClassFunc = onClassFunc or onDefaultFunc
    onMethodFunc = onMethodFunc or onDefaultFunc
    onClassMethodFunc = onClassMethodFunc or onDefaultFunc
    onStaticMethodFunc = onStaticMethodFunc or onDefaultFunc
    onDictFunc = onDictFunc or onDefaultFunc
    onListFunc = onListFunc or onDefaultFunc

    # ----------------------------------------------------------------------
    @staticderived
    class SimpleVisitor( Visitor, 
                         FundamentalCreateSimpleVisitor( onDefaultFunc=onDefaultFunc,
                                                         **fundamental_funcs
                                                       ),
                       ):
        # ----------------------------------------------------------------------
        @staticmethod
        def OnAnyOf(type_info, *args, **kwargs):
            return onAnyOfFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnClass(type_info, *args, **kwargs):
            return onClassFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnMethod(type_info, *args, **kwargs):
            return onMethodFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnClassMethod(type_info, *args, **kwargs):
            return onClassMethodFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnStaticMethod(type_info, *args, **kwargs):
            return onStaticMethodFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDict(type_info, *args, **kwargs):
            return onDictFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnList(type_info, *args, **kwargs):
            return onListFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------

    return SimpleVisitor
