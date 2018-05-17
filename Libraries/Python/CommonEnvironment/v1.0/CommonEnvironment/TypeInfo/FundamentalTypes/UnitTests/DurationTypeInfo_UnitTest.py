# ----------------------------------------------------------------------
# |  
# |  DurationTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 23:21:30
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for DurationTypeInfo.py."""

import datetime
import os
import sys
import unittest

from CommonEnvironment.TypeInfo.FundamentalTypes.DurationTypeInfo import DurationTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEqual(DurationTypeInfo.Desc, "Duration")
        self.assertEqual(DurationTypeInfo.ConstraintsDesc, '')
        self.assertEqual(DurationTypeInfo.ExpectedType, datetime.timedelta)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
