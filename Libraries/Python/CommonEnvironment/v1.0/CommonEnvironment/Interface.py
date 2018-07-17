# ----------------------------------------------------------------------
# |  
# |  Interface.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-20 20:32:50
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Utilities to check for consistent interfaces at runtime"""

import abc
import inspect
import os
import sys
import textwrap

from collections import OrderedDict

from enum import Enum
import six

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <...> doesn't conform to <style> naming style> pylint: disable = C0103

# ----------------------------------------------------------------------
_is_python2                                 = sys.version_info[0] == 2

# Introduce some abc items into the current namespace for convenience
abstractmethod                              = abc.abstractmethod

if _is_python2:
    abstractproperty                        = abc.abstractproperty
else:
    # ABC's abstractproperty decorator has been deprecated in favor of
    # a combination of @property and @abstractmethod. Maintain abstractproperty
    # for compatibility with 2.7.
    def abstractproperty(item):
        return property(abstractmethod(item))

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class InterfaceException(Exception):
    pass

# ----------------------------------------------------------------------
# <Too few public methods> pylint: disable = R0903
class Interface(object):
    """
    Augments python abstract base class functionality with support for static methods,
    parameter checking, derived type validation, and interface query/discovery
    functionality.

    Example:

        class MyInterface(Interface):
            @abstractmethod
            def Method(self, a, b):
                raise Exception("Abstract method")

            @staticmethod
            @abstractmethod
            def StaticMethod(a, b, c=None):
                raise Exception("Abstract static method")

            @classmethod
            def ClassMethod(cls, a, b):
                raise Exception("Abstract class method")

            @abstractproperty
            def Property(self):
                raise Exception("Abstract property")

        class Obj(MyInterface):
            @override
            def Method(self, a, b):                     
                pass                        # Good

            @override
            def Method(self, a):                        
                pass                        # ERROR: 'b' is missing

            @override
            def Method(self, a, notB):                  
                pass                        # ERROR: The parameter 'notB' is not named 'b'

            @staticmethod 
            @override
            def StaticMethod(a, b, c):    
                pass                        # Good

            @staticmethod 
            @override
            def StaticMethod(a, b, c=int):
                pass                        # ERROR: 'int' != 'None'

            @property 
            @override
            def Property(self):               
                pass                        # Good

        Obj._AbstractItems:                 All abstract items defined by the class
        Obj._ExtensionItems:                All extension items made available by the class
    """

    if __debug__:
        __metaclass__                       = abc.ABCMeta
        _verified_types                     = set()

        # ----------------------------------------------------------------------
        # <Too many local variables> pylint: disable = R0914
        def __new__(cls, *args, **kwargs):
            # If here, ABC has already validated that abstract methods and properties are
            # present and named correctly. We not need to validate static methods and parameters.

            try:
                try:
                    instance = super(Interface, cls).__new__(cls)
                except TypeError as ex:
                    raise InterfaceException(str(ex))
            
                if cls in Interface._verified_types:
                    return instance

                # ----------------------------------------------------------------------
                class Entity(object):
                    
                    # ----------------------------------------------------------------------
                    # |  Public Types

                    # Enumeration values used to indicate type
                    class Type(Enum):
                        StaticMethod        = 1
                        ClassMethod         = 2
                        Method              = 3
                        Property            = 4

                    # ----------------------------------------------------------------------
                    # <Too few public methods> pylint: disable = R0903
                    class NoDefault(object):
                        """
                        Placeholder to indicate that a default value was not provided; we
                        can't use None, as None may be the actual default value provided.
                        """
                        pass

                    # ----------------------------------------------------------------------
                    # |  Public Methods
                    def __init__(self, item):
                        if not _is_python2:
                            while hasattr(item, "__func__"):
                                item = item.__func__

                        if IsStaticMethod(item):
                            typ = Entity.Type.StaticMethod
                        elif IsClassMethod(item):
                            typ = Entity.Type.ClassMethod
                        elif IsStandardMethod(item):
                            typ = Entity.Type.Method
                        else:
                            typ = Entity.Type.Property
                            item = getattr(item, "fget", item)

                        self.Type               = typ
                        self.Item               = item
                        self.FuncCode           = getattr(item, "__code__", None)
                        self.FuncDefaults       = getattr(item, "__defaults__", None)
                
                    # ----------------------------------------------------------------------
                    def TypeString(self):
                        if self.Type == Entity.Type.StaticMethod:
                            return "staticmethod"
                        if self.Type == Entity.Type.ClassMethod:
                            return "classmethod"
                        if self.Type == Entity.Type.Method:
                            return "method"
                        if self.Type == Entity.Type.Property:
                            return "property"

                        assert False, self.Type
                        return None

                    # ----------------------------------------------------------------------
                    def LocationString(self):
                        if self.FuncCode is not None:
                            filename = self.FuncCode.co_filename
                            line = self.FuncCode.co_firstlineno
                        else:
                            filename = "Unknown"
                            line = 0

                        return "<{filename} [{line}]>".format( filename=filename,
                                                               line=line,
                                                             )

                    # ----------------------------------------------------------------------
                    def GetParams(self):
                        assert self.Type != Entity.Type.Property

                        params = OrderedDict()

                        var_names = self.FuncCode.co_varnames[:self.FuncCode.co_argcount]
                        default_value_offset = len(var_names) - len(self.FuncDefaults or [])

                        for index, name in enumerate(var_names):
                            # Skip the 'self' or 'cls' value as they aren't interesting when
                            # it comes to argument comparison.
                            if index == 0 and self.Type in [ Entity.Type.Method, Entity.Type.ClassMethod, ]:
                                continue

                            if index >= default_value_offset:
                                params[name] = self.FuncDefaults[index - default_value_offset]
                            else:
                                params[name] = Entity.NoDefault

                        return params

                # ----------------------------------------------------------------------

                # Get all the abstract items and make that information available via the class type
                abstracts = {}
                extensions = {}
                errors = []

                for base in reversed(inspect.getmro(cls)):
                    these_abstracts = []

                    for member_name, member_info in inspect.getmembers(base):
                        if getattr(member_info, "__extension_method", False):
                            entity = Entity(member_info)

                            if ( member_name in extensions and 
                                 ( entity.FuncCode.co_filename != extensions[member_name].FuncCode.co_filename or 
                                   entity.FuncCode.co_firstlineno != extensions[member_name].FuncCode.co_firstlineno
                                 )
                               ):
                                errors.append("The {} '{}' has already been extended; did you mean 'override'? (new: {}, previous: {})".format( entity.TypeString(),
                                                                                                                                                member_name,
                                                                                                                                                entity.LocationString(),
                                                                                                                                                extensions[member_name].LocationString(),
                                                                                                                                              ))
                                continue

                            extensions[member_name] = entity

                        elif getattr(member_info, "__isabstractmethod__", False):
                            these_abstracts.append(member_name)

                            if member_name not in abstracts:
                                abstracts[member_name] = Entity(member_info)
                                
                    if these_abstracts and base not in Interface._verified_types:
                        Interface._verified_types.add(base)

                        base._AbstractItems = these_abstracts

                if errors:
                    raise InterfaceException(errors)

                # Sort the dictionaries by definition location to ensure a stable sort

                # ----------------------------------------------------------------------
                def SortDict(d):
                    kvps = list(six.iteritems(d))

                    kvps.sort(key=lambda kvp: ( kvp[1].FuncCode.co_filename,
                                                kvp[1].FuncCode.co_firstlineno,
                                                kvp[0],
                                              ))

                    result = OrderedDict()

                    for k, v in kvps:
                        result[k] = v

                    return result

                # ----------------------------------------------------------------------

                abstracts = SortDict(abstracts)
                extensions = SortDict(extensions)

                cls._ExtensionItems = extensions


                # Ensure that all abstracts exist
                errors = []

                # ----------------------------------------------------------------------
                def HasEntity(abstract_name, abstract_entity):
                    if abstract_entity.Type == Entity.Type.Method:
                        value = getattr(cls, abstract_name, None)
                        if value is None:
                            return False

                        try:
                            if six.get_function_code(value) == abstract_entity.FuncCode:
                                return False
                        except AttributeError:
                            return False

                    return hasattr(cls, abstract_name)

                # ----------------------------------------------------------------------

                for abstract_name, abstract_entity in six.iteritems(abstracts):
                    if not HasEntity(abstract_name, abstract_entity):
                        errors.append("The abstract {type_} '{name}' is missing {location}".format( type_=abstract_entity.TypeString(),
                                                                                                    name=abstract_name,
                                                                                                    location=abstract_entity.LocationString(),
                                                                                                  ))

                if errors:
                    raise InterfaceException(errors)

                # Create entity values for all of the derived items
                concrete_entites = []

                for abstract_name in six.iterkeys(abstracts):
                    value = getattr(cls, abstract_name)
                    concrete_entites.append(Entity(value))

                # Ensure that all abstracts are of the correct type
                errors = []

                for (abstract_name, abstract_entity), concrete_entity in zip(six.iteritems(abstracts), concrete_entites):
                    # Check if the types are the same. Allow for an abstract static
                    # method to be fulfilled by a standard method.
                    if not ( abstract_entity.Type == concrete_entity.Type or
                             ( abstract_entity.Type in [ Entity.Type.StaticMethod, Entity.Type.ClassMethod, Entity.Type.Method, ] and 
                               concrete_entity.Type in [ Entity.Type.StaticMethod, Entity.Type.ClassMethod, Entity.Type.Method, ]
                             )
                           ):
                        errors.append("'{name}' was expected to be a {abstract_type} but {concrete_type} was found ({abstract_location}, {concrete_location})" \
                                        .format( name=abstract_name,
                                                 abstract_type=abstract_entity.TypeString(),
                                                 abstract_location=abstract_entity.LocationString(),
                                                 concrete_type=concrete_entity.TypeString(),
                                                 concrete_location=concrete_entity.LocationString(),
                                               ))

                if errors:
                    raise InterfaceException(errors)

                # abc handles methods but not properties, static methods, or class methods. Use the 
                # information associated with the function to ensure that the value defined is not the 
                # same as the abstract value.
                errors = []

                for (abstract_name, abstract_entity), concrete_entity in zip(six.iteritems(abstracts), concrete_entites):
                    if abstract_entity.Type == Entity.Type.Method:
                        continue

                    # ----------------------------------------------------------------------
                    def IsMissing():
                        if abstract_entity.Type == Entity.Type.Property:
                            return getattr(concrete_entity.Item, "__isabstractmethod__", False)

                        return ( concrete_entity.FuncCode.co_filename == abstract_entity.FuncCode.co_filename and 
                                 concrete_entity.FuncCode.co_firstlineno == abstract_entity.FuncCode.co_firstlineno
                               )

                    # ----------------------------------------------------------------------

                    if IsMissing():
                        errors.append("The abstract {type_} '{name}' is missing {location}".format( type_=abstract_entity.TypeString(),
                                                                                                    name=abstract_name,
                                                                                                    location=abstract_entity.LocationString(),
                                                                                                  ))

                if errors:
                    raise InterfaceException(errors)

                # Ensure that the items are defined with the correct arguments
                errors = []

                kwargs_flag = 4
                var_args_flag = 8

                for (abstract_name, abstract_entity), concrete_entity in zip(six.iteritems(abstracts), concrete_entites):
                    if abstract_entity.Type == Entity.Type.Property:
                        continue

                    concrete_params = concrete_entity.GetParams()
                    abstract_params = abstract_entity.GetParams()

                    # We can skip the test if either the abstract or concrete params are
                    # forwarding functions:
                    #   def Func(*args, **kwargs)

                    # ----------------------------------------------------------------------
                    def IsForwardingFunction(entity, params):
                        return ( not params and
                                 entity.FuncCode.co_flags & kwargs_flag and 
                                 entity.FuncCode.co_flags & var_args_flag
                               )

                    # ----------------------------------------------------------------------

                    if IsForwardingFunction(abstract_entity, abstract_params):
                        continue

                    if IsForwardingFunction(concrete_entity, concrete_params):
                        continue

                    # If the abstract specifies a variable number of args, only check those
                    # that come before them
                    require_exact_match = True

                    for flag in [ kwargs_flag, var_args_flag, ]:
                        if abstract_entity.FuncCode.co_flags & flag:
                            require_exact_match = False
                            break

                    # This is not standard from an object-oriented perspective, but allow custom parameters
                    # with default values in concrete definitions that weren't specified in the abstract
                    # definition.
                    if len(concrete_params) > len(abstract_params):
                        params_to_remove = min(len(concrete_params) - len(abstract_params), len(concrete_entity.FuncDefaults or []))

                        keys = list(six.iterkeys(concrete_params))

                        for _ in range(params_to_remove):
                            del concrete_params[keys.pop()]

                    if ( (require_exact_match and len(concrete_params) != len(abstract_params)) or 
                         not all(k in concrete_params and concrete_params[k] == v for k, v in six.iteritems(abstract_params))
                       ):
                        errors.append(( abstract_name, 
                                        abstract_params, 
                                        abstract_entity,
                                        concrete_params,
                                        concrete_entity,
                                      ))

                if errors:
                    # ----------------------------------------------------------------------
                    def DisplayParams(params):
                        values = []
                        has_default_value = False

                        for name, default_value in six.iteritems(params):
                            if default_value != Entity.NoDefault:
                                has_default_value = True

                                values.append("{name:<40}  {default:<20}  {type_}".format( name=name,
                                                                                           default=str(default_value),
                                                                                           type_=type(default_value),
                                                                                         ))
                            else:
                                values.append(name)

                        if has_default_value:
                            return '\n'.join([ "            {}".format(value) for value in values ])

                        return "            {}".format(", ".join(values))

                    # ----------------------------------------------------------------------

                    raise InterfaceException([ textwrap.dedent(
                                                    # <Wrong hanging indentation> pylint: disable = C0330
                                                    """\
                                                    {name}
                                                            Abstract {abstract_location}
                                                    {abstract_params}
                                            
                                                            Concrete {concrete_location}
                                                    {concrete_params}
                                            
                                                    """).format( name=name,
                                                                 abstract_location=aentity.LocationString(),
                                                                 abstract_params=DisplayParams(aparams),
                                                                 concrete_location=centity.LocationString(),
                                                                 concrete_params=DisplayParams(cparams),
                                                               )
                                               for name, aparams, aentity, cparams, centity in errors
                                             ])

                # Ensure that all methods marked with override have a corresponding abstract implementation
                errors = []

                for potential_item in dir(cls):
                    if potential_item in abstracts:
                        continue

                    value = getattr(cls, potential_item)
                    value = getattr(cls, "fget", value)

                    if getattr(value, "__override_method", False) and potential_item not in cls._ExtensionItems:
                        entity = Entity(value)
                        
                        errors.append("'{}' is decorrated with 'override' but doesn't match and abstacted/extended item ({})".format(potential_item, entity.LocationString()))

                if errors:
                    raise InterfaceException(errors)

                # Ensure that all derived methods are decorated with the override decorator
                warnings = []

                for abstract_name, concrete_entity in zip(six.iterkeys(abstracts), concrete_entites):
                    if not getattr(concrete_entity.Item, "__override_method", False):
                        warnings.append("{} '{}' {}".format( concrete_entity.TypeString(),
                                                             abstract_name,
                                                             concrete_entity.LocationString(),
                                                           ))
                        
                if warnings:
                    sys.stderr.write(textwrap.dedent(
                        """\
                        WARNING: Missing override decorations in '{name}':
                        {warnings}
                        """).format( name=cls.__name__,
                                     warnings='\n'.join([ "    - {}".format(warning) for warning in warnings ]),
                                   ))

                
                Interface._verified_types.add(cls)

                return instance

            except InterfaceException as ex:
                raise InterfaceException(textwrap.dedent(
                    """\
                    Can't instantiate class '{class_}' due to:
                    {errors}
                    """).format( class_=cls.__name__,
                                 errors='\n'.join([ "    - {}".format(error) for error in (ex.args[0] if isinstance(ex.args[0], (list, tuple)) else [ ex.args[0], ]) ]),
                               ))

        # ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Decorators
# |  
# ----------------------------------------------------------------------
def extensionmethod(func):
    """
    Decorator that indicates that the method is a method that is intended to be
    extended by derived classes to override functionality (aka an "extension point").
    Note that the class associated with the method must be based on an `Interface` for
    this construct to work properly.

    To view all extensions of an `Interface`-based type:

        print('\n'.join(six.iterkeys(MyClass._ExtensionItems)))
    """

    if isinstance(func, (staticmethod, classmethod)):
        actual_func = func.__func__
    elif callable(func):
        actual_func = func
    else:
        assert False, type(func)

    setattr(actual_func, "__extension_method", True)

    return func

# ----------------------------------------------------------------------
def override(func):
    """
    Decorator that indicates that the method is overriding an abstract or extension
    method defined in a base class. Note that this decorator has no impact on
    the method's functionalty.
    """

    if isinstance(func, (staticmethod, classmethod)):
        actual_func = func.__func__
    elif callable(func):
        actual_func = func
    else:
        assert False, type(func)

    setattr(actual_func, "__override_method", True)

    return func

# ----------------------------------------------------------------------
def staticderived(cls):
    """
    Decorator designed to be used by concreate classes that only implement
    static abstract methods.

    When a conrete class implements an interface, the object's __new__ method
    is used to verify that all methods and properties have been implemented as
    expected.

    Unfortunately, __new__ is only invoked when an instance of an object is created.
    When it comes to static methods, it is possible to invoke the method without
    creating an instance of the object, meaning __new__ will never fire and the
    abstract verification code will never be caled.

    This decorator, when used in conjunction with the concrete class based on the
    abstract interface, will ensure that __new__ is properly invoked and that the
    static methods are evaluated.
    """

    if __debug__:
        cls()

    return cls

# ----------------------------------------------------------------------
def clsinit(cls):
    """
    Calls __clsinit__ on an object.

    Example:
        @clsinit
        class MyStaticObject(object):
            @classmethod
            def __clsinit__(cls):
                # Perform class initialization here
                ...
    """

    cls.__clsinit__()
    return cls

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def CreateCulledCallable(func):
    """
    Wraps a function so that it can be called with a variety of different arguments,
    passing only those associated with the original func.

    Example:
        def MyMethod(a): pass

        culled_method = CreateCulledCallback(MyMethod)

        culled_method(c=3, a=1) -> MyMethod(a=1)
        culled_method(x=10, z=20) -> MyMethod(a=10)
    """
    
    if _is_python2:
        arg_spec = inspect.getargspec(func)
    else:
        arg_spec = inspect.getfullargspec(func)

    arg_names = { arg for arg in arg_spec.args }
    positional_arg_names = arg_spec.args[:len(arg_spec.args) - len(arg_spec.defaults or [])]
    
    # Handle perfect forwarding scenarios
    if not arg_names and not positional_arg_names:
        if getattr(arg_spec, "varkw", None) is not None:
            # ----------------------------------------------------------------------
            def Invoke(kwargs):
                return func(**kwargs)

            # ----------------------------------------------------------------------

        elif arg_spec.varargs is not None:
            # ----------------------------------------------------------------------
            def Invoke(kwargs):
                return func(*tuple(six.itervalues(kwargs)))

            # ----------------------------------------------------------------------

        else:
            # ----------------------------------------------------------------------
            def Invoke(_):
                return func()

            # ----------------------------------------------------------------------
    else:
        # ----------------------------------------------------------------------
        def Invoke(kwargs):
            potential_positional_args = []

            invoke_kwargs = {}

            for k in list(six.iterkeys(kwargs)):
                if k in arg_names:
                    invoke_kwargs[k] = kwargs[k]
                else:
                    potential_positional_args.append(kwargs[k])

            for name in positional_arg_names:
                if name not in kwargs and potential_positional_args:
                    invoke_kwargs[name] = potential_positional_args.pop(0)

            return func(**invoke_kwargs)

        # ----------------------------------------------------------------------

    return Invoke

# ----------------------------------------------------------------------
if _is_python2:
    # ----------------------------------------------------------------------
    def IsStaticMethod(item):
        return inspect.isfunction(item)

    # ----------------------------------------------------------------------
    def IsClassMethod(item):
        if not inspect.ismethod(item):
            return False

        # This is a bit strange, but class functions will have a __self__ value 
        # that isn't None
        return item.__self__ is not None and type(item.__self__) == type    # <Using type() instead of isinstance() for a typecheck.> pylint: disable = C0123

    # ----------------------------------------------------------------------
    def IsStandardMethod(item):
        if not inspect.ismethod(item):
            return False

        return item.__self__ is None or type(item.__self__) != type         # <Using type() instead of isinstance() for a typecheck.> pylint: disable = C0123

    # ----------------------------------------------------------------------

else:
    # Not using inspect.signature here, as that method doesn't return the "self" or "cls"
    # part of the signature
        
    # ----------------------------------------------------------------------
    def IsStaticMethod(item):
        if type(item).__name__ not in [ "function", ]:
            return False

        # There should be a more definitive way to differentiate between
        # static/class/standard methods. Things are more predictable if
        # we have an item associated with an instance of an object, but
        # not as clear when given a method associated with the class instance.
        #
        # This is a hack!

        var_names = item.__code__.co_varnames
        return not var_names or not _CheckVariableNameVariants(var_names[0], "self", "cls")

    # ----------------------------------------------------------------------
    def IsClassMethod(item):
        if type(item).__name__ not in [ "function", "method", ]:
            return False

        # See notes in IsStaticMethod
        
        var_names = item.__code__.co_varnames
        return var_names and _CheckVariableNameVariants(var_names[0], "cls")

    # ----------------------------------------------------------------------
    def IsStandardMethod(item):
        if type(item).__name__ not in [ "function", "method", ]:
            return False

        # See notes in IsStaticMethod

        var_names = item.__code__.co_varnames
        return var_names and _CheckVariableNameVariants(var_names[0], "self")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _CheckVariableNameVariants(var, *variants):
    for variant in variants:
        if var.startswith(variant) or var.endswith(variant):
            return True

    return False
