# ----------------------------------------------------------------------
# |  
# |  CallOnExit_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-20 19:21:01
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for CallOnExit.py"""

import os
import sys
import unittest

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExitException, CallOnExit

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Standard(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_SingleValue(self):
        nonlocals = CommonEnvironment.Nonlocals(value=0)
        
        # ----------------------------------------------------------------------
        def SetValue1():
            nonlocals.value = 1
            
        # ----------------------------------------------------------------------

        with CallOnExit(SetValue1):
            pass

        self.assertEqual(nonlocals.value, 1)

    # ----------------------------------------------------------------------
    def test_MultipleValues(self):
        nonlocals = CommonEnvironment.Nonlocals( value1=0,
                                                 value2=0,
                                               )

        # ----------------------------------------------------------------------
        def SetValue1():
            nonlocals.value1 = 1

        # ----------------------------------------------------------------------
        def SetValue2():
            nonlocals.value2 = 1

        # ----------------------------------------------------------------------

        with CallOnExit(SetValue1, SetValue2):
            pass

        self.assertEqual(nonlocals.value1, 1)
        self.assertEqual(nonlocals.value2, 1)

    # ----------------------------------------------------------------------
    def test_AlwaysCall(self):
        nonlocals = CommonEnvironment.Nonlocals(value=0)

        # ----------------------------------------------------------------------
        def SetValue():
            nonlocals.value = 1

        # ----------------------------------------------------------------------

        try:
            with CallOnExit(SetValue):
                raise Exception("")
        except:
            pass

        self.assertEqual(nonlocals.value, 1)

    # ----------------------------------------------------------------------
    def test_OnlyOnSuccess(self):
        nonlocals = CommonEnvironment.Nonlocals(value=0)

        # ----------------------------------------------------------------------
        def SetValue():
            nonlocals.value = 1

        # ----------------------------------------------------------------------

        try:
            with CallOnExit(True, SetValue):
                raise Exception("")
        except:
            pass

        self.assertEqual(nonlocals.value, 0)

    # ----------------------------------------------------------------------
    def test_OnlyOnFailure(self):
        nonlocals = CommonEnvironment.Nonlocals(value=0)

        # ----------------------------------------------------------------------
        def SetValue():
            nonlocals.value = 1

        # ----------------------------------------------------------------------

        try:
            with CallOnExit(False, SetValue):
                raise Exception("")
        except:
            pass

        self.assertEqual(nonlocals.value, 1)

    # ----------------------------------------------------------------------
    def test_SingleInternalException(self):
        # ----------------------------------------------------------------------
        def Func():
            def Raiser():
                raise Exception("Raising")

            with CallOnExit(Raiser):
                pass

        # ----------------------------------------------------------------------

        self.assertRaises(CallOnExitException, Func)

    # ----------------------------------------------------------------------
    def test_DoubleIternalException(self):
        # ----------------------------------------------------------------------
        def Func():
            def Raiser1(): raise Exception("Raising 1")
            def Raiser2(): raise Exception("Raising 2")

            with CallOnExit(Raiser1, Raiser2):
                pass

        # ----------------------------------------------------------------------

        self.assertRaises(CallOnExitException, Func)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
