# ----------------------------------------------------------------------
# |  
# |  Visitor_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-30 19:18:51
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for CommandVisitor.py"""

import os
import sys
import unittest

from CommonEnvironment import Nonlocals

from CommonEnvironment.Shell.Commands import *
from CommonEnvironment.Shell.Commands.Visitor import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        nonlocals = Nonlocals( onComment=0,
                               onMessage=0,
                               onCall=0,
                               onExecute=0,
                               onSymbolicLink=0,
                               onPath=0,
                               onAugmentedPath=0,
                               onSet=0,
                               onAugmented=0,
                               onExit=0,
                               onExitOnError=0,
                               onRaw=0,
                               onEchoOff=0,
                               onCommandPrompt=0,
                               onDelete=0,
                               onCopy=0,
                               onMove=0,
                             )

        # ----------------------------------------------------------------------
        def Update(attr):
            setattr(nonlocals, attr, getattr(nonlocals, attr) + 1)

        # ----------------------------------------------------------------------

        attributes = [ "onComment",
                       "onMessage",
                       "onCall",
                       "onExecute",
                       "onSymbolicLink",
                       "onPath",
                       "onAugmentedPath",
                       "onSet",
                       "onAugmented",
                       "onExit",
                       "onExitOnError",
                       "onRaw",
                       "onEchoOff",
                       "onCommandPrompt",
                       "onDelete",
                       "onCopy",
                       "onMove",
                     ]

        params = [ lambda command, attr=attr: Update(attr) for attr in attributes ]

        visitor = CreateSimpleVisitor(*params)

        visitor.Accept(Comment("foo"))
        visitor.Accept(Message("bar"))
        visitor.Accept(Call("command line"))
        visitor.Accept(Execute("command line"))
        visitor.Accept(SymbolicLink("link", "target", False))
        visitor.Accept(Path("path", True))
        visitor.Accept(AugmentPath("path"))
        visitor.Accept(Set("name", "value", True))
        visitor.Accept(Augment("name", "value"))
        visitor.Accept(Exit(False, False, 0))
        visitor.Accept(ExitOnError(-1))
        visitor.Accept(Raw("string"))
        visitor.Accept(EchoOff())
        visitor.Accept(CommandPrompt("foo"))
        visitor.Accept(Delete("filename"))
        visitor.Accept(Copy("source", "dest"))
        visitor.Accept(Move("source", "dest"))

        for attr in attributes:
            self.assertEqual(getattr(nonlocals, attr), 1)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass