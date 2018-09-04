# ----------------------------------------------------------------------
# |  
# |  Visitor.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 22:34:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains types that are helpful when applying the visitor pattern to Fundamental TypeInfo types."""

import os
import sys

from CommonEnvironment.Interface import Interface, \
                                        abstractmethod, \
                                        staticderived, \
                                        override

from CommonEnvironment.TypeInfo.FundamentalTypes.All import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Visitor(Interface):

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnBool(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnDateTime(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnDate(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnDirectory(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnDuration(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnEnum(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnFilename(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnFloat(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnGuid(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnInt(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnString(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnTime(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def OnUri(type_info, *args, **kwargs):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    def Accept(cls, type_info, *args, **kwargs):
        """Calls the appropriate On___ method based on the type_info's type."""

        lookup = { BoolTypeInfo             : cls.OnBool,
                   DateTimeTypeInfo         : cls.OnDateTime,
                   DateTypeInfo             : cls.OnDate,
                   DirectoryTypeInfo        : cls.OnDirectory,
                   DurationTypeInfo         : cls.OnDuration,
                   EnumTypeInfo             : cls.OnEnum,
                   FilenameTypeInfo         : cls.OnFilename,
                   FloatTypeInfo            : cls.OnFloat,
                   GuidTypeInfo             : cls.OnGuid,
                   IntTypeInfo              : cls.OnInt,
                   StringTypeInfo           : cls.OnString,
                   TimeTypeInfo             : cls.OnTime,
                   UriTypeInfo              : cls.OnUri,
                 }

        typ = type(type_info)

        if typ not in lookup:
            raise Exception("'{}' was not expected".format(typ))

        return lookup[typ](type_info, *args, **kwargs)

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def CreateSimpleVisitor( on_bool_func=None,             # def Func(type_info, *args, **kwargs)
                         on_date_time_func=None,        # def Func(type_info, *args, **kwargs)
                         on_date_func=None,             # def Func(type_info, *args, **kwargs)
                         on_directory_func=None,        # def Func(type_info, *args, **kwargs)
                         on_duration_func=None,         # def Func(type_info, *args, **kwargs)
                         on_enum_func=None,             # def Func(type_info, *args, **kwargs)
                         on_filename_func=None,         # def Func(type_info, *args, **kwargs)
                         on_float_func=None,            # def Func(type_info, *args, **kwargs)
                         on_guid_func=None,             # def Func(type_info, *args, **kwargs)
                         on_int_func=None,              # def Func(type_info, *args, **kwargs)
                         on_string_func=None,           # def Func(type_info, *args, **kwargs)
                         on_time_func=None,             # def Func(type_info, *args, **kwargs)
                         on_uri_func=None,              # def Func(type_info, *args, **kwargs)
                         on_default_func=None,          # def Func(type_info, *args, **kwargs)
                       ):
    """Creates a Visitor instance implemented in terms of the non-None function arguments."""

    on_default_func = on_default_func or (lambda type_info, *args, **kwargs: None)

    on_bool_func = on_bool_func or on_default_func
    on_date_time_func = on_date_time_func or on_default_func
    on_date_func = on_date_func or on_default_func
    on_directory_func = on_directory_func or on_default_func
    on_duration_func = on_duration_func or on_default_func
    on_enum_func = on_enum_func or on_default_func
    on_filename_func = on_filename_func or on_default_func
    on_float_func = on_float_func or on_default_func
    on_guid_func = on_guid_func or on_default_func
    on_int_func = on_int_func or on_default_func
    on_string_func = on_string_func or on_default_func
    on_time_func = on_time_func or on_default_func
    on_uri_func = on_uri_func or on_default_func

    # ----------------------------------------------------------------------
    @staticderived
    class SimpleVisitor(Visitor):
        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnBool(type_info, *args, **kwargs):
            return on_bool_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnDateTime(type_info, *args, **kwargs):
            return on_date_time_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnDate(type_info, *args, **kwargs):
            return on_date_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnDirectory(type_info, *args, **kwargs):
            return on_directory_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnDuration(type_info, *args, **kwargs):
            return on_duration_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnEnum(type_info, *args, **kwargs):
            return on_enum_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnFilename(type_info, *args, **kwargs):
            return on_filename_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnFloat(type_info, *args, **kwargs):
            return on_float_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnGuid(type_info, *args, **kwargs):
            return on_guid_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnInt(type_info, *args, **kwargs):
            return on_int_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnString(type_info, *args, **kwargs):
            return on_string_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnTime(type_info, *args, **kwargs):
            return on_time_func(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnUri(type_info, *args, **kwargs):
            return on_uri_func(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------

    return SimpleVisitor
