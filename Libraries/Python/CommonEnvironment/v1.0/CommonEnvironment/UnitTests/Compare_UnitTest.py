# ----------------------------------------------------------------------
# |
# |  Compare_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-06-27 11:10:05
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains tests for ./Compare.py"""

import os

from enum import auto, Enum

import CommonEnvironment
from CommonEnvironment.Compare import *

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
def test_String():
    assert Compare("1", "1") == 0
    assert Compare("1", "2") == -1
    assert Compare("2", "1") == 1


# ----------------------------------------------------------------------
def test_Int():
    assert Compare(1, 1) == 0
    assert Compare(1, 2) == -1
    assert Compare(2, 1) == 1


# ----------------------------------------------------------------------
def test_Iterable():
    assert Compare([1, 2, 3], [1, 2, 3]) == 0
    assert Compare([1, 2, 3], [3, 2, 1]) == -1
    assert Compare([1, 2, 3], [3, ]) == -1
    assert Compare([1, 2, 3, 4], [1, 2, 3]) == 1


# ----------------------------------------------------------------------
def test_StaticCompare():
    # ----------------------------------------------------------------------
    class Values(object):
        # ----------------------------------------------------------------------
        def __init__(self, value1, value2):
            self.value1 = value1
            self.value2 = value2

        # ----------------------------------------------------------------------
        @staticmethod
        def Compare(a, b):
            if a.value1 != b.value1:
                return -1 if a.value1 < b.value1 else 1

            if a.value2 != b.value2:
                return -1 if a.value2 < b.value2 else 1

            return 0

    # ----------------------------------------------------------------------

    assert Compare(Values(1, 2), Values(1, 2)) == 0
    assert Compare(Values(1, 2), Values(2, 3)) == -1
    assert Compare(Values(1, 2), Values(1, 0)) == 1


# ----------------------------------------------------------------------
def test_MethodCompare():
    # ----------------------------------------------------------------------
    class Values(object):
        # ----------------------------------------------------------------------
        def __init__(self, value1, value2):
            self.value1 = value1
            self.value2 = value2

        # ----------------------------------------------------------------------
        def Compare(self, b):
            if self.value1 != b.value1:
                return -1 if self.value1 < b.value1 else 1

            if self.value2 != b.value2:
                return -1 if self.value2 < b.value2 else 1

            return 0

    # ----------------------------------------------------------------------

    assert Compare(Values(1, 2), Values(1, 2)) == 0
    assert Compare(Values(1, 2), Values(2, 3)) == -1
    assert Compare(Values(1, 2), Values(1, 0)) == 1


# ----------------------------------------------------------------------
def test_Enum():
    # ----------------------------------------------------------------------
    class MyEnum(Enum):
        one = auto()
        two = auto()

    # ----------------------------------------------------------------------

    assert Compare(MyEnum.one, MyEnum.one) == 0
    assert Compare(MyEnum.one, MyEnum.two) == -1
    assert Compare(MyEnum.two, MyEnum.one) == 1


# ----------------------------------------------------------------------
def test_CompareNone():
    assert Compare(None, None) == 0
    assert Compare(None, 1) == -1
    assert Compare(1, None) == 1
