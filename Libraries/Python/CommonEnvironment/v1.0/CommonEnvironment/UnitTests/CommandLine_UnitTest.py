# ----------------------------------------------------------------------
# |  
# |  CommandLine_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-29 09:37:24
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit tests for CommandLine.py."""

import os
import sys
import unittest

from CommonEnvironment.CommandLine import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@EntryPoint
@Constraints( a=StringTypeInfo(),
              b=IntTypeInfo(min=1),
              c=IntTypeInfo(arity='?') # BugBug: This should be an issue and detected within CommandLine
            )
def Method1(a, b, c=None):
    print("BugBug!!!!!", a, b)
    pass

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def setUp(self):
        self.executor = Executor([ "<ScriptName>", "foo", ]) # BugBug "10", ])

    # ----------------------------------------------------------------------
    def test_NoArgs(self):
        self.executor.Invoke( verbose=True,
                            )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass