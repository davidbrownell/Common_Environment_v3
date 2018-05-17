# ----------------------------------------------------------------------
# |  
# |  __init___UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-30 21:05:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for __init__.py."""

import os
import sys
import unittest

from CommonEnvironment.Shell.Commands import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):
    def test_Standard(self):
        # Nothing much to test, other than the creation of each object
        self.assertTrue(True)

        Comment("comment")
        Message("message")
        Call("command line")
        Execute("command line")
        SymbolicLink("link", "target")
        Path("path")
        AugmentPath("path")
        Set("name", "value")
        Augment("name", "value")
        Exit()
        ExitOnError()
        Raw("raw")
        EchoOff()
        CommandPrompt("prompt")
        Delete("filename")
        Copy("source", "dest")
        Move("source", "dest")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass