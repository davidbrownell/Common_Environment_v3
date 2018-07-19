# ----------------------------------------------------------------------
# |  
# |  PythonCodeVisitor.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-15 13:55:00
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the PythonCodeSerialization object"""

import os
import sys

from CommonEnvironment.Interface import staticderived, override

from CommonEnvironment.TypeInfo.FundamentalTypes.Visitor import Visitor

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Parameters differ from overridden '<...>' method> pylint: disable = W0221

# ----------------------------------------------------------------------
@staticderived
class PythonCodeVisitor(Visitor):
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnBool(cls, type_info):
        return "BoolTypeInfo({})".format(cls._ArityString(type_info.Arity))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnDateTime(cls, type_info):
        return "DateTimeTypeInfo({})".format(cls._ArityString(type_info.Arity))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnDate(cls, type_info):
        return "DateTypeInfo({})".format(cls._ArityString(type_info.Arity))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnDirectory(cls, type_info):
        args = []

        if not type_info.EnsureExists:
            args.append("ensure_exists=False")

        if type_info.ValidationExpression:
            args.append("validation_expression='{}'".format(type_info.ValidationExpression))

        args.append(cls._ArityString(type_info.Arity))

        return "DirectoryTypeInfo({})".format(', '.join([ arg for arg in args if arg ]))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnDuration(cls, type_info):
        return "DurationTypeInfo({})".format(cls._ArityString(type_info.Arity))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnEnum(cls, type_info):
        # ----------------------------------------------------------------------
        def ToList(values):
            return "[ {}]".format(''.join([ "'{}', ".format(value) for value in values ]))
        
        # ----------------------------------------------------------------------

        args = [ ToList(type_info.Values), ]

        if type_info.FriendlyValues:
            args.append(ToList(type_info.FriendlyValues))

        args.append(cls._ArityString(type_info.Arity))

        return "EnumTypeInfo({})".format(', '.join([ arg for arg in args if arg ]))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnFilename(cls, type_info):
        args = []

        if not type_info.EnsureExists:
            args.append("ensure_exists=False")

        if type_info.MatchAny:
            args.append("match_any=True")

        if type_info.ValidationExpression:
            args.append("validation_expression='{}'".format(type_info.ValidationExpression))

        args.append(cls._ArityString(type_info.Arity))

        return "FilenameTypeInfo({})".format(', '.join([ arg for arg in args if arg ]))
        
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnFloat(cls, type_info):
        args = []

        if type_info.Min is not None:
            args.append("min={}".format(type_info.Min))

        if type_info.Max is not None:
            args.append("max={}".format(type_info.Max))

        args.append(cls._ArityString(type_info.Arity))

        return "FloatTypeInfo({})".format(', '.join([ arg for arg in args if arg ]))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnGuid(cls, type_info):
        return "GuidTypeInfo({})".format(cls._ArityString(type_info.Arity))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnInt(cls, type_info):
        args = []

        if type_info.Min is not None:
            args.append("min={}".format(type_info.Min))

        if type_info.Max is not None:
            args.append("max={}".format(type_info.Max))

        if type_info.Bytes is not None:
            args.append("bytes={}".format(type_info.Bytes))

        args.append(cls._ArityString(type_info.Arity))

        return "IntTypeInfo({})".format(', '.join([ arg for arg in args if arg ]))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnString(cls, type_info):
        args = []

        if type_info.ValidationExpression is not None:
            args.append("validation_expression='{}'".format(type_info.ValidationExpression))

        if type_info.MinLength is not None:
            args.append("min_length={}".format(type_info.MinLength))

        if type_info.MaxLength is not None:
            args.append("max_length={}".format(type_info.MaxLength))

        args.append(cls._ArityString(type_info.Arity))

        return "StringTypeInfo({})".format(', '.join([ arg for arg in args if arg ]))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnTime(cls, type_info):
        return "TimeTypeInfo({})".format(cls._ArityString(type_info.Arity))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnUri(cls, type_info):
        return "UriTypeInfo({})".format(cls._ArityString(type_info.Arity))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _ArityString(arity):
        if arity.IsOptional:
            return "arity=Arity.FromString('?')"
        
        if arity.IsOneOrMore:
            return "arity=Arity.FromString('+')"
        
        if arity.IsZeroOrMore:
            return "arity=Arity.FromString('*')"
        
        if arity.Min == arity.Max == 1:
            return ''
        
        return "arity=Arity({},{})".format( arity.Min,
                                            arity.Max or "None",
                                          )
