# ----------------------------------------------------------------------
# |  
# |  All_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-11 07:56:41
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for All.py."""

import os
import sys
import unittest

from CommonEnvironment.Shell.Commands.All import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):
    def test_Standard(self):
        self.assertNotEqual(len(ALL_COMMANDS), 0)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass