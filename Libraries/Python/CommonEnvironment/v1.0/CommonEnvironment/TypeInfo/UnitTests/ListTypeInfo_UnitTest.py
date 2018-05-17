# ----------------------------------------------------------------------
# |  
# |  ListTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 21:00:54
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for ListTypeInfo.py"""

import os
import sys
import unittest

from CommonEnvironment.TypeInfo.ListTypeInfo import ListTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def setUp(self):
        self.ti = ListTypeInfo( StringTypeInfo(min_length=2, arity="{3}"),
                                arity="{2}",
                              )

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEqual(self.ti.Desc, "List")
        self.assertEqual(self.ti.ExpectedType, (list, tuple))
        self.assertEqual(self.ti.ConstraintsDesc, "List of 'String' values where each value must have more than 2 characters")

        l = [ [ "abc", "def", "ghi", ],
              [ "012", "345", "678", ],
            ]

        self.assertTrue(self.ti.IsValid(l))

        # Too many items in the list
        l.append([ "xxx", "yyy", "zzz", ])
        self.assertFalse(self.ti.IsValid(l))
        l.pop()

        # Too many elements for an item within the list
        l[0].append("xxx")
        self.assertFalse(self.ti.IsValid(l))
        l[0].pop()

        # Invalid element for an item within the list
        l[0][0] = "1"
        self.assertFalse(self.ti.IsValid(l))
        l[0][0] = "abc"

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass