# ----------------------------------------------------------------------
# |  
# |  IntTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 09:31:34
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for IntTypeInfo.py."""

import os
import sys
import unittest

from CommonEnvironment.TypeInfo.FundamentalTypes.IntTypeInfo import IntTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Default(self):
        iti = IntTypeInfo()

        self.assertEqual(iti.Desc, "Integer")
        self.assertEqual(iti.ConstraintsDesc, '')
        self.assertEqual(iti.ExpectedType, int)
        self.assertTrue(iti.IsValidItem(20))
        self.assertFalse(iti.IsValidItem("20"))

    # ----------------------------------------------------------------------
    def test_Min(self):
        iti = IntTypeInfo(-10)

        self.assertEqual(iti.Desc, "Integer")
        self.assertEqual(iti.ConstraintsDesc, "Value must be >= -10")
        self.assertEqual(iti.ExpectedType, int)
        self.assertTrue(iti.IsValidItem(20))
        self.assertFalse(iti.IsValidItem(-20))

    # ----------------------------------------------------------------------
    def test_Max(self):
        iti = IntTypeInfo(max=20)

        self.assertEqual(iti.Desc, "Integer")
        self.assertEqual(iti.ConstraintsDesc, "Value must be <= 20")
        self.assertEqual(iti.ExpectedType, int)
        self.assertTrue(iti.IsValidItem(20))
        self.assertFalse(iti.IsValidItem(21))

    # ----------------------------------------------------------------------
    def test_MinMax(self):
        iti = IntTypeInfo(-10, 20)

        self.assertEqual(iti.Desc, "Integer")
        self.assertEqual(iti.ConstraintsDesc, "Value must be >= -10, <= 20")
        self.assertEqual(iti.ExpectedType, int)
        self.assertTrue(iti.IsValidItem(20))
        self.assertTrue(iti.IsValidItem(-10))
        self.assertFalse(iti.IsValidItem(-20))
        self.assertFalse(iti.IsValidItem(21))

    # ----------------------------------------------------------------------
    def test_Bytes(self):
        self.assertEqual(IntTypeInfo(bytes=1).Min, -128)
        self.assertEqual(IntTypeInfo(bytes=1).Max, 127)
        self.assertEqual(IntTypeInfo(bytes=1, unsigned=True).Min, 0)
        self.assertEqual(IntTypeInfo(bytes=1, unsigned=True).Max, 255)

        self.assertEqual(IntTypeInfo(bytes=2).Min, -32768)
        self.assertEqual(IntTypeInfo(bytes=2).Max, 32767)
        self.assertEqual(IntTypeInfo(bytes=2, unsigned=True).Min, 0)
        self.assertEqual(IntTypeInfo(bytes=2, unsigned=True).Max, 65535)

        self.assertEqual(IntTypeInfo(bytes=4).Min, -2147483648)
        self.assertEqual(IntTypeInfo(bytes=4).Max, 2147483647)
        self.assertEqual(IntTypeInfo(bytes=4, unsigned=True).Min, 0)
        self.assertEqual(IntTypeInfo(bytes=4, unsigned=True).Max, 4294967295)

        self.assertEqual(IntTypeInfo(bytes=8).Min, -9223372036854775808)
        self.assertEqual(IntTypeInfo(bytes=8).Max, 9223372036854775807)
        self.assertEqual(IntTypeInfo(bytes=8, unsigned=True).Min, 0)
        self.assertEqual(IntTypeInfo(bytes=8, unsigned=True).Max, 18446744073709551615)

    # ----------------------------------------------------------------------
    def test_ConstructErrors(self):
        self.assertRaises(Exception, lambda: IntTypeInfo(20, 10))
        self.assertRaises(Exception, lambda: IntTypeInfo(bytes=3))
        self.assertRaises(Exception, lambda: IntTypeInfo(min=0, max=1000, bytes=1))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
