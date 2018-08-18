# ----------------------------------------------------------------------
# |  
# |  __init___UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 09:50:29
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for __init__.py"""

import os
import sys
import unittest

from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.TypeInfo import Arity, TypeInfo, ValidationException

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class AritySuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_FromString(self):
        self.assertEqual(Arity.FromString('?'), Arity(0, 1))
        self.assertEqual(Arity.FromString('1'), Arity(1, 1))
        self.assertEqual(Arity.FromString('*'), Arity(0, None))
        self.assertEqual(Arity.FromString('+'), Arity(1, None))
        self.assertEqual(Arity.FromString('{3}'), Arity(3, 3))
        self.assertEqual(Arity.FromString('{3,4}'), Arity(3, 4))

    # ----------------------------------------------------------------------
    def test_InvalidConstruction(self):
        self.assertRaises(Exception, lambda: Arity(None, None))
        self.assertRaises(Exception, lambda: Arity(-1, None))
        self.assertRaises(Exception, lambda: Arity(5, 4))

    # ----------------------------------------------------------------------
    def test_Str(self):
        self.assertEqual(str(Arity(1, 2)), "Arity(1, 2)")
        self.assertEqual(str(Arity(2, 2)), "Arity(2, 2)")
        self.assertEqual(str(Arity(1, None)), "Arity(1, None)")

    # ----------------------------------------------------------------------
    def test_IsMethods(self):
        # ----------------------------------------------------------------------
        def Test( arity,
                  is_single=False,
                  is_optional=False,
                  is_collection=False,
                  is_optional_collection=False,
                  is_fixed_collection=False,
                  is_zero_or_more=False,
                  is_one_or_more=False,
                  is_range=False,
                ):
            self.assertEqual(arity.IsSingle, is_single)
            self.assertEqual(arity.IsOptional, is_optional)
            self.assertEqual(arity.IsCollection, is_collection)
            self.assertEqual(arity.IsOptionalCollection, is_optional_collection)
            self.assertEqual(arity.IsFixedCollection, is_fixed_collection)
            self.assertEqual(arity.IsZeroOrMore, is_zero_or_more)
            self.assertEqual(arity.IsOneOrMore, is_one_or_more)
            self.assertEqual(arity.IsRange, is_range)

        # ----------------------------------------------------------------------

        Test(Arity(1, 1), is_single=True)
        Test(Arity(0, 1), is_optional=True)
        Test(Arity(3, 5), is_collection=True, is_range=True)
        Test(Arity(0, 5), is_collection=True, is_optional_collection=True, is_range=True)
        Test(Arity(0, None), is_collection=True, is_optional_collection=True, is_zero_or_more=True)
        Test(Arity(4, 4), is_collection=True, is_fixed_collection=True)
        Test(Arity(1, 5),is_collection=True, is_range=True)

    # ----------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(Arity(0, 1).ToString(), "?")
        self.assertEqual(Arity(1, 1).ToString(), "")
        self.assertEqual(Arity(0, None).ToString(), "*")
        self.assertEqual(Arity(1, None).ToString(), "+")
        self.assertEqual(Arity(2, 2).ToString(), "{2}")
        self.assertEqual(Arity(2, 4).ToString(), "{2,4}")
        self.assertEqual(Arity(2, 4).ToString(('[', ']')), "[2,4]")

    # ----------------------------------------------------------------------
    def test_Equal(self):
        self.assertEqual(Arity(0, None), Arity.FromString('*'))
        self.assertTrue(Arity(0, None) != Arity.FromString('+'))

    # ----------------------------------------------------------------------
    def test_LessThan(self):
        self.assertTrue(Arity(1, 1) < 4)
        self.assertTrue(Arity(1, 1000) < Arity(2, 100))
        self.assertTrue(Arity(1, 1000) < Arity(1, None))
        self.assertTrue(Arity(1, 100) < Arity(1, 200))

# ----------------------------------------------------------------------
class TypeInfoSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    @staticderived
    class TeenTypeInfo(TypeInfo):
        Desc                                = DerivedProperty("A number that is in the teens")
        ConstraintsDesc                     = DerivedProperty("13 <= value <= 19")
        ExpectedType                        = int 

        @staticmethod
        @override
        def _ValidateItemNoThrowImpl(item, **custom_args):
            if item < 13: return "item < 13"
            if item > 19: return "item > 19"

    # ----------------------------------------------------------------------
    def test_Construct(self):
        self.TeenTypeInfo(Arity(1, 1))
        self.TeenTypeInfo('?')
        self.assertRaises(Exception, lambda: self.TeenTypeInfo(Arity(1, 1), collection_validation_func=lambda items: None))
            
    # ----------------------------------------------------------------------
    def test_IsExpectedType(self):
        self.assertTrue(self.TeenTypeInfo().IsExpectedType(10))
        self.assertFalse(self.TeenTypeInfo().IsExpectedType("bad type"))

    # ----------------------------------------------------------------------
    def test_IsValid(self):
        self.assertTrue(self.TeenTypeInfo().IsValid(13))
        self.assertTrue(self.TeenTypeInfo('*').IsValid([]))
        self.assertTrue(self.TeenTypeInfo('*').IsValid([ 14, ]))

        self.assertFalse(self.TeenTypeInfo().IsValid(10))
        self.assertFalse(self.TeenTypeInfo().IsValid(20))
        self.assertFalse(self.TeenTypeInfo('*').IsValid(13))
        self.assertFalse(self.TeenTypeInfo('*').IsValid([ 10, ]))

    # ----------------------------------------------------------------------
    def test_IsValidItem(self):
        self.assertTrue(self.TeenTypeInfo().IsValidItem(15))
        self.assertTrue(self.TeenTypeInfo('*').IsValidItem(15))

        self.assertFalse(self.TeenTypeInfo().IsValidItem(10))
        self.assertFalse(self.TeenTypeInfo('*').IsValidItem(20))

    # ----------------------------------------------------------------------
    def test_IsValidArity(self):
        self.assertTrue(self.TeenTypeInfo().IsValidArity(10))
        self.assertTrue(self.TeenTypeInfo('*').IsValidArity([]))
        self.assertTrue(self.TeenTypeInfo('*').IsValidArity([ 13, ]))
        self.assertTrue(self.TeenTypeInfo('?').IsValidArity(None))
        self.assertTrue(self.TeenTypeInfo('?').IsValidArity(13))

        self.assertFalse(self.TeenTypeInfo().IsValidArity(None))
        self.assertFalse(self.TeenTypeInfo().IsValidArity([ 13, ]))
        self.assertFalse(self.TeenTypeInfo('*').IsValidArity(13))
        self.assertFalse(self.TeenTypeInfo('{2}').IsValidArity([ 13, ]))

    # ----------------------------------------------------------------------
    def test_Validate(self):
        self.TeenTypeInfo().Validate(13)
        self.TeenTypeInfo('{2}').Validate([ 13, 15, ])
        self.TeenTypeInfo('?').Validate(None)
        self.TeenTypeInfo('?').Validate(16)

        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo().Validate(10))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo().Validate("string"))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo().Validate(None))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo().Validate([ 14, ]))

        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo('?').Validate([ 17, ]))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo('{2}').Validate(17))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo('{2}').Validate([ 17, ]))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo('{2}').Validate([ 17, 10, ]))

    # ----------------------------------------------------------------------
    def test_ValidateItem(self):
        self.TeenTypeInfo().ValidateItem(16)
        self.TeenTypeInfo('*').ValidateItem(17)
        self.TeenTypeInfo('?').ValidateItem(None)
        self.TeenTypeInfo('?').ValidateItem(19)

        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo().ValidateItem(12))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo().ValidateItem(None))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo().ValidateItem(12))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo('?').ValidateItem(12))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo('{2}').ValidateItem([ 13, 14, ]))
        
    # ----------------------------------------------------------------------
    def test_ValidateArity(self):
        self.TeenTypeInfo().ValidateArity(14)
        self.TeenTypeInfo('{3}').ValidateArity([ 13, 14, 15 ])
        self.TeenTypeInfo('?').ValidateArity(None)

        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo().ValidateArity([ 13, ]))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo('?').ValidateArity([ 13, ]))
        self.assertRaises(ValidationException, lambda: self.TeenTypeInfo('{2}').ValidateArity([ 13, ]))

    # ----------------------------------------------------------------------
    # TypeInfo.ValidateNoThrow is covered by the previous tests
    # TypeInfo.ValidateItemNoThrow is covered by the previous tests
    # TypeInfo.ValidateArityNoThrow is covered by the previous tests

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass