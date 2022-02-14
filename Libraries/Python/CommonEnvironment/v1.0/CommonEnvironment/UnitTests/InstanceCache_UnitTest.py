# ----------------------------------------------------------------------
# |
# |  InstanceCache_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-10-15 21:11:48
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for InstanceCache.py"""

import os

import CommonEnvironment
from CommonEnvironment.Interface import clsinit

from CommonEnvironment.InstanceCache import *

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
def test_Instance():
    # ----------------------------------------------------------------------
    class Object(InstanceCache):
        # ----------------------------------------------------------------------
        @InstanceCacheGet
        def Invoke(self, value):
            return value

        # ----------------------------------------------------------------------
        @InstanceCacheReset
        def Reset(self):
            pass

    # ----------------------------------------------------------------------

    obj1 = Object()
    obj2 = Object()

    assert obj1.Invoke(10) == 10
    assert obj2.Invoke(100) == 100
    assert obj1.Invoke(20) == 10
    assert obj2.Invoke(200) == 100

    assert obj1.Invoke(1111, instance_cache_skip=True) == 1111
    assert obj2.Invoke(2222, instance_cache_skip=True) == 2222

    assert obj1.Invoke(1111) == 10
    assert obj2.Invoke(2222) == 100

    obj2.Reset()
    assert obj1.Invoke(30) == 10
    assert obj2.Invoke(400) == 400

    obj1.Reset()
    assert obj1.Invoke(50) == 50
    assert obj2.Invoke(500) == 400


# ----------------------------------------------------------------------
def test_Class():
    # ----------------------------------------------------------------------
    @clsinit
    class Object(InstanceCache):
        # ----------------------------------------------------------------------
        @classmethod
        @InstanceCacheGet
        def Invoke(cls, value):
            return value

        # ----------------------------------------------------------------------
        @classmethod
        @InstanceCacheReset
        def Reset(cls):
            pass

    # ----------------------------------------------------------------------

    assert Object.Invoke(10) == 10
    assert Object.Invoke(100) == 10
    assert Object.Invoke(20) == 10
    assert Object.Invoke(200) == 10

    assert Object.Invoke(1111, instance_cache_skip=True) == 1111
    assert Object.Invoke(2222, instance_cache_skip=True) == 2222

    assert Object.Invoke(1111) == 10
    assert Object.Invoke(2222) == 10

    Object.Reset()
    assert Object.Invoke(30) == 30
    assert Object.Invoke(400) == 30

    Object.Reset()
    assert Object.Invoke(50) == 50
    assert Object.Invoke(500) == 50
