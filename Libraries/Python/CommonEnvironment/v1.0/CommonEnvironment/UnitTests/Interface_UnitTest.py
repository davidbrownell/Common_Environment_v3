# ----------------------------------------------------------------------
# |  
# |  Interface_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-21 19:24:20
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit tst for Interface.py"""

import os
import sys
import unittest

import CommonEnvironment
from CommonEnvironment.Interface import *

# ----------------------------------------------------------------------
class InterfaceSuite(unittest.TestCase):
    # # ----------------------------------------------------------------------
    # def assertRaises(self, exception, func, *args, **kwargs):
    #     try:
    #         func(*args, **kwargs)
    #         self.fail()
    #     except exception as ex:
    #         print("\n", ex)
    #         self.assertTrue(True)

    # ----------------------------------------------------------------------
    class MyIterface(Interface):
        @abstractproperty
        def Property(self): pass

        @abstractmethod
        def Method(self, a, b): pass

        @staticmethod
        @abstractmethod
        def StaticMethod(a, b, c=None): pass

        @classmethod
        @abstractmethod
        def ClassMethod(cls, a, b): pass

    # ----------------------------------------------------------------------
    def test_Valid(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): return 10

            @override
            def Method(self, a, b): pass

            @staticmethod
            @override
            def StaticMethod(a, b, c=None): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b): pass

        # ----------------------------------------------------------------------

        MyObject();
        self.assertEqual(MyObject().Property, 10);

    # ----------------------------------------------------------------------
    def test_MissingProperty(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @override
            def Method(self, a, b): pass
    
            @staticmethod
            @override
            def StaticMethod(a, b, c=None): pass
    
            @classmethod
            @override
            def ClassMethod(cls, a, b): pass
    
        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)

    # ----------------------------------------------------------------------
    def test_MissingMethod(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @staticmethod
            @override
            def StaticMethod(a, b, c=None): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b): pass

        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)
        
    # ----------------------------------------------------------------------
    def test_MissingStaticMethod(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @override
            def Method(self, a, b): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b): pass

        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)
        
    # ----------------------------------------------------------------------
    def test_MissingClassMethod(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @override
            def Method(self, a, b): pass

            @staticmethod
            @override
            def StaticMethod(a, b, c=None): pass

        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)
        
    # ----------------------------------------------------------------------
    def test_AllMethods(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @override
            def Method(self, a, b): pass

            @override
            def StaticMethod(self, a, b, c=None): pass

            @override
            def ClassMethod(cls, a, b): pass

        # ----------------------------------------------------------------------

        MyObject()
        self.assertTrue(True)

    # ----------------------------------------------------------------------
    def test_AllStaticMethods(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @staticmethod
            @override
            def Method(a, b): pass

            @staticmethod
            @override
            def StaticMethod(a, b, c=None): pass

            @staticmethod
            @override
            def ClassMethod(a, b): pass

        # ----------------------------------------------------------------------

        MyObject()
        self.assertTrue(True)
        
    # ----------------------------------------------------------------------
    def test_AllClassMethods(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @classmethod
            @override
            def Method(cls, a, b): pass

            @classmethod
            @override
            def StaticMethod(cls, a, b, c=None): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b): pass

        # ----------------------------------------------------------------------

        MyObject()
        self.assertTrue(True)

    # ----------------------------------------------------------------------
    def test_ForwardingFuncs(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @override
            def Method(self, *args, **kwargs): pass

            @staticmethod
            @override
            def StaticMethod(*args, **kwargs): pass

            @classmethod
            @override
            def ClassMethod(cls, *args, **kwargs): pass

        # ----------------------------------------------------------------------

        MyObject()
        self.assertTrue(True)

    # ----------------------------------------------------------------------
    def test_InvalidMethodParam(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @override
            def Method(self, a_, b): pass

            @staticmethod
            @override
            def StaticMethod(a, b, c=None): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b): pass

        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)
        
    # ----------------------------------------------------------------------
    def test_InvalidStaticMethodParam(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @override
            def Method(self, a, b): pass

            @staticmethod
            @override
            def StaticMethod(a, _b, c=None): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b): pass

        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)
        
    # ----------------------------------------------------------------------
    def test_InvalidClassMethodParam(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @override
            def Method(self, a, b): pass

            @staticmethod
            @override
            def StaticMethod(a, b, c=None): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b_): pass

        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)

    # ----------------------------------------------------------------------
    def test_InvalidDefaultType(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @override
            def Method(self, a, b): pass

            @staticmethod
            @override
            def StaticMethod(a, b, c=int): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b): pass

        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)

    # ----------------------------------------------------------------------
    def test_ExtractDefaults(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @override
            def Method(self, a, b, c=None): pass

            @staticmethod
            @override
            def StaticMethod(a, b, c=None, d=10): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b, c="a string"): pass

        # ----------------------------------------------------------------------

        MyObject()
        self.assertTrue(True)

    # ----------------------------------------------------------------------
    def test_InvalidPropertyType(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @override
            def Property(self, a): pass

            @override
            def Method(self, a, b): pass

            @staticmethod
            @override
            def StaticMethod(a, b, c=None): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b): pass

        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)

    # ----------------------------------------------------------------------
    def test_InvalidMethodType(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @property
            @override
            def Method(self): pass

            @staticmethod
            @override
            def StaticMethod(a, b, c=None): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b): pass

        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)

    # ----------------------------------------------------------------------
    def test_InvlidStaticMethodType(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @override
            def Method(self, a, b): pass

            @property
            @override
            def StaticMethod(self): pass

            @classmethod
            @override
            def ClassMethod(cls, a, b): pass

        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)

    # ----------------------------------------------------------------------
    def test_InvalidClassMethodType(self):
        # ----------------------------------------------------------------------
        class MyObject(self.MyIterface):
            @property
            @override
            def Property(self): pass

            @override
            def Method(self, a, b): pass

            @staticmethod
            @override
            def StaticMethod(a, b, c=None): pass

            @property
            @override
            def ClassMethod(self): pass

        # ----------------------------------------------------------------------

        self.assertRaises(InterfaceException, MyObject)

# ----------------------------------------------------------------------
class ExtensionMethodSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    class Base(Interface):
        def Method1(self): pass

        @extensionmethod
        def ExtensionMethod(self): pass

        @staticmethod
        @extensionmethod
        def StaticExtensionMethod(self): pass

        @classmethod
        @extensionmethod
        def ClassExtensionMethod(self): pass

    # ----------------------------------------------------------------------
    class Derived(Base):
        def Method2(self): pass

        @extensionmethod
        def ExtensionMethod2(self): pass

        @staticmethod
        @extensionmethod
        def StaticExtensionMethod2(self): pass

        @classmethod
        @extensionmethod
        def ClassExtensionMethod2(self): pass

    # ----------------------------------------------------------------------
    def test_Base(self):
        self.assertEqual( list(six.iterkeys(self.Base()._ExtensionItems)),
                          [ "ExtensionMethod",
                            "StaticExtensionMethod",
                            "ClassExtensionMethod",
                          ],
                        )

    # ----------------------------------------------------------------------
    def test_Derived(self):
        self.assertEqual( list(six.iterkeys(self.Derived()._ExtensionItems)),
                          [ "ExtensionMethod",
                            "StaticExtensionMethod",
                            "ClassExtensionMethod",
                            "ExtensionMethod2",
                            "StaticExtensionMethod2",
                            "ClassExtensionMethod2",
                          ],
                        )
        self.assertEqual( self.Derived()._ClassExtensions,
                          [ "ExtensionMethod2",
                            "StaticExtensionMethod2",
                            "ClassExtensionMethod2",
                          ],
                        )

    # ----------------------------------------------------------------------
    def test_Errors(self):
        class Base(Interface):
            @extensionmethod
            def Method(self): pass

        class Derived(Base):
            @override
            def DoesNotExist(self): pass

        self.assertRaises(InterfaceException, lambda: Derived())

        class DoubleOverride(Base):
            @extensionmethod
            def Method(self): pass

        self.assertRaises(InterfaceException, lambda: DoubleOverride())

    # ----------------------------------------------------------------------
    def test_MultipleOverride(self):
        class Base(Interface):
            @staticmethod
            @extensionmethod
            def Method(value): return value

        @staticderived
        class Derived1(Base):
            @classmethod
            @override
            def Method(cls, value) : return super(Derived1, cls).Method(value) * 10

        @staticderived
        class Derived2(Derived1):
            @classmethod
            @override
            def Method(cls, value): return super(Derived2, cls).Method(value) * 20


        self.assertEqual(Derived1.Method(1), 10)
        self.assertEqual(Derived2.Method(1), 200)

# ----------------------------------------------------------------------
class DerivedPropertySuite(unittest.TestCase):

    class Base(Interface):
        @abstractproperty
        def Property(self):
            raise Exception("Abstract Property")

    # ----------------------------------------------------------------------
    def test_Standard(self):
        class DerivedNotSet(self.Base):
            Property                        = DerivedProperty(10)

        self.assertNotEqual(DerivedNotSet.Property, 10)

        @staticderived
        class DerivedSet(self.Base):
            Property                        = DerivedProperty(10)

        self.assertEqual(DerivedSet.Property, 10)

    # ----------------------------------------------------------------------
    def test_MultiDerived(self):
        class Derived1(self.Base):
            Property                        = DerivedProperty(10)

        @staticderived
        class Derived2(Derived1):
            pass

        @staticderived
        class Derived3(Derived1):
            pass

        @staticderived
        class DerivedWithOverride(Derived1):
            Property                        = DerivedProperty(20)
            # Property = 20

        self.assertEqual(Derived3.Property, 10)
        self.assertEqual(Derived2.Property, 10)
        self.assertEqual(Derived1.Property, 10)
        self.assertEqual(DerivedWithOverride.Property, 20)

# ----------------------------------------------------------------------
class StaticDerivedSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    class Base(Interface):
        @staticmethod
        @abstractmethod
        def Method(): 
            return 100

    # ----------------------------------------------------------------------
    def test_Invalid(self):
        # ----------------------------------------------------------------------
        class Derived(self.Base):
            pass

        # ----------------------------------------------------------------------
    
        # This shouldn't be valid, as Base.Method is conceptually abstract
        self.assertEqual(Derived.Method(), 100)

    # ----------------------------------------------------------------------
    def test_Valid(self):
        try:
            # ----------------------------------------------------------------------
            @staticderived
            class Derived(self.Base):
                pass

            # ----------------------------------------------------------------------

            self.fail()
        except InterfaceException:
            self.assertTrue(True)

# ----------------------------------------------------------------------
class MixinSuite(unittest.TestCase):

    class MyInterface(Interface):
        @staticmethod
        @abstractmethod
        def Method1(a): pass

        @staticmethod
        @abstractmethod
        def Method2(a, b): pass

    @mixin
    class Mixin1(Interface):
        @staticmethod
        @override
        def Method1(a): pass

    @mixin
    class Mixin2(Interface):
        @staticmethod
        @override
        def Method2(a, b): pass

    # ----------------------------------------------------------------------
    def test_Valid(self):
        class MyObject(self.Mixin1, self.Mixin2, self.MyInterface):
            pass

        MyObject()

    # ----------------------------------------------------------------------
    def test_MissingMethod(self):
        class MyObject(self.Mixin1, self.MyInterface):
            pass

        self.assertRaises(InterfaceException, MyObject)

    # ----------------------------------------------------------------------
    def test_WrongParams(self):
        class MyObject(self.Mixin1, self.Mixin2, self.MyInterface):
            @staticmethod
            @override
            def Method2(a, b, c): pass

        self.assertRaises(InterfaceException, MyObject)

# ----------------------------------------------------------------------
class ClsInitSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        nonlocals = CommonEnvironment.Nonlocals(value=False)

        # ----------------------------------------------------------------------
        @clsinit
        class Object(object):
            @classmethod
            def __clsinit__(cls):
                nonlocals.value = True

        # ----------------------------------------------------------------------

        self.assertTrue(nonlocals.value)

# ----------------------------------------------------------------------
class TestCreateCulledCallable(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Invoke(self):
        single_arg_func = CreateCulledCallable(lambda a: a)

        self.assertEqual(single_arg_func(OrderedDict([ ( "a", 10 ), 
                                                     ])), 10)
        self.assertEqual(single_arg_func(OrderedDict([ ( "a", 10 ),
                                                       ( "b", 20 ),
                                                     ])), 10)
        self.assertEqual(single_arg_func(OrderedDict([ ( "b", 20 ),
                                                       ( "a", 10 ),
                                                     ])), 10)

        multiple_arg_func = CreateCulledCallable(lambda a, b: ( a, b ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "a", 10 ),
                                                         ( "b", 20 ),
                                                       ])), ( 10, 20 ))
        self.assertEqual(multiple_arg_func(OrderedDict([ ( "a", 10 ),
                                                         ( "b", 20 ),
                                                         ( "c", 30 ),
                                                       ])), ( 10, 20 ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "b", 20 ),
                                                         ( "a", 10 ),
                                                         ( "c", 30 ),
                                                       ])), ( 10, 20 ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "foo", 20 ),
                                                         ( "bar", 10 ),
                                                         ( "baz", 30 ),
                                                       ])), ( 20, 10 ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "foo", 20 ),
                                                         ( "bar", 10 ),
                                                         ( "baz", 30 ),
                                                         ( "a", 1 ),
                                                       ])), ( 1, 20 ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "foo", 20 ),
                                                         ( "bar", 10 ),
                                                         ( "baz", 30 ),
                                                         ( "b", 2 ),
                                                       ])), ( 20, 2 ))

        self.assertEqual(multiple_arg_func(OrderedDict([ ( "foo", 20 ),
                                                         ( "bar", 10 ),
                                                         ( "baz", 30 ),
                                                         ( "b", 2 ),
                                                         ( "a", 1 ),
                                                       ])), ( 1, 2 ))

        with_defaults_func = CreateCulledCallable(lambda a, b, c=30, d=40: ( a, b, c, d ))

        self.assertEqual(with_defaults_func(OrderedDict([ ( "a", 10 ),
                                                          ( "b", 20 ),
                                                        ])), ( 10, 20, 30, 40 ))

        self.assertEqual(with_defaults_func(OrderedDict([ ( "b", 20 ),
                                                          ( "a", 10 ),
                                                        ])), ( 10, 20, 30, 40 ))

        self.assertEqual(with_defaults_func(OrderedDict([ ( "foo", 10 ),
                                                          ( "bar", 20 ),
                                                        ])), ( 10, 20, 30, 40 ))

        self.assertEqual(with_defaults_func(OrderedDict([ ( "foo", 10 ),
                                                          ( "d", 400 ),
                                                          ( "bar", 20 ),
                                                        ])), ( 10, 20, 30, 400 ))

        self.assertEqual(with_defaults_func(OrderedDict([ ( "foo", 10 ),
                                                          ( "bar", 20 ),
                                                          ( "baz", 300 ),
                                                        ])), ( 10, 20, 30, 40 ))
                                                        
        no_arg_func = CreateCulledCallable(lambda: 10)
        
        self.assertEqual(no_arg_func(OrderedDict()), 10)
        self.assertEqual(no_arg_func(OrderedDict([ ( "foo", 1 ),
                                                   ( "bar", 2 ),
                                                 ])), 10)

# ----------------------------------------------------------------------
class TestIsMethodsSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    class Object(object):
        def Method(self, a, b): pass

        @staticmethod
        def StaticMethod(a, b): pass

        @classmethod
        def ClassMethod(cls, a, b): pass

    # ----------------------------------------------------------------------
    def test_IsStaticMethod(self):
        self.assertEqual(IsStaticMethod(self.Object.Method), False)
        self.assertEqual(IsStaticMethod(self.Object.StaticMethod), True)
        self.assertEqual(IsStaticMethod(self.Object.ClassMethod), False)

        o = self.Object()

        self.assertEqual(IsStaticMethod(o.Method), False)
        self.assertEqual(IsStaticMethod(o.StaticMethod), True)
        self.assertEqual(IsStaticMethod(o.ClassMethod), False)

    # ----------------------------------------------------------------------
    def test_IsClassMethod(self):
        self.assertEqual(IsClassMethod(self.Object.Method), False)
        self.assertEqual(IsClassMethod(self.Object.StaticMethod), False)
        self.assertEqual(IsClassMethod(self.Object.ClassMethod), True)

        o = self.Object()
        
        self.assertEqual(IsClassMethod(o.Method), False)
        self.assertEqual(IsClassMethod(o.StaticMethod), False)
        self.assertEqual(IsClassMethod(o.ClassMethod), True)

    # ----------------------------------------------------------------------
    def test_IsStandardMethod(self):
        self.assertEqual(IsStandardMethod(self.Object.Method), True)
        self.assertEqual(IsStandardMethod(self.Object.StaticMethod), False)
        self.assertEqual(IsStandardMethod(self.Object.ClassMethod), False)

        o = self.Object()

        self.assertEqual(IsStandardMethod(o.Method), True)
        self.assertEqual(IsStandardMethod(o.StaticMethod), False)
        self.assertEqual(IsStandardMethod(o.ClassMethod), False)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
