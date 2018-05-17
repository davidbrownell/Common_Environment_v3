# ----------------------------------------------------------------------
# |  
# |  Constraints_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 16:13:20
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for Constraints.py."""

import os
import sys
import unittest

from CommonEnvironment import Nonlocals
from CommonEnvironment.Constraints import *
from CommonEnvironment.TypeInfo import ValidationException
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        # ----------------------------------------------------------------------
        @Constraints( a=IntTypeInfo(min=10, max=10),
                      b=IntTypeInfo(min=20, max=20),
                    )
        def Func(a, b):
            return a + b

        # ----------------------------------------------------------------------

        self.assertEqual(Func(10, 20), 30)

        try:
            Func(11, 20)
            self.fail()
        except ValidationException as ex:
            self.assertEqual(str(ex), "Validation for the arg 'a' failed - 11 is not <= 10")

        try:
            Func(10, 21)
            self.fail()
        except ValidationException as ex:
            self.assertEqual(str(ex), "Validation for the arg 'b' failed - 21 is not <= 20")

    # ----------------------------------------------------------------------
    def test_Postcondition(self):
        # ----------------------------------------------------------------------
        @Constraints( postcondition=IntTypeInfo(min=20, max=20),
                    )
        def Func(a):
            return a

        # ----------------------------------------------------------------------

        self.assertEqual(Func(20), 20)

        try:
            Func(21)
            self.fail()
        except ValidationException as ex:
            self.assertEqual(str(ex), "Validation for the result failed - 21 is not <= 20")

    # ----------------------------------------------------------------------
    def test_NoConditions(self):
        try:
            @Constraints()
            def Func():
                pass

            self.fail()
        except Exception as ex:
            # print(ex)
            self.assertTrue(True)

    # ----------------------------------------------------------------------
    def test_InvalidConditions(self):
        try:
            @Constraints(a=StringTypeInfo())
            def Func(b):
                pass

            Func("test")

            self.fail()
        except Exception as ex:
            # print(ex)
            self.assertTrue(True)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
