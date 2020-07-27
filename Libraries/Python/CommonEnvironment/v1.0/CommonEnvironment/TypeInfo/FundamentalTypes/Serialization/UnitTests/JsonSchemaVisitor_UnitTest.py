# ----------------------------------------------------------------------
# |
# |  JsonSchemaVisitor_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-07-27 08:36:21
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for JsonSchemaVisitor.py"""

import os
import sys
import unittest

import CommonEnvironment
from CommonEnvironment.TypeInfo import Arity
from CommonEnvironment.TypeInfo.All import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.JsonSchemaVisitor import JsonSchemaVisitor

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def setUp(self):
        self.maxDiff = None
        self._visitor = JsonSchemaVisitor()

    # ----------------------------------------------------------------------
    def test_Boolean(self):
        self.assertEqual(
            self._visitor.Accept(BoolTypeInfo()),
            {"type" : "boolean"},
        )

        self.assertEqual(
            self._visitor.Accept(
                BoolTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {"type" : "boolean"},
            },
        )

    # ----------------------------------------------------------------------
    def test_DateTime(self):
        self.assertEqual(
            self._visitor.Accept(DateTimeTypeInfo()),
            {
                "type" : "string",
                "format" : "date-time",
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                DateTimeTypeInfo(
                    arity=Arity.FromString("+"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "string",
                    "format" : "date-time",
                },
                "minItems" : 1,
            },
        )

    # ----------------------------------------------------------------------
    def test_Date(self):
        self.assertEqual(
            self._visitor.Accept(DateTypeInfo()),
            {
                "type" : "string",
                "pattern" : "^([0-9]{4})[-/\\.](0?[1-9]|1[0-2])[-/\\.]([0-2][0-9]|3[0-1])$",
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                DateTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "string",
                    "pattern" : "^([0-9]{4})[-/\\.](0?[1-9]|1[0-2])[-/\\.]([0-2][0-9]|3[0-1])$",
                },
            },
        )

    # ----------------------------------------------------------------------
    def test_Directory(self):
        self.assertEqual(
            self._visitor.Accept(DirectoryTypeInfo()),
            {
                "type" : "string",
                "minLength" : 1,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                DirectoryTypeInfo(
                    arity=Arity.FromString("+"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "string",
                    "minLength" : 1,
                },
                "minItems" : 1,
            },
        )

    # ----------------------------------------------------------------------
    def test_Duration(self):
        self.assertEqual(
            self._visitor.Accept(DurationTypeInfo()),
            {
                "type" : "string",
                "pattern" : "^(?:(\\d+)[\\.:])?(2[0-3]|[0-1][0-9]|[0-9]):([0-5][0-9]):([0-5][0-9])(?:\\.(\\d+))?$",
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                DurationTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "string",
                    "pattern" : "^(?:(\\d+)[\\.:])?(2[0-3]|[0-1][0-9]|[0-9]):([0-5][0-9]):([0-5][0-9])(?:\\.(\\d+))?$",
                },
            },
        )

    # ----------------------------------------------------------------------
    def test_Enum(self):
        self.assertEqual(
            self._visitor.Accept(EnumTypeInfo(["one", "two", "three"])),
            {
                "enum" : ["one", "two", "three"],
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                EnumTypeInfo(
                    ["one", "two", "three"],
                    arity=Arity.FromString("+"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "enum" : ["one", "two", "three"],
                },
                "minItems" : 1,
            },
        )

    # ----------------------------------------------------------------------
    def test_Filename(self):
        self.assertEqual(
            self._visitor.Accept(FilenameTypeInfo()),
            {
                "type" : "string",
                "minLength" : 1,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                FilenameTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "string",
                    "minLength" : 1,
                },
            },
        )

    # ----------------------------------------------------------------------
    def test_Float(self):
        self.assertEqual(
            self._visitor.Accept(FloatTypeInfo()),
            {"type" : "number"},
        )

        self.assertEqual(
            self._visitor.Accept(
                FloatTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {"type" : "number"},
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                FloatTypeInfo(
                    min=1.0,
                ),
            ),
            {
                "type" : "number",
                "minimum" : 1.0,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                FloatTypeInfo(
                    max=10.0,
                ),
            ),
            {
                "type" : "number",
                "maximum" : 10.0,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                FloatTypeInfo(
                    min=1.0,
                    max=10.0,
                ),
            ),
            {
                "type" : "number",
                "minimum" : 1.0,
                "maximum" : 10.0,
            },
        )

    # ----------------------------------------------------------------------
    def test_Guid(self):
        self.assertEqual(
            self._visitor.Accept(GuidTypeInfo()),
            {
                "type" : "string",
                "pattern" : "^\\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\\}$",
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                GuidTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "string",
                    "pattern" : "^\\{[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\\}$",
                },
            },
        )

    # ----------------------------------------------------------------------
    def test_Int(self):
        self.assertEqual(
            self._visitor.Accept(IntTypeInfo()),
            {"type" : "integer"},
        )

        self.assertEqual(
            self._visitor.Accept(
                IntTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {"type" : "integer"},
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                IntTypeInfo(
                    min=1,
                ),
            ),
            {
                "type" : "integer",
                "minimum" : 1,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                IntTypeInfo(
                    max=10,
                ),
            ),
            {
                "type" : "integer",
                "maximum" : 10,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                IntTypeInfo(
                    min=1,
                    max=10,
                ),
            ),
            {
                "type" : "integer",
                "minimum" : 1,
                "maximum" : 10,
            },
        )

    # ----------------------------------------------------------------------
    def test_String(self):
        self.assertEqual(
            self._visitor.Accept(StringTypeInfo()),
            {
                "type" : "string",
                "minLength" : 1,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                StringTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "string",
                    "minLength" : 1,
                },
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                StringTypeInfo(
                    validation_expression="foo",
                ),
            ),
            {
                "type" : "string",
                "pattern" : "^foo$",
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                StringTypeInfo(
                    validation_expression="^foo",
                ),
            ),
            {
                "type" : "string",
                "pattern" : "^foo$",
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                StringTypeInfo(
                    validation_expression="foo$",
                ),
            ),
            {
                "type" : "string",
                "pattern" : "^foo$",
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                StringTypeInfo(
                    min_length=2,
                ),
            ),
            {
                "type" : "string",
                "minLength" : 2,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                StringTypeInfo(
                    max_length=10,
                ),
            ),
            {
                "type" : "string",
                "minLength" : 1,
                "maxLength" : 10,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                StringTypeInfo(
                    min_length=2,
                    max_length=10,
                ),
            ),
            {
                "type" : "string",
                "minLength" : 2,
                "maxLength" : 10,
            },
        )

    # ----------------------------------------------------------------------
    def test_Time(self):
        self.assertEqual(
            self._visitor.Accept(TimeTypeInfo()),
            {
                "type" : "string",
                "pattern" : "^([0-1][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])(?:\\.(\\d+))?$",
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                TimeTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "string",
                    "pattern" : "^([0-1][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])(?:\\.(\\d+))?$",
                },
            },
        )

    # ----------------------------------------------------------------------
    def test_Uri(self):
        self.assertEqual(
            self._visitor.Accept(UriTypeInfo()),
            {
                "type" : "string",
                "pattern" : "^\\S+?://\\S+$"
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                UriTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "string",
                    "pattern" : "^\\S+?://\\S+$"
                },
            },
        )

    # ----------------------------------------------------------------------
    def test_AnyOf(self):
        self.assertEqual(
            self._visitor.Accept(
                AnyOfTypeInfo([BoolTypeInfo(), IntTypeInfo()]),
            ),
            {
                "anyOf" : [{"type" : "boolean"}, {"type" : "integer"}],
            },
        )

        # I'm not sure if this is correct for all cases, but this is how
        # it is currently implemented.
        self.assertEqual(
            self._visitor.Accept(
                AnyOfTypeInfo(
                    [
                        BoolTypeInfo(
                            arity=Arity(1, 2),
                        ),
                        IntTypeInfo(
                            arity=Arity(3, 4),
                        ),
                    ],
                    arity=Arity(5, 6),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "anyOf" : [
                        {
                            "type" : "array",
                            "items" : {
                                "type" : "boolean",
                            },
                            "minItems" : 1,
                            "maxItems" : 2,
                        },
                        {
                            "type" : "array",
                            "items" : {
                                "type" : "integer",
                            },
                            "minItems" : 3,
                            "maxItems" : 4,
                        },
                    ],
                },
                "minItems" : 5,
                "maxItems" : 6,
            },
        )

    # ----------------------------------------------------------------------
    def test_Class(self):
        self.assertEqual(
            self._visitor.Accept(
                ClassTypeInfo(
                    a=IntTypeInfo(),
                    b=BoolTypeInfo(),
                ),
            ),
            {
                "type" : "object",
                "properties" : {
                    "a" : {"type" : "integer"},
                    "b" : {"type" : "boolean"},
                },
                "required" : ["a", "b"],
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                ClassTypeInfo(
                    a=IntTypeInfo(),
                    b=BoolTypeInfo(),
                    require_exact_match=True,
                ),
            ),
            {
                "type" : "object",
                "properties" : {
                    "a" : {"type" : "integer"},
                    "b" : {"type" : "boolean"},
                },
                "required" : ["a", "b"],
                "additionalProperties" : False,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                ClassTypeInfo(
                    a=IntTypeInfo(),
                    b=BoolTypeInfo(
                        arity=Arity.FromString("?"),
                    ),
                ),
            ),
            {
                "type" : "object",
                "properties" : {
                    "a" : {"type" : "integer"},
                    "b" : {"type" : "boolean"},
                },
                "required" : ["a"]
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                ClassTypeInfo(
                    a=IntTypeInfo(),
                    b=BoolTypeInfo(),
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "object",
                    "properties" : {
                        "a" : {"type" : "integer"},
                        "b" : {"type" : "boolean"},
                    },
                    "required" : ["a", "b"],
                },
            },
        )

    # ----------------------------------------------------------------------
    def test_Method(self):
        self.assertRaises(Exception, lambda: self._visitor.Accept(MethodTypeInfo()))

    # ----------------------------------------------------------------------
    def test_ClassMethod(self):
        self.assertRaises(Exception, lambda: self._visitor.Accept(ClassMethodTypeInfo()))

    # ----------------------------------------------------------------------
    def test_StaticMethod(self):
        self.assertRaises(Exception, lambda: self._visitor.Accept(StaticMethodTypeInfo()))

    # ----------------------------------------------------------------------
    def test_Dict(self):
        self.assertEqual(
            self._visitor.Accept(
                DictTypeInfo(
                    a=IntTypeInfo(),
                    b=BoolTypeInfo(),
                ),
            ),
            {
                "type" : "object",
                "properties" : {
                    "a" : {"type" : "integer"},
                    "b" : {"type" : "boolean"},
                },
                "required" : ["a", "b"],
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                DictTypeInfo(
                    a=IntTypeInfo(),
                    b=BoolTypeInfo(),
                    require_exact_match=True,
                ),
            ),
            {
                "type" : "object",
                "properties" : {
                    "a" : {"type" : "integer"},
                    "b" : {"type" : "boolean"},
                },
                "required" : ["a", "b"],
                "additionalProperties" : False,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                DictTypeInfo(
                    a=IntTypeInfo(),
                    b=BoolTypeInfo(
                        arity=Arity.FromString("?"),
                    ),
                ),
            ),
            {
                "type" : "object",
                "properties" : {
                    "a" : {"type" : "integer"},
                    "b" : {"type" : "boolean"},
                },
                "required" : ["a"]
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                DictTypeInfo(
                    a=IntTypeInfo(),
                    b=BoolTypeInfo(),
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "object",
                    "properties" : {
                        "a" : {"type" : "integer"},
                        "b" : {"type" : "boolean"},
                    },
                    "required" : ["a", "b"],
                },
            },
        )

    # ----------------------------------------------------------------------
    def test_Generic(self):
        self.assertEqual(
            self._visitor.Accept(GenericTypeInfo()),
            {},
        )

        self.assertEqual(
            self._visitor.Accept(
                GenericTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {},
            },
        )

    # ----------------------------------------------------------------------
    def test_List(self):
        self.assertEqual(
            self._visitor.Accept(
                ListTypeInfo(
                    BoolTypeInfo(),
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {
                    "type" : "boolean",
                },
            },
        )

    # ----------------------------------------------------------------------
    def test_Collections(self):
        self.assertEqual(
            self._visitor.Accept(
                BoolTypeInfo(
                    arity=Arity(1, None),
                ),
            ),
            {
                "type" : "array",
                "items" : {"type" : "boolean"},
                "minItems" : 1,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                BoolTypeInfo(
                    arity=Arity(0, None),
                ),
            ),
            {
                "type" : "array",
                "items" : {"type" : "boolean"},
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                BoolTypeInfo(
                    arity=Arity(0, 10),
                ),
            ),
            {
                "type" : "array",
                "items" : {"type" : "boolean"},
                "maxItems" : 10,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                BoolTypeInfo(
                    arity=Arity(5, 10),
                ),
            ),
            {
                "type" : "array",
                "items" : {"type" : "boolean"},
                "minItems" : 5,
                "maxItems" : 10,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                BoolTypeInfo(
                    arity=Arity(2, 2),
                ),
            ),
            {
                "type" : "array",
                "items" : {"type" : "boolean"},
                "minItems" : 2,
                "maxItems" : 2,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                BoolTypeInfo(
                    arity=Arity.FromString("*"),
                ),
            ),
            {
                "type" : "array",
                "items" : {"type" : "boolean"},
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                BoolTypeInfo(
                    arity=Arity.FromString("+"),
                ),
            ),
            {
                "type" : "array",
                "items" : {"type" : "boolean"},
                "minItems" : 1,
            },
        )

        self.assertEqual(
            self._visitor.Accept(
                BoolTypeInfo(
                    arity=Arity.FromString("?"),
                ),
            ),
            {"type" : "boolean"},
        )


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(
            unittest.main(
                verbosity=2,
            ),
        )
    except KeyboardInterrupt:
        pass
