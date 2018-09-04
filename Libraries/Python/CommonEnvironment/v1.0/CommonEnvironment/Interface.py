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

        Obj._AbstractItems:                 All abstract items defined by the class and its bases
        Obj._ExtensionItems:                All extension items made available by the class and its bases
        Obj._OverrideItems:                 All items overridden by the class and its bases
        
        Obj._ClassAbstractions              Abstraction names defined by this class (and not its base classes)
        obj._ClassExtensions:               Extensions names defined by this class (and not its base classes)
        obj._ClassOverrides                 Override names defined by this class (and not its base classes)
    """

    __metaclass__                       = abc.ABCMeta
    _verified_types                     = set()

    # ----------------------------------------------------------------------
    # <Too many local variables> pylint: disable = R0914
    def __new__(cls, *args, **kwargs):
        # If here, ABC has already validated that abstract methods and properties are
        # present and named correctly. We not need to validate static methods and parameters.

        try:
            _ResolveType(Interface._verified_types, cls, is_concrete_type=True)

            try:
                return super(Interface, cls).__new__(cls)
            except TypeError as ex:
                raise InterfaceException(str(ex))

        except InterfaceException as ex:
            raise InterfaceException(textwrap.dedent(
                """\
                Can't instantiate class '{class_}' due to:
                {errors}
                """).format( class_=cls.__name__,
                             errors='\n'.join([ "    - {}".format(error) for error in (ex.args[0] if isinstance(ex.args[0], (list, tuple)) else [ ex.args[0], ]) ]),
                           ))

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
        raise Exception("This type cannot be decorated with 'extensionmethod'")

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
        raise Exception("This type cannot be decorated with 'override'")

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

    cls()

    return cls

# ----------------------------------------------------------------------
def mixin(cls):
    """
    Decorate applied to a class that indicates the class is a mixin and should not
    participate in interface verification until it is part of another class.

    Example:
        class MyInterface(Interface):
            @staticmethod
            @abstractmethod
            def Method1(): pass

            @staticmethod
            @abstractmethod
            def Method2(): pass

        # Don't check that Method matches MyInterface, as Mixin isn't based on
        # MyInterface yet.

        @mixin 
        class Mixin1(Interface):
            @staticmethod
            @override
            def Method1(): pass

        @mixin
        class Mixin2(Interface):
            @staticmethod
            @override
            def Method2(): pass

        class MyObject(Mixin1, Mixin2, MyInterface):
            pass
    """

    setattr(cls, "__mixin", cls)
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
def DerivedProperty(value):
    """
    Helper when implementating a derived property that isn't dependent upon the
    instance's state. In python, a class may implement a property A) using the property
    decorator (which is valuable when the value depends on instance state or B) by
    assigning a class-level variable:

        # (A)
        class Foo(object):
            @property
            def AProperty(self):
                return self._some_value

        # (B)
        class Foo(object):
            AProperty = 10

    However, things become more complicated when implemeting a property that is abstract in
    the base class but overridden in the derived class, as the detection logic needs something
    to use to detect the user's intent (in this case, that they are overridding something that
    should be defined in the base class). This method provides that implementation using a fairly
    natural syntax.

        class Base(Interface):
            @abstractproperty
            def Name(self):
                raise Exception("Abstract property")

        @staticderived
        class Derived(Base):
            Name                            = DerivedProperty("My Name")
    """

    # ----------------------------------------------------------------------
    @property
    @override
    def PseudoProperty(self):
        return value

    # ----------------------------------------------------------------------

    # Instances of this method will be replaced by the corresponding value during
    # the logic above.
    return PseudoProperty

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
class _Entity(object):
                    
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
    class DoesNotExist(object):
        """
        Placeholder to indicate that a value doesn't exist. This gives the ability
        to differentiate from None, which is considered a valid value in some cases.
        """
        pass

    # ----------------------------------------------------------------------
    # |  Public Methods
    def __init__(self, cls, is_mixin, item):
        if not _is_python2:
            while hasattr(item, "__func__"):
                item = item.__func__

        abstract_check_item = item

        if IsStaticMethod(item):
            typ = _Entity.Type.StaticMethod
        elif IsClassMethod(item):
            typ = _Entity.Type.ClassMethod
        elif IsStandardMethod(item):
            typ = _Entity.Type.Method
        else:
            typ = _Entity.Type.Property

            item = getattr(item, "fget", item)
            if sys.version[0] != '2':
                abstract_check_item = item

        self._is_abstract                   = getattr(abstract_check_item, "__isabstractmethod__", False)

        self.Cls                            = cls
        self.IsMixin                        = is_mixin
        self.Type                           = typ
        self.Item                           = item
        self.FuncCode                       = getattr(item, "__code__", None)
        self.FuncDefaults                   = getattr(item, "__defaults__", None)
        self.RealizedValue                  = item(None) if getattr(item, "__name__", None) == "PseudoProperty" else self.DoesNotExist        

        assert self.RealizedValue == self.DoesNotExist or self.FuncCode

    # ----------------------------------------------------------------------
    @property
    def IsAbstract(self):
        return self._is_abstract

    @property
    def IsExtension(self):
        return getattr(self.Item, "__extension_method", False)

    @property
    def IsOverride(self):
        return getattr(self.Item, "__override_method", False)

    # ----------------------------------------------------------------------
    def __repr__(self):
        return textwrap.dedent(
            """\
            Interface.Entity:
                Type:           {}
                Item:           {}
                FuncCode:       {}
                FuncDefaults:   {}

            """).format( self.Type,
                         self.Item,
                         self.FuncCode,
                         self.FuncDefaults,
                       )

    # ----------------------------------------------------------------------
    def IsSameLocation(self, other):
        # Properties are tricky, as we aren't able to get code location information for
        # a property assigned as a class attribute.
        if self.Type == _Entity.Type.Property and other.Type == _Entity.Type.Property:
            # If we don't have code information for either, it means that they
            # were both created as class attributes. Compare the values to determine
            # if they are the same.
            if self.FuncCode is None and other.FuncCode is None:
                return self.Item == other.Item

            # Compare values/realized values
            if self.RealizedValue != _Entity.DoesNotExist or other.RealizedValue != _Entity.DoesNotExist:
                self_value = self.RealizedValue if self.RealizedValue != _Entity.DoesNotExist else self.Item
                other_value = other.RealizedValue if other.RealizedValue != _Entity.DoesNotExist else other.Item

                return self_value == other_value

            # If one of the entities doesn't have code info, then they can't match
            if self.FuncCode is None or other.FuncCode is None:
                return False
            
        return ( self.FuncCode.co_filename == other.FuncCode.co_filename and
                 self.FuncCode.co_firstlineno == other.FuncCode.co_firstlineno
               )

    # ----------------------------------------------------------------------
    def TypeString(self):
        if self.Type == _Entity.Type.StaticMethod:
            return "staticmethod"
        if self.Type == _Entity.Type.ClassMethod:
            return "classmethod"
        if self.Type == _Entity.Type.Method:
            return "method"
        if self.Type == _Entity.Type.Property:
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
        assert self.Type != _Entity.Type.Property

        params = OrderedDict()

        var_names = self.FuncCode.co_varnames[:self.FuncCode.co_argcount]
        default_value_offset = len(var_names) - len(self.FuncDefaults or [])

        for index, name in enumerate(var_names):
            # Skip the 'self' or 'cls' value as they aren't interesting when
            # it comes to argument comparison.
            if index == 0 and self.Type in [ _Entity.Type.Method, _Entity.Type.ClassMethod, ]:
                continue

            if index >= default_value_offset:
                params[name] = self.FuncDefaults[index - default_value_offset]
            else:
                params[name] = _Entity.DoesNotExist

        return params

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ResolveType(verified_types, cls, is_concrete_type):
    if cls in verified_types:
        return

    verified_types.add(cls)

    is_mixin = getattr(cls, "__mixin", False) == cls

    bases = list(reversed(inspect.getmro(cls)))

    # Collect information about the members of the cls
    abstracts = {}
    extensions = {}
    overrides = {}
    
    # ----------------------------------------------------------------------
    def EntityInList(entities, new_entity):
        for entity in entities:
            if entity.IsSameLocation(new_entity):
                return True

        return False

    # ----------------------------------------------------------------------
    
    # Collect information in the bases
    for base in bases:
        if base == cls or base.__name__ == "object":
            continue

        _ResolveType(verified_types, base, is_concrete_type=False)

        for src, dest in [ ( base._AbstractItems, abstracts ),
                           ( base._ExtensionItems, extensions ),
                           ( base._OverrideItems, overrides ),
                         ]:
            for k, v in six.iteritems(src):
                if isinstance(v, list):
                    src_items = v
                else:
                    src_items = [ v, ]

                dest_items = dest.setdefault(k, [])

                for src_item in src_items:
                    if EntityInList(dest_items, src_item):
                        continue

                    dest_items.append(src_item)

    # Collect information in this class
    these_abstracts = []
    these_extensions = []
    these_overrides = []
    extra_validations = []

    errors = []

    for name, value in inspect.getmembers(cls):
        if name.startswith('__'):
            continue

        entity = _Entity(cls, is_mixin, value)

        decorator_count = 0

        if entity.IsAbstract:
            decorator_count += 1

            if name not in abstracts or not EntityInList(abstracts[name], entity):
                abstracts.setdefault(name, []).append(entity)
                these_abstracts.append(name)

        if entity.IsExtension:
            decorator_count += 1

            if name not in extensions or not EntityInList(extensions[name], entity):
                extensions.setdefault(name, []).append(entity)
                these_extensions.append(name)

        if entity.IsOverride:
            decorator_count += 1

            if name not in overrides or not EntityInList(overrides[name], entity):
                overrides.setdefault(name, []).append(entity)
                these_overrides.append(name)

            if not is_mixin and name in overrides and overrides[name][-1].IsMixin:
                extra_validations.append(name)

        if decorator_count > 1:
            assert entity is not None
            errors.append("Only one of 'abstract/abstractproperty', 'extension', 'override' may be applied to an item ({}, {})".fomrat(name, entity.LocationString()))

    if errors:
        raise InterfaceException(errors)

    # Sort the items by definition location so the output is consistent
    
    # ----------------------------------------------------------------------
    def EntitySortKey(entity_kvp):
        if isinstance(entity_kvp[1], list):
            value = entity_kvp[1][-1]
        else:
            value = entity_kvp[1]

        return value.LocationString()

    # ----------------------------------------------------------------------
    def SortedEntities(entities):
        """Expects input to be an iterable of kvp tuples"""
        return OrderedDict([ kvp for kvp in sorted(six.iteritems(entities), key=EntitySortKey) ])

    # ----------------------------------------------------------------------
    def SortedNames(entities, existing_names):
        existing_names = set(existing_names)

        result = []

        for name in six.iterkeys(entities):
            if name in existing_names:
                result.append(name)

        return result

    # ----------------------------------------------------------------------

    abstracts = SortedEntities(abstracts)
    these_abstracts = SortedNames(abstracts, these_abstracts)

    extensions = SortedEntities(extensions)
    these_extensions = SortedNames(extensions, these_extensions)

    overrides = SortedEntities(overrides)
    these_overrides = SortedNames(overrides, these_overrides)

    if __debug__:
        # We shouldn't have multiple abstract or extension methods defined across multiple
        # bases. Check for this condition as we squash the lists.
        errors = []
        
        for desc, d in [ ( "abstract", abstracts ),
                         ( "extension", extensions ),
                       ]:
            for k, v in six.iteritems(d):
                if len(v) > 1:
                    errors.append("The {} {} '{}' has already been defined; did you mean 'override'? (new: {}, previous: {})" \
                                    .format( desc,
                                             v[-1].TypeString(),
                                             k,
                                             v[-1].LocationString(),
                                             v[-2].LocationString(),
                                           ))
                d[k] = v[-1]
        
        if errors:
            raise InterfaceException(errors)
        
        # We should not have items that are both abstract and extensions
        errors = []
        
        for name, abstract_entity in six.iteritems(abstracts):
            extension_entity = extensions.get(name, None)
            if extension_entity is None:
                continue
        
            errors.append("'{}' is defined as both an abstract and extension item ({}, {})".format(abstract_entity.LocationString(), extension_entity.LocationString()))
        
        if errors:
            raise InterfaceException(errors)
        
        if not is_mixin:
            overrides_to_validate = these_overrides + extra_validations

            # Ensure that derived items are associated with abstract/extension items
            errors = []
            
            for override in overrides_to_validate:
                if override not in abstracts and override not in extensions:
                    entity = overrides[override][-1]
            
                    errors.append("The {} '{}' is decorated with 'override' but doesn't match an abstract/extension item ({})".format( entity.TypeString(),
                                                                                                                                       override,
                                                                                                                                       entity.LocationString(),
                                                                                                                                     ))
            
            if errors:
                raise InterfaceException(errors)
            
            # Ensure that derived items are the right type
            errors = []
            
            for override in overrides_to_validate:
                derived_entity = overrides[override][-1]
            
                base_entity = abstracts.get(override, extensions.get(override, None))
                assert base_entity is not None, override
            
                if not ( base_entity.Type == derived_entity.Type or
                         ( base_entity.Type in [ _Entity.Type.StaticMethod, _Entity.Type.ClassMethod, _Entity.Type.Method, ] and
                           derived_entity.Type in [ _Entity.Type.StaticMethod, _Entity.Type.ClassMethod, _Entity.Type.Method, ]
                         )
                       ):
                    errors.append("The {} '{}' was implemented as a {} ({}, {})" \
                                    .format( base_entity.TypeString(),
                                             override,
                                             derived_entity.TypeString(),
                                             base_entity.LocationString(),
                                             derived_entity.LocationString(),
                                           ))
            
            if errors:
                raise InterfaceException(errors)
            
            # Ensure that derived items are defined with the correct arguments
            errors = []
            
            kwargs_flag = 4
            var_args_flag = 8
            
            for override in overrides_to_validate:
                derived_entity = overrides[override][-1]
            
                base_entity = abstracts.get(override, extensions.get(override, None))
                assert base_entity is not None, override
            
                if base_entity.Type == _Entity.Type.Property:
                    continue
            
                base_params = base_entity.GetParams()
                derived_params = derived_entity.GetParams()
            
                # We can skip the test if either the base or derived params represents a
                # forwarding function:
                #
                #   def Func(*args, **kwargs)
            
                # ----------------------------------------------------------------------
                def IsForwardingFunction(entity, params):
                    return ( not params and
                             entity.FuncCode.co_flags & kwargs_flag and
                             entity.FuncCode.co_flags & var_args_flag
                           )
            
                # ----------------------------------------------------------------------
            
                if IsForwardingFunction(base_entity, base_params):
                    continue
            
                if IsForwardingFunction(derived_entity, derived_params):
                    continue
            
                # If the base specifies a variable number of args, only check those
                # that are positional.
                require_exact_match = True
            
                for flag in [ kwargs_flag,
                              var_args_flag,
                            ]:
                    if base_entity.FuncCode.co_flags & flag:
                        require_exact_match = False
                        break
            
                # This is not standard from an object-oriented perspective, but all custom 
                # parameters with default values in derived functions, even if they weren't
                # present in the base function.
                if len(derived_params) > len(base_params):
                    params_to_remove = min(len(derived_params) - len(base_params), len(derived_entity.FuncDefaults or []))
            
                    keys = list(six.iterkeys(derived_params))
            
                    for _ in range(params_to_remove):
                        del derived_params[keys.pop()]
            
                if ( (require_exact_match and len(derived_params) != len(base_params)) or
                     not all(k in derived_params and derived_params[k] == v for k, v in six.iteritems(base_params))
                   ):
                    errors.append(( name,
                                    base_params,
                                    base_entity,
                                    derived_params,
                                    derived_entity,
                                  ))
            
            if errors:
                # ----------------------------------------------------------------------
                def DisplayParams(params):
                    values = []
                    has_default_value = False
            
                    for name, default_value in six.iteritems(params):
                        if default_value != _Entity.DoesNotExist:
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
                                                """\
                                                {name}
                                                        Base {base_location}
                                                {base_params}
            
                                                        Derived {derived_location}
            
                                                {derived_params}
            
                                                """).format( name=name,
                                                             base_location=bentity.LocationString(),
                                                             base_params=DisplayParams(bparams),
                                                             derived_location=dentity.LocationString(),
                                                             derived_params=DisplayParams(dparams),
                                                           )
                                           for name, bparams, bentity, dparams, dentity in errors 
                                         ])
            
            # Ensure that derived items are marked with override
            warnings = []
            
            for name, value in inspect.getmembers(cls):
                if name.startswith('__'):
                    continue
            
                base_entity = abstracts.get(name, extensions.get(name, None))
                if base_entity is None:
                    continue
            
                entity = _Entity(cls, is_mixin, value)
            
                if entity.IsSameLocation(base_entity):
                    continue
            
                if name not in overrides or not overrides[name][-1].IsSameLocation(entity):
                    overrides.setdefault(name, []).append(entity)
            
                    warnings.append("{} '{}' {}".format( entity.TypeString(),
                                                         name,
                                                         entity.LocationString(),
                                                       ))
            
            if warnings:
                sys.stderr.write(textwrap.dedent(
                    """\
                    WARNING: Missing override decorations in the object '{name}'
                                Filename:   {filename}
                                Line:       {line}
            
                    {warnings}
            
                    """).format( name=cls.__name__,
                                 filename=inspect.getfile(cls),
                                 line=inspect.findsource(cls)[1],
                                 warnings='\n'.join([ "               - {}".format(warning) for warning in warnings ]),
                               ))

            if is_concrete_type:
                # Ensure that all abstracts are decorated
                errors = []
            
                for name, base_entity in six.iteritems(abstracts):
                    this_entity = _Entity(cls, is_mixin, getattr(cls, name))
            
                    if this_entity.IsSameLocation(base_entity):
                        errors.append("The abstract {} '{}' is missing {}".format( base_entity.TypeString(),
                                                                                   name,
                                                                                   base_entity.LocationString(),
                                                                                 ))
            
                if errors:
                    raise InterfaceException(errors)

    # Commit the values
    cls._AbstractItems = abstracts
    cls._ExtensionItems = extensions
    cls._OverrideItems = overrides

    cls._ClassAbstractions = these_abstracts
    cls._ClassExtensions = these_extensions
    cls._ClassOverrides = these_overrides

    # Convert pseudo properties into their actual values
    for k, v in six.iteritems(overrides):
        if v[-1].RealizedValue != _Entity.DoesNotExist:
            setattr(cls, k, v[-1].RealizedValue)

# ----------------------------------------------------------------------
def _CheckVariableNameVariants(var, *variants):
    for variant in variants:
        if var.startswith(variant) or var.endswith(variant):
            return True

    return False
