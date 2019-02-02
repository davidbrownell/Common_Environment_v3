# ----------------------------------------------------------------------
# |  
# |  PythonCodeVisitor.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-15 13:55:00
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the PythonCodeSerialization object"""

import os

import six

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override

from CommonEnvironment.TypeInfo.Visitor import Visitor

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Parameters differ from overridden '<...>' method> pylint: disable = W0221

# ----------------------------------------------------------------------
@staticderived
class PythonCodeVisitor(Visitor):
    # ----------------------------------------------------------------------
    @staticmethod
    def LoadTypeInfo(*args, **kwargs):
        # Convenience method for code below
        return LoadTypeInfo(*args, **kwargs)

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
    @classmethod
    @override
    def OnAnyOf(cls, type_info, element_type_infos_code=None):
        if element_type_infos_code is None:
            element_type_infos_code = [ None, ] * len(type_info.ElementTypeInfos)
        else:
            assert len(element_type_infos_code) == len(type_info.ElementTypeInfos)

        for index, eti in enumerate(type_info.ElementTypeInfos):
            if element_type_infos_code[index] is None:
                element_type_infos_code[index] = cls.Accept(eti)

        args = [ '[ {} ]'.format(', '.join(element_type_infos_code)),
                 cls._ArityString(type_info.Arity),
               ]

        return "AnyOfTypeInfo({})".format( ', '.join([ arg for arg in args if arg ]))

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnClass(cls, type_info):
        return cls._OnDictLikeImpl(type_info)
        
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnMethod(cls, type_info):
        return "MethodTypeInfo({})".format(cls._ArityString(type_info.Arity))
        
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnClassMethod(cls, type_info):
        return "ClassMethodTypeInfo({})".format(cls._ArityString(type_info.Arity))
        
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnStaticMethod(cls, type_info):
        return "StaticMethodTypeInfo({})".format(cls._ArityString(type_info.Arity))
        
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnDict(cls, type_info):
        return cls._OnDictLikeImpl(type_info)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnGeneric(cls, type_info):
        return "GenericTypeInfo({})".format(cls._ArityString(type_info.Arity))
        
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnList(cls, type_info, element_type_info_code=None):
        if element_type_info_code is None:
            element_type_info_code = cls.Accept(type_info.ElementTypeInfo)

        args = [ element_type_info_code,
                 cls._ArityString(type_info.Arity),
               ]

        return "ListTypeInfo({})".format(', '.join([ arg for arg in args if arg ]))
        
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

    # ----------------------------------------------------------------------
    @classmethod
    def _OnDictLikeImpl(cls, type_info):
        # Dict-like structures may be recursive, which complicates how we persist and create the items.
        # This code will enumerate through the type and create the child if it hasn't been seen yet or 
        # has been seen and is complete. If it has been seen but is not yet complete (this is the recursive
        # scenario), we create a bread crumb that can be used to assemble the complete type at runtime.
        from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo

        type_infos = {}
        nonlocals = CommonEnvironment.Nonlocals( recursive=False,
                                               )

        # ----------------------------------------------------------------------
        def Impl(ti):
            lookup_key = id(ti)
            
            if lookup_key in type_infos:
                index, content = type_infos[lookup_key]

                nonlocals.recursive = True
                return str(index)

            type_infos[lookup_key] = [ len(type_infos), None, ]

            if isinstance(ti, DictTypeInfo):
                values = []

                for k, v in six.iteritems(ti.Items):
                    if k is None:
                        k = "None"
                    else:
                        k = '"{}"'.format(k)

                    values.append('( {}, {} )'.format(k, Impl(v)))

                args = [ "OrderedDict([ {} ])".format(', '.join(values)),
                       ]

                if ti.RequireExactMatchDefault is not None:
                    args.append("require_exact_match={}".format(ti.RequireExactMatchDefault))

                args.append(cls._ArityString(ti.Arity))

                content = "{}({})".format( type(ti).__name__,
                                           ', '.join([ arg for arg in args if arg ]),
                                         )
            else:
                kwargs = {}

                if hasattr(ti, "ElementTypeInfo"):
                    eti_lookup_key = id(ti.ElementTypeInfo)

                    existing_type_info = type_infos.get(eti_lookup_key, None)
                    if existing_type_info is not None:
                        nonlocals.recursive = True
                        kwargs["element_type_info_code"] = str(existing_type_info[0])

                elif hasattr(ti, "ElementTypeInfos"):
                    element_type_infos_code = []
                    found_one = False

                    for eti in ti.ElementTypeInfos:
                        eti_lookup_key = id(eti)

                        existing_type_info = type_infos.get(eti_lookup_key, None)
                        if existing_type_info is not None:
                            found_one = True
                            existing_type_info = str(existing_type_info[0])

                        element_type_infos_code.append(existing_type_info)

                    if found_one:
                        nonlocals.recursive = True
                        kwargs["element_type_infos_code"] = element_type_infos_code
            
                content = cls.Accept(ti, **kwargs)

            type_infos[lookup_key][1] = content 
            return type_infos[lookup_key][1]

        # ----------------------------------------------------------------------

        content = Impl(type_info)

        if nonlocals.recursive:
            return "PythonCodeVisitor.LoadTypeInfo({})".format(content)

        return content

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def LoadTypeInfo(type_info):
    from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo

    type_infos = []

    # ----------------------------------------------------------------------
    def Impl(ti):
        type_infos.append(ti)

        if isinstance(ti, DictTypeInfo):
            for k, v in six.iteritems(ti.Items):
                if isinstance(v, int):
                    assert v < len(type_infos), (k, v, len(type_infos))
                    ti.Items[k] = type_infos[v]
                else:
                    Impl(v)
        
        elif hasattr(ti, "ElementTypeInfo"):
            if isinstance(ti.ElementTypeInfo, int):
                ti.ElementTypeInfo = type_infos[ti.ElementTypeInfo]
        
        elif hasattr(ti, "ElementTypeInfos"):
            for eti_index, eti in enumerate(ti.ElementTypeInfos):
                if isinstance(eti, int):
                    ti.ElementTypeInfos[eti_index] = type_infos[eti]

    # ----------------------------------------------------------------------

    Impl(type_info)

    return type_info
