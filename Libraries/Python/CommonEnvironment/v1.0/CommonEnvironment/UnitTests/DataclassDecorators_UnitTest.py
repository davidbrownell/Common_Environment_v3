# ----------------------------------------------------------------------
# |
# |  DataclassDecorators_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-07-29 22:54:26
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021
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
def test_Simple():
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
def test_BaseAndDerived():
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
