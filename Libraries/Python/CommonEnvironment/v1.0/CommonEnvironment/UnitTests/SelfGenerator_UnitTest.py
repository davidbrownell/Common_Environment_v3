# ----------------------------------------------------------------------
# |
# |  SelfGenerator_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-05-03 10:25:43
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for SelfGenerator.py."""

import os
import sys
import unittest

import CommonEnvironment
from CommonEnvironment.SelfGenerator import *

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_First(self):
        # ----------------------------------------------------------------------
        @SelfGenerator
        def Func(self):
            yield 1
            yield str(self)
            yield 3

        # ----------------------------------------------------------------------

        l = list(Func())

        self.assertEqual(len(l), 3)
        self.assertEqual(l[0], 1)
        self.assertTrue("SelfGenerator.SelfGenerator" in l[1])
        self.assertEqual(l[2], 3)

    # ----------------------------------------------------------------------
    def test_DocstringExample(self):
        # ----------------------------------------------------------------------
        @SelfGenerator
        def A(self):
            while True:
                message = yield
                yield self is message
                yield self is message

        # ----------------------------------------------------------------------

        a = A()
        b = A()

        next(a)

        self.assertEqual(a.send(a), True)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
