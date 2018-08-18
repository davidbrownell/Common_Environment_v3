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

from CommonEnvironment.Interface import abstractmethod, \
                                        staticderived, \
                                        override

# <Unused import> pylint: disable = W0614

from CommonEnvironment.TypeInfo.All import *            # <Wildcard import> pylint: disable = W0401
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
def CreateSimpleVisitor( on_any_of_func=None,           # def Func(type_info, *args, **kwargs)
                         on_class_func=None,            # def Func(type_info, *args, **kwargs)
                         on_method_func=None,           # def Func(type_info, *args, **kwargs)
                         on_class_method_func=None,     # def Func(type_info, *args, **kwargs)
                         on_static_method_func=None,    # def Func(type_info, *args, **kwargs)
                         on_dict_func=None,             # def Func(type_info, *args, **kwargs)
                         on_list_func=None,             # def Func(type_info, *args, **kwargs)

                         on_default_func=None,          # def Func(type_info, *args, **kwargs)

                         **fundamental_funcs
                       ):
    """Creates a Visitor instance implemented in terms of the non-None function arguments."""

    on_default_func = on_default_func or (lambda type_info, *args, **kwargs: None)

    on_any_of_func = on_any_of_func or on_default_func
    on_class_func = on_class_func or on_default_func
    on_method_func = on_method_func or on_default_func
    on_class_method_func = on_class_method_func or on_default_func
    on_static_method_func = on_static_method_func or on_default_func
    on_dict_func = on_dict_func or on_default_func
    on_list_func = on_list_func or on_default_func

    # ----------------------------------------------------------------------
    @staticderived
    class SimpleVisitor( Visitor, 
                         FundamentalCreateSimpleVisitor( on_default_func=on_default_func,
                                                         **fundamental_funcs
                                                       ),
                       ):
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnAnyOf(type_info, *args, **kwargs):
            return on_any_of_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnClass(type_info, *args, **kwargs):
            return on_class_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnMethod(type_info, *args, **kwargs):
            return on_method_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnClassMethod(type_info, *args, **kwargs):
            return on_class_method_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnStaticMethod(type_info, *args, **kwargs):
            return on_static_method_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnDict(type_info, *args, **kwargs):
            return on_dict_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnList(type_info, *args, **kwargs):
            return on_list_func(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------

    return SimpleVisitor
