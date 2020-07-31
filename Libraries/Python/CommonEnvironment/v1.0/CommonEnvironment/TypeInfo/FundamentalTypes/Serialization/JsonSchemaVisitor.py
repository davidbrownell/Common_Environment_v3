# ----------------------------------------------------------------------
# |
# |  JsonSchemaVisitor.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-07-27 08:38:41
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the JsonSchemaVisitor object"""

import os

from collections import OrderedDict
import six

import CommonEnvironment
from CommonEnvironment import Interface
from CommonEnvironment import RegularExpression

from CommonEnvironment.TypeInfo.Visitor import Visitor
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import RegularExpressionVisitor

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Parameters differ from overridden '<...>' method> pylint: disable = W0221

# ----------------------------------------------------------------------
@Interface.staticderived
class JsonSchemaVisitor(Visitor):
    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnBool(cls, type_info):
        return cls._Collectionize(
            type_info.Arity,
            {"type" : "boolean"},
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnDateTime(cls, type_info):
        return cls._Collectionize(
            type_info.Arity,
            {
                "type" : "string",
                "format" : "date-time",
            },
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnDate(cls, type_info):
        return cls._Collectionize(
            type_info.Arity,
            {
                "type" : "string",
                "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(RegularExpressionVisitor().Accept(type_info)[0])),
            },
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnDirectory(cls, type_info):
        return cls._Collectionize(
            type_info.Arity,
            {
                "type" : "string",
                "minLength" : 1,
            },
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnDuration(cls, type_info):
        return cls._Collectionize(
            type_info.Arity,
            {
                "type" : "string",
                "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(RegularExpressionVisitor().Accept(type_info)[0])),
            },
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnEnum(cls, type_info):
        return cls._Collectionize(
            type_info.Arity,
            {"enum" : type_info.Values},
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnFilename(cls, type_info):
        return cls._Collectionize(
            type_info.Arity,
            {
                "type" : "string",
                "minLength" : 1,
            },
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnFloat(cls, type_info):
        result = {"type" : "number"}

        for attribute, json_schema_key in [
            ("Min", "minimum"),
            ("Max", "maximum"),
        ]:
            value = getattr(type_info, attribute, None)
            if value is not None:
                result[json_schema_key] = value

        return cls._Collectionize(type_info.Arity, result)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnGuid(cls, type_info):
        return cls._Collectionize(
            type_info.Arity,
            {
                "type" : "string",
                "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(RegularExpressionVisitor().Accept(type_info)[0])),
            },
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnInt(cls, type_info):
        result = {"type" : "integer"}

        for attribute, json_schema_key in [
            ("Min", "minimum"),
            ("Max", "maximum"),
        ]:
            value = getattr(type_info, attribute, None)
            if value is not None:
                result[json_schema_key] = value

        return cls._Collectionize(type_info.Arity, result)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnString(cls, type_info):
        result = {"type" : "string"}

        if type_info.ValidationExpression is not None:
            validation = RegularExpression.PythonToJavaScript(type_info.ValidationExpression)

            if not validation.startswith("^"):
                validation = "^{}".format(validation)
            if not validation.endswith("$"):
                validation = "{}$".format(validation)

            result["pattern"] = validation

        else:
            if type_info.MinLength not in [0, None]:
                result["minLength"] = type_info.MinLength
            if type_info.MaxLength:
                result["maxLength"] = type_info.MaxLength

        return cls._Collectionize(type_info.Arity, result)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnTime(cls, type_info):
        return cls._Collectionize(
            type_info.Arity,
            {
                "type" : "string",
                "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(RegularExpressionVisitor().Accept(type_info)[0])),
            },
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnUri(cls, type_info):
        return cls._Collectionize(
            type_info.Arity,
            {
                "type" : "string",
                "pattern" : "^{}$".format(RegularExpression.PythonToJavaScript(RegularExpressionVisitor().Accept(type_info)[0])),
            },
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnAnyOf(cls, type_info):
        return cls._Collectionize(
            type_info.Arity,
            {"anyOf" : [cls.Accept(ti) for ti in type_info.ElementTypeInfos]},
        )

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnClass(cls, type_info):
        return cls._OnDictLike(type_info)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnMethod(cls, type_info):
        raise Exception("Methods are not supported")

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnClassMethod(cls, type_info):
        raise Exception("Methods are not supported")

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnStaticMethod(cls, type_info):
        raise Exception("Methods are not supported")

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnDict(cls, type_info):
        return cls._OnDictLike(type_info)

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnGeneric(cls, type_info):
        return cls._Collectionize(type_info.Arity, {})

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def OnList(cls, type_info):
        return cls._Collectionize(type_info.Arity, cls.Accept(type_info.ElementTypeInfo))

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _Collectionize(arity, schema):
        if arity.Max == 1:
            return schema

        schema = {
            "type" : "array",
            "items" : schema,
        }

        if arity.Min != 0:
            schema["minItems"] = arity.Min
        if arity.Max is not None:
            schema["maxItems"] = arity.Max

        return schema

    # ----------------------------------------------------------------------
    @classmethod
    def _OnDictLike(cls, type_info):
        properties = OrderedDict()
        required = []

        for k, v in six.iteritems(type_info.Items):
            properties[k] = cls.Accept(v)

            if v.Arity.Min != 0:
                required.append(k)

        result = {
            "type" : "object",
            "properties" : properties,
        }

        if required:
            required.sort()
            result["required"] = required

        if type_info.RequireExactMatchDefault:
            result["additionalProperties"] = False

        return cls._Collectionize(type_info.Arity, result)
