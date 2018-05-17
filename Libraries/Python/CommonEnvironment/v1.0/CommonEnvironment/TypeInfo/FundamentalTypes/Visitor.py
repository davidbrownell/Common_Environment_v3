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

from CommonEnvironment.Interface import *
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
def CreateSimpleVisitor( onBoolFunc=None,               # def Func(type_info, *args, **kwargs)
                         onDateTimeFunc=None,           # def Func(type_info, *args, **kwargs)
                         onDateFunc=None,               # def Func(type_info, *args, **kwargs)
                         onDirectoryFunc=None,          # def Func(type_info, *args, **kwargs)
                         onDurationFunc=None,           # def Func(type_info, *args, **kwargs)
                         onEnumFunc=None,               # def Func(type_info, *args, **kwargs)
                         onFilenameFunc=None,           # def Func(type_info, *args, **kwargs)
                         onFloatFunc=None,              # def Func(type_info, *args, **kwargs)
                         onGuidFunc=None,               # def Func(type_info, *args, **kwargs)
                         onIntFunc=None,                # def Func(type_info, *args, **kwargs)
                         onStringFunc=None,             # def Func(type_info, *args, **kwargs)
                         onTimeFunc=None,               # def Func(type_info, *args, **kwargs)
                         onUriFunc=None,                # def Func(type_info, *args, **kwargs)
                         onDefaultFunc=None,            # def Func(type_info, *args, **kwargs)
                       ):
    """Creates a Visitor instance implemented in terms of the non-None function arguments."""

    onDefaultFunc = onDefaultFunc or (lambda type_info, *args, **kwargs: None)

    onBoolFunc = onBoolFunc or onDefaultFunc
    onDateTimeFunc = onDateTimeFunc or onDefaultFunc
    onDateFunc = onDateFunc or onDefaultFunc
    onDirectoryFunc = onDirectoryFunc or onDefaultFunc
    onDurationFunc = onDurationFunc or onDefaultFunc
    onEnumFunc = onEnumFunc or onDefaultFunc
    onFilenameFunc = onFilenameFunc or onDefaultFunc
    onFloatFunc = onFloatFunc or onDefaultFunc
    onGuidFunc = onGuidFunc or onDefaultFunc
    onIntFunc = onIntFunc or onDefaultFunc
    onStringFunc = onStringFunc or onDefaultFunc
    onTimeFunc = onTimeFunc or onDefaultFunc
    onUriFunc = onUriFunc or onDefaultFunc

    # ----------------------------------------------------------------------
    @staticderived
    class SimpleVisitor(Visitor):
        # ----------------------------------------------------------------------
        @staticmethod
        def OnBool(type_info, *args, **kwargs):
            return onBoolFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDateTime(type_info, *args, **kwargs):
            return onDateTimeFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDate(type_info, *args, **kwargs):
            return onDateFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDirectory(type_info, *args, **kwargs):
            return onDirectoryFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnDuration(type_info, *args, **kwargs):
            return onDurationFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnEnum(type_info, *args, **kwargs):
            return onEnumFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnFilename(type_info, *args, **kwargs):
            return onFilenameFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnFloat(type_info, *args, **kwargs):
            return onFloatFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnGuid(type_info, *args, **kwargs):
            return onGuidFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnInt(type_info, *args, **kwargs):
            return onIntFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnString(type_info, *args, **kwargs):
            return onStringFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnTime(type_info, *args, **kwargs):
            return onTimeFunc(type_info, *args, **kwargs)

        # ----------------------------------------------------------------------
        @staticmethod
        def OnUri(type_info, *args, **kwargs):
            return onUriFunc(type_info, *args, **kwargs)

    # ----------------------------------------------------------------------

    return SimpleVisitor
