# ----------------------------------------------------------------------
# |  
# |  JsonSerialization_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 22:00:42
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for JsonSerialization.py."""

import datetime
import os
import sys
import unittest

from CommonEnvironment.TypeInfo.FundamentalTypes.All import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.JsonSerialization import JsonSerialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_SerializeItem(self):
        self.assertEqual(JsonSerialization.SerializeItem(BoolTypeInfo(), True), True)
        self.assertEqual(JsonSerialization.SerializeItem(FloatTypeInfo(), 1.0), 1.0)
        self.assertEqual(JsonSerialization.SerializeItem(IntTypeInfo(), 100), 100)
        self.assertEqual(JsonSerialization.SerializeItem(DurationTypeInfo(), datetime.timedelta(seconds=130)), "0:02:10")

    # ----------------------------------------------------------------------
    def test_DeserializeItem(self):
        self.assertEqual(JsonSerialization.DeserializeItem(BoolTypeInfo(), True), True)
        self.assertEqual(JsonSerialization.DeserializeItem(FloatTypeInfo(), 1.0), 1.0)
        self.assertEqual(JsonSerialization.DeserializeItem(IntTypeInfo(), 100), 100)
        self.assertEqual(JsonSerialization.DeserializeItem(DurationTypeInfo(), "0:02:10.0"), datetime.timedelta(seconds=130))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass