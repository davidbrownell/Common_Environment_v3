# ----------------------------------------------------------------------
# |  
# |  StringTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 11:36:02
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for StringTypeInfo.py."""

import os
import sys
import unittest

import six

from CommonEnvironment.TypeInfo.FundamentalTypes.StringTypeInfo import StringTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        sti = StringTypeInfo()

        self.assertEqual(sti.Desc, "String")
        self.assertEqual(sti.ConstraintsDesc, "Value must have more than 1 character")
        self.assertEqual(sti.ExpectedType, six.string_types)
        self.assertEqual(sti.MinLength, 1)
        self.assertEqual(sti.MaxLength, None)
        self.assertEqual(sti.ValidationExpression, None)
        self.assertTrue(sti.IsValidItem("test"))
        self.assertFalse(sti.IsValidItem(""))
        self.assertFalse(sti.IsValidItem(None))

    # ----------------------------------------------------------------------
    def test_ValidationExpression(self):
        sti = StringTypeInfo("[A-Z][a-z]{3}")

        self.assertEqual(sti.Desc, "String")
        self.assertEqual(sti.ConstraintsDesc, "Value must match the regular expression '[A-Z][a-z]{3}'")
        self.assertEqual(sti.ExpectedType, six.string_types)
        self.assertEqual(sti.MinLength, None)
        self.assertEqual(sti.MaxLength, None)
        self.assertEqual(sti.ValidationExpression, "[A-Z][a-z]{3}")
        self.assertTrue(sti.IsValidItem("Test"))
        self.assertFalse(sti.IsValidItem("test"))
        self.assertFalse(sti.IsValidItem(None))

    # ----------------------------------------------------------------------
    def test_Min(self):
        sti = StringTypeInfo(min_length=2)

        self.assertEqual(sti.Desc, "String")
        self.assertEqual(sti.ConstraintsDesc, "Value must have more than 2 characters")
        self.assertEqual(sti.ExpectedType, six.string_types)
        self.assertEqual(sti.MinLength, 2)
        self.assertEqual(sti.MaxLength, None)
        self.assertEqual(sti.ValidationExpression, None)
        self.assertTrue(sti.IsValidItem("test"))
        self.assertFalse(sti.IsValidItem("t"))
        self.assertFalse(sti.IsValidItem(None))

    # ----------------------------------------------------------------------
    def test_Max(self):
        sti = StringTypeInfo(max_length=4)

        self.assertEqual(sti.Desc, "String")
        self.assertEqual(sti.ConstraintsDesc, "Value must have more than 1 character, have less than 4 characters")
        self.assertEqual(sti.ExpectedType, six.string_types)
        self.assertEqual(sti.MinLength, 1)
        self.assertEqual(sti.MaxLength, 4)
        self.assertEqual(sti.ValidationExpression, None)
        self.assertTrue(sti.IsValidItem("test"))
        self.assertFalse(sti.IsValidItem("testing"))
        self.assertFalse(sti.IsValidItem(None))

    # ----------------------------------------------------------------------
    def test_ConstructErrors(self):
        self.assertRaises(Exception, lambda: StringTypeInfo("expr", min_length=10))
        self.assertRaises(Exception, lambda: StringTypeInfo("expr", max_length=10))
        self.assertRaises(Exception, lambda: StringTypeInfo(min_length=-1))
        self.assertRaises(Exception, lambda: StringTypeInfo(min_length=20, max_length=10))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
