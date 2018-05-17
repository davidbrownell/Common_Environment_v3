# ----------------------------------------------------------------------
# |  
# |  DateTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 23:00:25
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for DateTypeInfo.py."""

import datetime
import os
import sys
import unittest

from CommonEnvironment.TypeInfo.FundamentalTypes.DateTypeInfo import DateTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEqual(DateTypeInfo.Desc, "Date")
        self.assertEqual(DateTypeInfo.ConstraintsDesc, '')
        self.assertEqual(DateTypeInfo.ExpectedType, datetime.date)

    # ----------------------------------------------------------------------
    def test_Create(self):
        self.assertEqual(DateTypeInfo.Create(), datetime.date.today())

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
