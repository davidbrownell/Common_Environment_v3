# ----------------------------------------------------------------------
# |  
# |  Visitor_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 13:30:18
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for Visitor.py."""

import os
import sys
import unittest

from CommonEnvironment import Nonlocals

from CommonEnvironment.TypeInfo.FundamentalTypes.All import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Visitor import CreateSimpleVisitor

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        nonlocals = Nonlocals( onBool=0,
                               onDateTime=0,
                               onDate=0,
                               onDirectory=0,
                               onDuration=0,
                               onEnum=0,
                               onFilename=0,
                               onFloat=0,
                               onGuid=0,
                               onInt=0,
                               onString=0,
                               onTime=0,
                               onUri=0,
                             )

        # ----------------------------------------------------------------------
        def Update(attr):
            setattr(nonlocals, attr, getattr(nonlocals, attr) + 1)

        # ----------------------------------------------------------------------

        attributes = [ "onBool",
                       "onDateTime",
                       "onDate",
                       "onDirectory",
                       "onDuration",
                       "onEnum",
                       "onFilename",
                       "onFloat",
                       "onGuid",
                       "onInt",
                       "onString",
                       "onTime",
                       "onUri",
                     ]

        params = [ lambda ti, attr=attr: Update(attr) for attr in attributes ]
                  
        visitor = CreateSimpleVisitor(*params)

        visitor.Accept(BoolTypeInfo())
        visitor.Accept(DateTimeTypeInfo())
        visitor.Accept(DateTypeInfo())
        visitor.Accept(DirectoryTypeInfo())
        visitor.Accept(DurationTypeInfo())
        visitor.Accept(EnumTypeInfo([ "one", ]))
        visitor.Accept(FilenameTypeInfo())
        visitor.Accept(FloatTypeInfo())
        visitor.Accept(GuidTypeInfo())
        visitor.Accept(IntTypeInfo())
        visitor.Accept(StringTypeInfo())
        visitor.Accept(TimeTypeInfo())
        visitor.Accept(UriTypeInfo())

        for attr in attributes:
            self.assertEqual(getattr(nonlocals, attr), 1, attr)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
