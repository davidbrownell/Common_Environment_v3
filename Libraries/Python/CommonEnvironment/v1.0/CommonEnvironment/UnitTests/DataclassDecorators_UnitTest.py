# ----------------------------------------------------------------------
# |
# |  DataclassDecorators_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-07-29 22:54:26
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for DataclassDecorators.py"""

import os

from dataclasses import dataclass

import CommonEnvironment
from CommonEnvironment.DataclassDecorators import *

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def test_DefaultValues():
    # ----------------------------------------------------------------------
    @DataclassDefaultValues(
        b=10,
    )
    @dataclass
    class MyDataClass(object):
        a: str
        b: int
        c: bool

    # ----------------------------------------------------------------------

    value = MyDataClass("Hello", True)

    assert value.a == "Hello"
    assert value.b == 10
    assert value.c == True

    value = MyDataClass("Hello", True, b="with_override")

    assert value.a == "Hello"
    assert value.b == "with_override"
    assert value.c == True


# ----------------------------------------------------------------------
def test_DefaultValuesBaseAndDerived():
    # ----------------------------------------------------------------------
    @dataclass(frozen=True)
    class Base(object):
        a: str
        b: int

    # ----------------------------------------------------------------------
    @DataclassDefaultValues(
        b=10,
    )
    @dataclass(frozen=True)
    class Derived(Base):
        c: bool

    # ----------------------------------------------------------------------

    value = Derived("Hello", True)

    assert value.a == "Hello"
    assert value.b == 10
    assert value.c == True

    value = Derived("Hello", True, b="with_override")

    assert value.a == "Hello"
    assert value.b == "with_override"
    assert value.c == True


# ----------------------------------------------------------------------
def test_ComparisonOperators():
    # ----------------------------------------------------------------------
    @ComparisonOperators
    @dataclass(frozen=True)
    class Location(object):
        line: int
        column: int

        @staticmethod
        def Compare(a: "Location", b:"Location") -> int:
            result = a.line - b.line
            if result != 0:
                return result

            result = a.column - b.column
            if result != 0:
                return result

            return 0

    # ----------------------------------------------------------------------

    assert Location(1, 2) == Location(1, 2)
    assert Location(1, 2) != Location(3, 4)
    assert Location(1, 2) != Location(1, 5)
    assert Location(1, 2) < Location(3, 4)
    assert Location(1, 2) < Location(1, 5)
    assert Location(1, 2) <= Location(3, 4)
    assert Location(1, 2) <= Location(1, 2)
    assert Location(3, 4) > Location(1, 2)
    assert Location(1, 5) > Location(1, 2)
    assert Location(3, 4) >= Location(1, 2)
    assert Location(1, 2) >= Location(1, 2)
