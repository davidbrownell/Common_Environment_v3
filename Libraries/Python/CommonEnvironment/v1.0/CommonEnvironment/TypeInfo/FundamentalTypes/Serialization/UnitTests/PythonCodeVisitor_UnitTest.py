# ----------------------------------------------------------------------
# |  
# |  PythonCodeVisitor_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-15 14:12:49
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for PythonCodeVisitor.py"""

import os
import sys
import unittest

from CommonEnvironment.TypeInfo import Arity
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.PythonCodeVisitor import PythonCodeVisitor

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Arity(self):
        # Use BoolTypeInfo to validate
        self.assertEqual(PythonCodeVisitor().Accept(BoolTypeInfo()), "BoolTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(BoolTypeInfo(arity=Arity.FromString('?'))), "BoolTypeInfo(arity=Arity.FromString('?'))")
        self.assertEqual(PythonCodeVisitor().Accept(BoolTypeInfo(arity=Arity.FromString('+'))), "BoolTypeInfo(arity=Arity.FromString('+'))")
        self.assertEqual(PythonCodeVisitor().Accept(BoolTypeInfo(arity=Arity.FromString('*'))), "BoolTypeInfo(arity=Arity.FromString('*'))")
        self.assertEqual(PythonCodeVisitor().Accept(BoolTypeInfo(arity=Arity(2, 2))), "BoolTypeInfo(arity=Arity(2,2))")
        self.assertEqual(PythonCodeVisitor().Accept(BoolTypeInfo(arity=Arity(1, 20))), "BoolTypeInfo(arity=Arity(1,20))")
        self.assertEqual(PythonCodeVisitor().Accept(BoolTypeInfo(arity=Arity(5, None))), "BoolTypeInfo(arity=Arity(5,None))")

    # ----------------------------------------------------------------------
    def test_Bool(self):
        self.assertEqual(PythonCodeVisitor().Accept(BoolTypeInfo()), "BoolTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(BoolTypeInfo(arity=Arity.FromString('?'))), "BoolTypeInfo(arity=Arity.FromString('?'))")
        
    # ----------------------------------------------------------------------
    def test_DateTime(self):
        self.assertEqual(PythonCodeVisitor().Accept(DateTimeTypeInfo()), "DateTimeTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(DateTimeTypeInfo(arity=Arity.FromString('?'))), "DateTimeTypeInfo(arity=Arity.FromString('?'))")

    # ----------------------------------------------------------------------
    def test_Date(self):
        self.assertEqual(PythonCodeVisitor().Accept(DateTypeInfo()), "DateTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(DateTypeInfo(arity=Arity.FromString('?'))), "DateTypeInfo(arity=Arity.FromString('?'))")

    # ----------------------------------------------------------------------
    def test_Directory(self):
        self.assertEqual(PythonCodeVisitor().Accept(DirectoryTypeInfo()), "DirectoryTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(DirectoryTypeInfo(ensure_exists=False)), "DirectoryTypeInfo(ensure_exists=False)")
        self.assertEqual(PythonCodeVisitor().Accept(DirectoryTypeInfo(validation_expression='.+')), "DirectoryTypeInfo(validation_expression='.+')")
        self.assertEqual(PythonCodeVisitor().Accept(DirectoryTypeInfo(ensure_exists=False, validation_expression='.+')), "DirectoryTypeInfo(ensure_exists=False, validation_expression='.+')")
        self.assertEqual(PythonCodeVisitor().Accept(DirectoryTypeInfo(ensure_exists=False, validation_expression='.+', arity=Arity.FromString('?'))), "DirectoryTypeInfo(ensure_exists=False, validation_expression='.+', arity=Arity.FromString('?'))")

    # ----------------------------------------------------------------------
    def test_Duration(self):
        self.assertEqual(PythonCodeVisitor().Accept(DurationTypeInfo()), "DurationTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(DurationTypeInfo(arity=Arity.FromString('?'))), "DurationTypeInfo(arity=Arity.FromString('?'))")

    # ----------------------------------------------------------------------
    def test_Enum(self):
        self.assertEqual(PythonCodeVisitor().Accept(EnumTypeInfo([ "1", "too", "three", ])), "EnumTypeInfo([ '1', 'too', 'three', ])")
        self.assertEqual(PythonCodeVisitor().Accept(EnumTypeInfo([ "1", "too", "three", ], [ "a", "b", "c", ])), "EnumTypeInfo([ '1', 'too', 'three', ], [ 'a', 'b', 'c', ])")
        self.assertEqual(PythonCodeVisitor().Accept(EnumTypeInfo([ "1", "too", "three", ], [ "a", "b", "c", ], arity=Arity.FromString('?'))), "EnumTypeInfo([ '1', 'too', 'three', ], [ 'a', 'b', 'c', ], arity=Arity.FromString('?'))")

    # ----------------------------------------------------------------------
    def test_Filename(self):
        self.assertEqual(PythonCodeVisitor().Accept(FilenameTypeInfo()), "FilenameTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(FilenameTypeInfo(ensure_exists=False)), "FilenameTypeInfo(ensure_exists=False)")
        self.assertEqual(PythonCodeVisitor().Accept(FilenameTypeInfo(ensure_exists=False, validation_expression=".+")), "FilenameTypeInfo(ensure_exists=False, validation_expression='.+')")
        self.assertEqual(PythonCodeVisitor().Accept(FilenameTypeInfo(ensure_exists=False, match_any=True, validation_expression=".+")), "FilenameTypeInfo(ensure_exists=False, match_any=True, validation_expression='.+')")
        self.assertEqual(PythonCodeVisitor().Accept(FilenameTypeInfo(ensure_exists=False, match_any=True, validation_expression=".+", arity=Arity.FromString('?'))), "FilenameTypeInfo(ensure_exists=False, match_any=True, validation_expression='.+', arity=Arity.FromString('?'))")

    # ----------------------------------------------------------------------
    def test_Float(self):
        self.assertEqual(PythonCodeVisitor().Accept(FloatTypeInfo()), "FloatTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(FloatTypeInfo(min=1.0)), "FloatTypeInfo(min=1.0)")
        self.assertEqual(PythonCodeVisitor().Accept(FloatTypeInfo(min=1.0, max=2.0)), "FloatTypeInfo(min=1.0, max=2.0)")
        self.assertEqual(PythonCodeVisitor().Accept(FloatTypeInfo(min=1.0, max=2.0, arity=Arity.FromString('?'))), "FloatTypeInfo(min=1.0, max=2.0, arity=Arity.FromString('?'))")

    # ----------------------------------------------------------------------
    def test_Guid(self):
        self.assertEqual(PythonCodeVisitor().Accept(GuidTypeInfo()), "GuidTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(GuidTypeInfo(arity=Arity.FromString('?'))), "GuidTypeInfo(arity=Arity.FromString('?'))")

    # ----------------------------------------------------------------------
    def test_Int(self):
        self.assertEqual(PythonCodeVisitor().Accept(IntTypeInfo()), "IntTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(IntTypeInfo(min=5)), "IntTypeInfo(min=5)")
        self.assertEqual(PythonCodeVisitor().Accept(IntTypeInfo(min=5, max=10)), "IntTypeInfo(min=5, max=10)")
        self.assertEqual(PythonCodeVisitor().Accept(IntTypeInfo(min=5, max=10, bytes=4)), "IntTypeInfo(min=5, max=10, bytes=4)")
        self.assertEqual(PythonCodeVisitor().Accept(IntTypeInfo(min=5, max=10, bytes=4)), "IntTypeInfo(min=5, max=10, bytes=4)")
        self.assertEqual(PythonCodeVisitor().Accept(IntTypeInfo(unsigned=True, arity=Arity.FromString('?'))), "IntTypeInfo(min=0, arity=Arity.FromString('?'))")

    # ----------------------------------------------------------------------
    def test_String(self):
        self.assertEqual(PythonCodeVisitor().Accept(StringTypeInfo()), "StringTypeInfo(min_length=1)")
        self.assertEqual(PythonCodeVisitor().Accept(StringTypeInfo(validation_expression=".+")), "StringTypeInfo(validation_expression='.+')")
        self.assertEqual(PythonCodeVisitor().Accept(StringTypeInfo(max_length=10)), "StringTypeInfo(min_length=1, max_length=10)")
        self.assertEqual(PythonCodeVisitor().Accept(StringTypeInfo(max_length=10, arity=Arity.FromString('?'))), "StringTypeInfo(min_length=1, max_length=10, arity=Arity.FromString('?'))")

    # ----------------------------------------------------------------------
    def test_Time(self):
        self.assertEqual(PythonCodeVisitor().Accept(TimeTypeInfo()), "TimeTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(TimeTypeInfo(arity=Arity.FromString('?'))), "TimeTypeInfo(arity=Arity.FromString('?'))")

    # ----------------------------------------------------------------------
    def test_Uri(self):
        self.assertEqual(PythonCodeVisitor().Accept(UriTypeInfo()), "UriTypeInfo()")
        self.assertEqual(PythonCodeVisitor().Accept(UriTypeInfo(arity=Arity.FromString('?'))), "UriTypeInfo(arity=Arity.FromString('?'))")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass