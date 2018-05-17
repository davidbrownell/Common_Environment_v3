# ----------------------------------------------------------------------
# |  
# |  AnyOfTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 19:37:12
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for AnyOfTypeInfo.py"""

import os
import sys
import unittest

from CommonEnvironment.TypeInfo.AnyOfTypeInfo import AnyOfTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def setUp(self):
        self.ti = AnyOfTypeInfo([ IntTypeInfo(min=10), StringTypeInfo() ])

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertRaises(Exception, lambda: AnyOfTypeInfo([]))
        
        self.assertEqual(self.ti.Desc, "Any of 'Integer', 'String'")
        self.assertEqual(self.ti.ConstraintsDesc, "Value where - Integer: Value must be >= 10 / String: Value must have more than 1 character")
        
        self.assertTrue(self.ti.IsExpectedType(12))    
        self.assertTrue(self.ti.IsExpectedType("test"))
        self.assertFalse(self.ti.IsExpectedType(10.0))
        
        self.assertTrue(self.ti.IsValidItem(12))
        self.assertTrue(self.ti.IsValidItem("test"))
        self.assertFalse(self.ti.IsValidItem(9))
        self.assertFalse(self.ti.IsValidItem(""))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass