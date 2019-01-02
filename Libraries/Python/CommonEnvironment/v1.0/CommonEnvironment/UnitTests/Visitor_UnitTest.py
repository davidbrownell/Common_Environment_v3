# ----------------------------------------------------------------------
# |  
# |  Visitor_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-11-09 16:38:00
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for Visitor.py."""

import os
import sys
import unittest

import CommonEnvironment
from CommonEnvironment.Visitor import *
from CommonEnvironment.Interface import override, staticderived, abstractmethod

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class MyVisitorInterface(Visitor):
     # All methods are static

     @staticmethod
     @abstractmethod
     def OnOdd(value, *args, **kwargs):
         raise Exception("Abstract method")

     @staticmethod
     @abstractmethod
     def OnEven(value, *args, **kwargs):
         raise Exception("Abstract method")

     @classmethod
     def Accept(cls, value, *args, **kwargs):
         if value & 1:
             return cls.OnOdd(value, *args, **kwargs)
         
         return cls.OnEven(value, *args, **kwargs)

@staticderived
class MyStaticVisitor(MyVisitorInterface):
    @staticmethod
    @override
    def OnOdd(value):
        return "Static - Odd: {}".format(value)

    @staticmethod
    @override
    def OnEven(value):
        return "Static - Even: {}".format(value)

class MyVisitor(MyVisitorInterface):
    def __init__(self, factor):
        self._factor                = factor

    @override
    def OnOdd(self, value):
        return "Odd: {}".format(value * self._factor)

    @override
    def OnEven(self, value):
        return "Even: {}".format(value * self._factor)

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_Static(self):
        self.assertEqual(MyStaticVisitor.Accept(11), "Static - Odd: 11")
        self.assertEqual(MyStaticVisitor.Accept(10), "Static - Even: 10")

    # ----------------------------------------------------------------------
    def test_Instance(self):
        v = MyVisitor(100)

        self.assertEqual(v.Accept(11), "Odd: 1100")
        self.assertEqual(v.Accept(10), "Even: 1000")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
