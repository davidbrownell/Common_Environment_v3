# ----------------------------------------------------------------------
# |
# |  __init___UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-20 19:31:28
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-21.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Unit test for __init__.py"""

import datetime
import os
import re
import sys
import textwrap
import unittest

from collections import OrderedDict

import six

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class NonlocalsSuite(unittest.TestCase):
    def test_Standard(self):
        nonlocals = CommonEnvironment.Nonlocals( x=10,
                                                 y=20,
                                                 z=30,
                                               )

        # ----------------------------------------------------------------------
        def Foo():
            nonlocals.x = 100
            nonlocals.y = 200

        # ----------------------------------------------------------------------

        Foo()

        self.assertEqual(nonlocals.x, 100)
        self.assertEqual(nonlocals.y, 200)
        self.assertEqual(nonlocals.z, 30)

# ----------------------------------------------------------------------
class DescribeSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Dict(self):
        # Standard
        sink = six.moves.StringIO()
        CommonEnvironment.Describe(OrderedDict([ ( "a", "one" ),
                                                 ( "bee", 2 ),
                                                 ( "c", True ),
                                                 ( "d", 1.0 ),
                                               ]), sink)

        self.maxDiff = None

        if sys.version[0] == '2':
            type_name = "type"
        else:
            type_name = "class"

        self.assertEqual(sink.getvalue(), textwrap.dedent(
            """\
            a   : one
            bee : 2 <{type_name} 'int'>
            c   : True <{type_name} 'bool'>
            d   : 1.0 <{type_name} 'float'>


            """).format(type_name=type_name))

        # Nested
        sink = six.moves.StringIO()
        CommonEnvironment.Describe({ "nested" : { "foo" : "bar", "baz" : "biz", "one" : "more", }, "a" : "one", "bee" : 2, }, sink)

        if sys.version[0] == '2':
            self.assertEqual(sink.getvalue(), textwrap.dedent(
                """\
                a      : one
                bee    : 2 <type 'int'>
                nested : foo : bar
                         baz : biz
                         one : more


                """))
        else:
            self.assertEqual(sink.getvalue(), textwrap.dedent(
                """\
                nested : foo : bar
                         baz : biz
                         one : more
                a      : one
                bee    : 2 <class 'int'>


                """))

        # Empty
        sink = six.moves.StringIO()
        CommonEnvironment.Describe({}, sink)

        self.assertEqual(sink.getvalue(), textwrap.dedent(
            """\
            -- empty dict --


            """))

    # ----------------------------------------------------------------------
    def test_List(self):

        self.maxDiff = None

        if sys.version[0] == '2':
            type_name = "type"
        else:
            type_name = "class"

        # Standard
        sink = six.moves.StringIO()
        CommonEnvironment.Describe([ "one", 2, 3.0, ], sink)

        self.assertEqual(sink.getvalue(), textwrap.dedent(
            """\
            0)   one
            1)   2 <{type_name} 'int'>
            2)   3.0 <{type_name} 'float'>


            """).format(type_name=type_name))

        # Nested
        sink = six.moves.StringIO()
        CommonEnvironment.Describe([ "one", [ "foo", "bar", ], 2, 3.0, ], sink)

        self.assertEqual(sink.getvalue(), textwrap.dedent(
            """\
            0)   one
            1)   0)   foo
                 1)   bar
            2)   2 <{type_name} 'int'>
            3)   3.0 <{type_name} 'float'>


            """).format(type_name=type_name))

        # Empty
        sink = six.moves.StringIO()
        CommonEnvironment.Describe([], sink)

        self.assertEqual(sink.getvalue(), textwrap.dedent(
            """\
            -- empty list --


            """))

# ----------------------------------------------------------------------
class ObjectReprImpl(unittest.TestCase):
    def test_Standard(self):
        # ----------------------------------------------------------------------
        def CreateObj(
            include_methods,
            include_class_info,
            max_recursion_depth=None,
        ):
            class Object(CommonEnvironment.ObjectReprImplBase):
                def __init__(self, a, b, c):
                    CommonEnvironment.ObjectReprImplBase.__init__(
                        self,
                        include_class_info=include_class_info,
                        include_methods=include_methods,
                        max_recursion_depth=max_recursion_depth,
                    )

                    self.a = a
                    self.b = b
                    self.c = c

                def Method(self): pass

                @staticmethod
                def StaticMethod(): pass

                @classmethod
                def ClassMethod(cls): pass

            return Object("one", 2, Object(3.0, "four", Object('1', '2', True)))

        # ----------------------------------------------------------------------

        self.maxDiff = None

        if sys.version[0] == '2':
            class_name = "<class '__main__.Object'>"
            type_name = "type"
        else:
            class_name = "<class '__main__.ObjectReprImpl.test_Standard.<locals>.CreateObj.<locals>.Object'>"
            type_name = "class"

        self.assertEqual(str(CreateObj(False, True)), textwrap.dedent(
            """\
            {class_name}
            a : one
            b : 2 <{type_name} 'int'>
            c : {class_name}
                a : 3.0 <{type_name} 'float'>
                b : four
                c : {class_name}
                    a : 1
                    b : 2
                    c : True <{type_name} 'bool'>
            """).format(class_name=class_name, type_name=type_name))

        self.assertEqual(str(CreateObj(False, False)), textwrap.dedent(
            """\
            {class_name}
            a : one
            b : 2
            c : {class_name}
                a : 3.0
                b : four
                c : {class_name}
                    a : 1
                    b : 2
                    c : True
            """,
        ).format(class_name=class_name, type_name=type_name))

        self.assertEqual(str(CreateObj(True, True)), textwrap.dedent(
            """\
            {class_name}
            ClassMethod  : callable
            Method       : callable
            StaticMethod : callable
            ToString     : callable
            a            : one
            b            : 2 <{type_name} 'int'>
            c            : {class_name}
                           ClassMethod  : callable
                           Method       : callable
                           StaticMethod : callable
                           ToString     : callable
                           a            : 3.0 <{type_name} 'float'>
                           b            : four
                           c            : {class_name}
                                          ClassMethod  : callable
                                          Method       : callable
                                          StaticMethod : callable
                                          ToString     : callable
                                          a            : 1
                                          b            : 2
                                          c            : True <{type_name} 'bool'>
            """).format(class_name=class_name, type_name=type_name))

        self.assertEqual(str(CreateObj(True, False)), textwrap.dedent(
            """\
            {class_name}
            ClassMethod  : callable
            Method       : callable
            StaticMethod : callable
            ToString     : callable
            a            : one
            b            : 2
            c            : {class_name}
                           ClassMethod  : callable
                           Method       : callable
                           StaticMethod : callable
                           ToString     : callable
                           a            : 3.0
                           b            : four
                           c            : {class_name}
                                          ClassMethod  : callable
                                          Method       : callable
                                          StaticMethod : callable
                                          ToString     : callable
                                          a            : 1
                                          b            : 2
                                          c            : True
            """).format(class_name=class_name, type_name=type_name))

        self.assertEqual(str(CreateObj(True, False, 1)), textwrap.dedent(
            """\
            {class_name}
            ClassMethod  : callable
            Method       : callable
            StaticMethod : callable
            ToString     : callable
            a            : one
            b            : 2
            c            : -- recursion is disabled: complex element --
            """).format(class_name=class_name, type_name=type_name))

        self.assertEqual(str(CreateObj(True, False, 2)), textwrap.dedent(
            """\
            {class_name}
            ClassMethod  : callable
            Method       : callable
            StaticMethod : callable
            ToString     : callable
            a            : one
            b            : 2
            c            : {class_name}
                           ClassMethod  : callable
                           Method       : callable
                           StaticMethod : callable
                           ToString     : callable
                           a            : 3.0
                           b            : four
                           c            : -- recursion is disabled: complex element --
            """).format(class_name=class_name, type_name=type_name))


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
