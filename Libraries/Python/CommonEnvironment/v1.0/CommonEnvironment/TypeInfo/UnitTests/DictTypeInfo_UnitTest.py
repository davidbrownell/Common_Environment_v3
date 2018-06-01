# ----------------------------------------------------------------------
# |  
# |  DictTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 20:08:29
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for DictTypeInfo.py"""

import os
import sys
import unittest

from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def setUp(self):
        self.ti = DictTypeInfo(a=IntTypeInfo(min=10), b=StringTypeInfo())

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEqual(self.ti.Desc, "Dictionary")
        self.assertEqual(self.ti.ExpectedType, dict)
        self.assertEqual(self.ti.ConstraintsDesc, "Value must contain the attributes 'a' <Integer>, 'b' <String>")
        DictTypeInfo() # Empty is OK when require_exact_match is False or not set
        self.assertRaises(Exception, lambda: DictTypeInfo(require_exact_match=True))

    # ----------------------------------------------------------------------
    def test_Validation(self):
        self.assertTrue(self.ti.IsValidItem({ "a" : 20, "b" : "test", }))
        self.assertFalse(self.ti.IsValidItem({ "a" : 20, "b" : "test", "c" : None, }))
        self.assertTrue(self.ti.IsValidItem({ "a" : 20, "b" : "test", "c" : None, }, require_exact_match=False))
        self.assertFalse(self.ti.IsValidItem({ "a" : 5, "b" : "test", }))
        self.assertFalse(self.ti.IsValidItem({ "a" : 20, "b" : "", }))
        self.assertFalse(self.ti.IsValidItem({ "a" : 20, "b" : 0, }))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass