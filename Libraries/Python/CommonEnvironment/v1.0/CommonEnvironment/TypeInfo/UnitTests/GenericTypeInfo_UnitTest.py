# ----------------------------------------------------------------------
# |  
# |  GenericTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-10-24 22:18:54
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for GenericTypeInfo.py"""

import os
import sys
import unittest

import CommonEnvironment
from CommonEnvironment.TypeInfo.GenericTypeInfo import GenericTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def setUp(self):
        self.ti = GenericTypeInfo(arity="{2}")

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEqual(self.ti.Desc, "Generic")
        self.assertEqual(self.ti.ConstraintsDesc, '')
        self.assertTrue(self.ti.ExpectedType(int))
        self.assertTrue(self.ti.ExpectedType(bool))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
