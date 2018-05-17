# ----------------------------------------------------------------------
# |  
# |  FilenameTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 00:04:03
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for FilenameTypeInfo.py."""

import os
import sys
import unittest

import six

from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        fti = FilenameTypeInfo()

        self.assertEqual(fti.Desc, "Filename")
        self.assertEqual(fti.ConstraintsDesc, "Value must be a valid file")
        self.assertEqual(fti.ExpectedType, six.string_types)
        self.assertTrue(fti.IsValidItem(_script_fullpath))
        self.assertFalse(fti.IsValidItem(_script_dir))
        self.assertFalse(fti.IsValidItem("filename that doesn't exist"))

    # ----------------------------------------------------------------------
    def test_NoEnsureExists(self):
        fti = FilenameTypeInfo(ensure_exists=False)

        self.assertEqual(fti.Desc, "Filename")
        self.assertEqual(fti.ConstraintsDesc, '')
        self.assertEqual(fti.ExpectedType, six.string_types)
        self.assertTrue(fti.IsValidItem(_script_fullpath))
        self.assertTrue(fti.IsValidItem(_script_dir))
        self.assertTrue(fti.IsValidItem("filename that doesn't exist"))

    # ----------------------------------------------------------------------
    def test_MatchAny(self):
        fti = FilenameTypeInfo(match_any=True)

        self.assertEqual(fti.Desc, "Filename")
        self.assertEqual(fti.ConstraintsDesc, "Value must be a valid file or directory")
        self.assertEqual(fti.ExpectedType, six.string_types)
        self.assertTrue(fti.IsValidItem(_script_fullpath))
        self.assertTrue(fti.IsValidItem(_script_dir))
        self.assertFalse(fti.IsValidItem("filename that doesn't exist"))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
