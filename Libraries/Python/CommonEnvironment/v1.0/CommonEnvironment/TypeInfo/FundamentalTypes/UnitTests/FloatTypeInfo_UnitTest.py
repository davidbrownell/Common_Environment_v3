# ----------------------------------------------------------------------
# |  
# |  FloatTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 00:21:09
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for FloatTypeInfo.py."""

import os
import sys
import unittest

from CommonEnvironment.TypeInfo.FundamentalTypes.FloatTypeInfo import FloatTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Empty(self):
        fti = FloatTypeInfo()

        self.assertEqual(fti.Desc, "Float")
        self.assertEqual(fti.ConstraintsDesc, '')
        self.assertEqual(fti.ExpectedType, (float, int))
        self.assertTrue(fti.IsValidItem(1.0))
        self.assertTrue(fti.IsValidItem(1))

    # ----------------------------------------------------------------------
    def test_Min(self):
        fti = FloatTypeInfo(min=2.0)

        self.assertEqual(fti.Desc, "Float")
        self.assertEqual(fti.ConstraintsDesc, "Value must be >= 2.0")
        self.assertEqual(fti.ExpectedType, (float, int))
        self.assertTrue(fti.IsValidItem(2.0))
        self.assertTrue(fti.IsValidItem(2))
        self.assertFalse(fti.IsValidItem(1.0))

    # ----------------------------------------------------------------------
    def test_Max(self):
        fti = FloatTypeInfo(max=2.0)

        self.assertEqual(fti.Desc, "Float")
        self.assertEqual(fti.ConstraintsDesc, "Value must be <= 2.0")
        self.assertEqual(fti.ExpectedType, (float, int))
        self.assertTrue(fti.IsValidItem(2.0))
        self.assertTrue(fti.IsValidItem(1))
        self.assertFalse(fti.IsValidItem(3.0))

    # ----------------------------------------------------------------------
    def test_MinMax(self):
        self.assertRaises(Exception, lambda: FloatTypeInfo(min=1.0, max=0.0))
        fti = FloatTypeInfo(min=2.0, max=10.0)

        self.assertEqual(fti.Desc, "Float")
        self.assertEqual(fti.ConstraintsDesc, "Value must be >= 2.0, <= 10.0")
        self.assertEqual(fti.ExpectedType, (float, int))
        self.assertTrue(fti.IsValidItem(2.0))
        self.assertTrue(fti.IsValidItem(2))
        self.assertTrue(fti.IsValidItem(10.0))
        self.assertTrue(fti.IsValidItem(10))
        self.assertFalse(fti.IsValidItem(1.0))
        self.assertFalse(fti.IsValidItem(11.0))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
