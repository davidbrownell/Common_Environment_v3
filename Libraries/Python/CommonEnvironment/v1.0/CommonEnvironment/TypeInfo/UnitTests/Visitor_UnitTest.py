# ----------------------------------------------------------------------
# |  
# |  Visitor_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 21:42:29
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

from CommonEnvironment.TypeInfo.All import *
from CommonEnvironment.TypeInfo.Visitor import CreateSimpleVisitor

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        nonlocals = Nonlocals( onAnyOf=0,
                               onClass=0,
                               onMethod=0,
                               onClassMethod=0,
                               onStaticMethod=0,
                               onDict=0,
                               onList=0,
                               
                               onBool=0,
                               onString=0,
                             )

        # ----------------------------------------------------------------------
        def Update(attr):
            setattr(nonlocals, attr, getattr(nonlocals, attr) + 1)

        # ----------------------------------------------------------------------

        attributes = [ "onAnyOf",
                       "onClass",
                       "onMethod",
                       "onClassMethod",
                       "onStaticMethod",
                       "onDict",
                       "onList",
                       "onBool",
                       "onString",
                     ]

        params = { "{}Func".format(attr) : lambda ti, attr=attr: Update(attr) for attr in attributes }

        visitor = CreateSimpleVisitor(**params)

        visitor.Accept(AnyOfTypeInfo([ StringTypeInfo(), ]))
        visitor.Accept(ClassTypeInfo(a=StringTypeInfo()))
        visitor.Accept(MethodTypeInfo())
        visitor.Accept(ClassMethodTypeInfo())
        visitor.Accept(StaticMethodTypeInfo())
        visitor.Accept(DictTypeInfo(a=StringTypeInfo()))
        visitor.Accept(ListTypeInfo([ StringTypeInfo() ]))

        visitor.Accept(BoolTypeInfo())
        visitor.Accept(StringTypeInfo())

        for attr in attributes:
            self.assertEqual(getattr(nonlocals, attr), 1)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass