# ----------------------------------------------------------------------
# |
# |  YamlSerialization_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-12 14:17:29
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for YamlSerialization.py."""

import datetime
import os
import sys
import unittest

import CommonEnvironment
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.YamlSerialization import YamlSerialization

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_SerializeItem(self):
        self.assertEqual(YamlSerialization.SerializeItem(BoolTypeInfo(), True), True)
        self.assertEqual(YamlSerialization.SerializeItem(FloatTypeInfo(), 1.0), 1.0)
        self.assertEqual(YamlSerialization.SerializeItem(IntTypeInfo(), 100), 100)
        self.assertEqual(
            YamlSerialization.SerializeItem(
                DurationTypeInfo(),
                datetime.timedelta(
                    seconds=130,
                ),
            ),
            datetime.timedelta(
                seconds=130,
            ),
        )

    # ----------------------------------------------------------------------
    def test_DeserializeItem(self):
        self.assertEqual(YamlSerialization.DeserializeItem(BoolTypeInfo(), True), True)
        self.assertEqual(YamlSerialization.DeserializeItem(FloatTypeInfo(), 1.0), 1.0)
        self.assertEqual(YamlSerialization.DeserializeItem(IntTypeInfo(), 100), 100)
        self.assertEqual(
            YamlSerialization.DeserializeItem(DurationTypeInfo(), "0:02:10.0"),
            datetime.timedelta(
                seconds=130,
            ),
        )


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
