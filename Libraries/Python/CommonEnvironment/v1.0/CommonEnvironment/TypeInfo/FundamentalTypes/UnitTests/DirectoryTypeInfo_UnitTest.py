# ----------------------------------------------------------------------
# |  
# |  DirectoryTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 23:11:30
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for DirectoryTypeInfo.py"""

import os
import sys
import unittest

import six

from CommonEnvironment.TypeInfo.FundamentalTypes.DirectoryTypeInfo import DirectoryTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        dti = DirectoryTypeInfo()

        self.assertEqual(dti.Desc, "Directory")
        self.assertEqual(dti.ConstraintsDesc, "Value must be a valid directory")
        self.assertEqual(dti.ExpectedType, six.string_types)
        
        self.assertTrue(dti.IsValidItem(os.getcwd()))
        self.assertFalse(dti.IsValidItem("this is a directory that doesn't exist"))

    # ----------------------------------------------------------------------
    def test_NoExist(self):
        dti = DirectoryTypeInfo(ensure_exists=False)

        self.assertEqual(dti.Desc, "Directory")
        self.assertEqual(dti.ConstraintsDesc, '')
        self.assertEqual(dti.ExpectedType, six.string_types)

        self.assertTrue(dti.IsValidItem(os.getcwd()))
        self.assertTrue(dti.IsValidItem("this is a directory that doesn't exist"))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
