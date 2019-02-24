# ----------------------------------------------------------------------
# |
# |  XmlSerialization_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-23 22:00:42
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Unit test for XmlSerialization.py."""

import datetime
import os
import sys
import unittest

import CommonEnvironment
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.XmlSerialization import XmlSerialization

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_SerializeItem(self):
        self.assertEqual(XmlSerialization.SerializeItem(BoolTypeInfo(), True), "true")
        self.assertEqual(XmlSerialization.SerializeItem(DateTimeTypeInfo(), datetime.datetime(2019, 2, 23, 18, 12, 35)), "2019-02-23T18:12:35")
        self.assertEqual(XmlSerialization.SerializeItem(DurationTypeInfo(), datetime.timedelta(hours=3, minutes=20, seconds=4)), "P0DT3H20M4S")


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(
            unittest.main(
                verbosity=2,
            ),
        )
    except KeyboardInterrupt:
        pass
