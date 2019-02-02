# ----------------------------------------------------------------------
# |  
# |  Visitor.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-11-09 14:48:00
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Visitor object"""

import os

import six

import CommonEnvironment
from CommonEnvironment.Interface import Interface

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class Visitor(Interface):
    """
    Abstract base class for Visitors.

    Example:
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

        MyStaticVisitor.Accept(11)          # Static - Odd: 11
        MyStaticVisitor.Accept(10)          # Static - Even: 10

        class MyVisitor(MyVisitorInterface):
            def __init__(self, factor):
                self._factor                = factor

            @override
            def OnOdd(self, value):
                return "Odd: {}".format(value * self._factor)

            @override
            def OnEven(self, value):
                return "Even: {}".format(value * self._factor)

        v = MyVisitor(100)

        v.Accept(11)                        # Odd: 1100
        v.Accept(10)                        # Even: 1000

    """

    # ----------------------------------------------------------------------
    def __new__(cls, *args, **kwargs):
        instance = super(Visitor, cls).__new__(cls)

        import inspect

        bases = inspect.getmro(cls)

        # 1st base is the class that implements the visitor interfaces
        # 2nd base is the class that defines the visitor interfaces
        # ...
        # 3rd to last base is the visitor
        # 2nd to last base is the interface
        # Last base is object
        assert len(bases) >= 5, bases
        assert bases[-3] == Visitor, bases[-3]
        assert bases[-2] == Interface, bases[-2]
        assert bases[-1] == object, bases[-1]
        
        # Dynamically create a type that has all of the interface methods defined
        # as static methods with an implementation that forwards to the instance's
        # member function.
        methods = {}

        # Ensure that we capture methods from all potential bases
        for base_index in range(1, 1 + len(bases) - 4):
            for k in six.iterkeys(bases[base_index].__dict__):
                if k.startswith('_') or k == "Accept":
                    continue

                methods[k] = staticmethod(getattr(instance, k))

        Wrapper = type("Wrapper", ( bases[1], ), methods)                   # <Variable name "Wrapper" doesn't conform to snake_case naming style> pylint: disable = C0103

        # Override the instance's Accept method with the methods created above.
        # All of this is necessary so that we can maintain the original implementation
        # of Accept, which is expecting to invoke static methods.

        instance.Accept = Wrapper.Accept  # <Class 'Wrapper' has no 'Accept' member> pylint: disable = E1101

        return instance
