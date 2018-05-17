# ----------------------------------------------------------------------
# |  
# |  EnumTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 23:35:21
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for EnumTypeInfo.py."""

import os
import sys
import unittest

import six

from CommonEnvironment.TypeInfo.FundamentalTypes.EnumTypeInfo import EnumTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Construct(self):
        EnumTypeInfo([ "one", ])
        EnumTypeInfo([ "one", "two", ])
        EnumTypeInfo([ "one", ], [ "1", ])
        EnumTypeInfo([ "one", "two", ], [ "1", "2", ])

        self.assertRaises(Exception, lambda: EnumTypeInfo(None))
        self.assertRaises(Exception, lambda: EnumTypeInfo([]))
        self.assertRaises(Exception, lambda: EnumTypeInfo([ "one", "two", ], [ "1", ]))
        self.assertRaises(Exception, lambda: EnumTypeInfo([ "one", "two", ], [ "1", "2", "3", ]))

    # ----------------------------------------------------------------------
    def test_Single(self):
        eti = EnumTypeInfo([ "one", ])

        self.assertEqual(eti.Desc, "Enum")
        self.assertEqual(eti.ConstraintsDesc, 'Value must be "one"')
        self.assertEqual(eti.ExpectedType, six.string_types)
        self.assertEqual(eti.ValidateItemNoThrow("one"), None)
        self.assertEqual(eti.ValidateItemNoThrow("invalid"), """'invalid' is not a valid value ("one" expected)""")

    # ----------------------------------------------------------------------
    def test_Multiple(self):
        eti = EnumTypeInfo([ "one", "two", ])

        self.assertEqual(eti.Desc, "Enum")
        self.assertEqual(eti.ConstraintsDesc, 'Value must be one of "one", "two"')
        self.assertEqual(eti.ExpectedType, six.string_types)
        self.assertEqual(eti.ValidateItemNoThrow("one"), None)
        self.assertEqual(eti.ValidateItemNoThrow("two"), None)
        self.assertEqual(eti.ValidateItemNoThrow("invalid"), """'invalid' is not a valid value ("one", "two" expected)""")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
