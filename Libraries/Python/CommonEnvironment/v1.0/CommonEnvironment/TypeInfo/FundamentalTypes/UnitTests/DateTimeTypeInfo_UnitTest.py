# ----------------------------------------------------------------------
# |  
# |  DateTimeTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 22:48:49
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for DateTimeTypeInfo.py."""

import datetime
import os
import sys
import unittest

from CommonEnvironment.TypeInfo.FundamentalTypes.DateTimeTypeInfo import DateTimeTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEqual(DateTimeTypeInfo.Desc, "Datetime")
        self.assertEqual(DateTimeTypeInfo.ConstraintsDesc, '')
        self.assertEqual(DateTimeTypeInfo.ExpectedType, datetime.datetime)

    # ----------------------------------------------------------------------
    def test_Create(self):
        past = DateTimeTypeInfo.Create()
        result = datetime.datetime.now() - past
        self.assertTrue(result <= datetime.timedelta(seconds=2))

        dt = DateTimeTypeInfo.Create(microseconds=False)
        self.assertEqual(dt.microsecond, 0)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
