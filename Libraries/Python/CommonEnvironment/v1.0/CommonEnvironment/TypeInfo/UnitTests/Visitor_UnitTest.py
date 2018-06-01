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
        nonlocals = Nonlocals( on_any_of=0,
                               on_class=0,
                               on_method=0,
                               on_class_method=0,
                               on_static_method=0,
                               on_dict=0,
                               on_list=0,
                               
                               on_bool=0,
                               on_string=0,
                             )

        # ----------------------------------------------------------------------
        def Update(attr):
            setattr(nonlocals, attr, getattr(nonlocals, attr) + 1)

        # ----------------------------------------------------------------------

        attributes = [ "on_any_of",
                       "on_class",
                       "on_method",
                       "on_class_method",
                       "on_static_method",
                       "on_dict",
                       "on_list",
                       "on_bool",
                       "on_string",
                     ]

        params = { "{}_func".format(attr) : lambda ti, attr=attr: Update(attr) for attr in attributes }

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