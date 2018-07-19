# ----------------------------------------------------------------------
# |  
# |  ClassTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 20:25:18
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for ClassTypeInfo.py"""

import os
import sys
import unittest

from CommonEnvironment.TypeInfo.ClassTypeInfo import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Object(object):
    def Method(self): pass

    @classmethod
    def ClassMethod(cls): pass

    @staticmethod
    def StaticMethod(): pass

    
# ----------------------------------------------------------------------
class MethodSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_MethodTypeInfo(self):
        ti = MethodTypeInfo()

        self.assertEqual(ti.Desc, "Method")
        self.assertEqual(ti.ConstraintsDesc, '')
        self.assertEqual(ti.ExpectedTypeIsCallable, True)
        self.assertTrue(ti.IsValidItem(Object.Method))
        self.assertFalse(ti.IsValidItem(Object.ClassMethod))
        self.assertFalse(ti.IsValidItem(Object.StaticMethod))

    # ----------------------------------------------------------------------
    def test_ClassMethodTypeInfo(self):
        ti = ClassMethodTypeInfo()

        self.assertEqual(ti.Desc, "Class Method")
        self.assertEqual(ti.ConstraintsDesc, '')
        self.assertEqual(ti.ExpectedTypeIsCallable, True)
        self.assertFalse(ti.IsValidItem(Object.Method))
        self.assertTrue(ti.IsValidItem(Object.ClassMethod))
        self.assertFalse(ti.IsValidItem(Object.StaticMethod))

    # ----------------------------------------------------------------------
    def test_StaticMethodTypeInfo(self):
        ti = StaticMethodTypeInfo()

        self.assertEqual(ti.Desc, "Static Method")
        self.assertEqual(ti.ConstraintsDesc, '')
        self.assertEqual(ti.ExpectedTypeIsCallable, True)
        self.assertFalse(ti.IsValidItem(Object.Method))
        self.assertFalse(ti.IsValidItem(Object.ClassMethod))
        self.assertTrue(ti.IsValidItem(Object.StaticMethod))

# ----------------------------------------------------------------------
class ClassTypeInfoSuite(unittest.TestCase):
    def test_Standard(self):
        ti = ClassTypeInfo( Method=MethodTypeInfo(),
                            ClassMethod=ClassMethodTypeInfo(),
                            StaticMethod=StaticMethodTypeInfo(),
                          )

        self.assertEqual(ti.Desc, "Class")

        if sys.version[0] == '2':
            # Python2 returns items in alpha order
            self.assertEqual(ti.ConstraintsDesc, "Value must contain the attributes 'ClassMethod' <Class Method>, 'StaticMethod' <Static Method>, 'Method' <Method>")
        else:
            # Python3 returns item in declared order
            self.assertEqual(ti.ConstraintsDesc, "Value must contain the attributes 'Method' <Method>, 'ClassMethod' <Class Method>, 'StaticMethod' <Static Method>")

        self.assertTrue(ti.ExpectedTypeIsCallable)
        self.assertTrue(ti.IsExpectedType(Object))
        self.assertTrue(ti.IsValidItem(Object()))

        class Object2(Object):
            def AnotherMethod(self): pass

        self.assertFalse(ti.IsValidItem(Object2()))
        self.assertTrue(ti.IsValidItem(Object2(), require_exact_match=False))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass