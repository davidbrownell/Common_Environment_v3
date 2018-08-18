# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-20 20:11:20
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Constructs used when defining types."""

import os
import sys

import inflect as inflect_mod
import six

import CommonEnvironment
from CommonEnvironment.Interface import Interface, \
                                        abstractmethod, \
                                        abstractproperty

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class ValidationException(Exception):
    """Exception thrown when an aspect of a type failed validation."""
    pass

# ----------------------------------------------------------------------
class Arity(object):
    """Describes how many instances of a type are considered valid."""

    # ----------------------------------------------------------------------
    @classmethod
    def FromString(cls, value):
        """
        Returns an Arity object based on a string value.

        Examples:
            ?       0 or 1
            1       1
            *       0 or more
            +       1 or more
            {3,4}   3 or 4
            {2,8}   2-8 [inclusive]
            {4}     Exactly 4
            {2+}    2 or more
        """

        if value == '?':
            return cls(0, 1)
        if value == '1':
            return cls(1, 1)
        if value == '*':
            return cls(0, None)
        if value == '+':
            return cls(1, None)

        if value.startswith('{') and value.endswith('}'):
            values = [ v.strip() for v in value[1:-1].split(',') ]

            if len(values) == 1 and values[0].endswith('+'):
                is_or_more = True
                values[0] = values[0][:-1]
            else:
                is_or_more = False

            values = [ int(value) for value in values ]

            if len(values) == 1:
                if is_or_more:
                    return cls(values[0], None)

                return cls(values[0], values[0])
            elif len(values) == 2:
                return cls(values[0], values[1])

        raise Exception("'{}' is not a valid arity string".format(value))

    # ----------------------------------------------------------------------
    def __init__(self, min, max_or_none):
        if min is None or min < 0:
            raise Exception("Invalid argument - 'min'")

        if max_or_none is not None and min > max_or_none:
            raise Exception("Invalid argument - 'max_or_none'")

        self.Min                            = min
        self.Max                            = max_or_none

    # ----------------------------------------------------------------------
    def __repr__(self):
        return "Arity({}, {})".format(self.Min, self.Max)

    # ----------------------------------------------------------------------
    @property
    def IsSingle(self):
        return self.Min == 1 and self.Max == 1

    @property
    def IsOptional(self):
        return self.Min == 0 and self.Max == 1

    @property
    def IsCollection(self):
        return self.Max is None or self.Max > 1

    @property
    def IsOptionalCollection(self):
        return self.IsCollection and self.Min == 0

    @property
    def IsFixedCollection(self):
        return self.IsCollection and self.Min == self.Max

    @property
    def IsZeroOrMore(self):
        return self.Min == 0 and self.Max is None

    @property
    def IsOneOrMore(self):
        return self.Min == 1 and self.Max is None

    @property
    def IsRange(self):
        return self.Max is not None and self.Min != self.Max and not self.IsOptional

    # ----------------------------------------------------------------------
    def ToString( self,
                  brackets=None,            # (lbracket, rbracket)
                ):
        brackets = brackets or ( '{', '}' )

        if self.IsOptional:
            return '?'
        if self.IsSingle:
            return ''
        if self.IsZeroOrMore:
            return '*'
        if self.IsOneOrMore:
            return '+'
        if self.Min == self.Max:
            return "{}{}{}".format( brackets[0],
                                    self.Min,
                                    brackets[1],
                                  )
        if self.Max is None:
            return "{}{}+{}".format( brackets[0],
                                     self.Min,
                                     brackets[1],
                                   )

        return "{}{},{}{}".format( brackets[0],
                                   self.Min,
                                   self.Max,
                                   brackets[1],
                                 )

    # ----------------------------------------------------------------------
    # <Too many return statements> pylint: disable = R0911
    def __cmp__(self, other):
        if not isinstance(other, self.__class__):
            return -1

        if self.Min < other.Min:
            return -1
        elif other.Min < self.Min:
            return 1

        if self.Max is None:
            if other.Max is not None:
                return 1
        else:
            if other.Max is None:
                return -1

            if self.Max < other.Max:
                return -1
            elif self.Max > other.Max:
                return 1

        assert self.Min == other.Min, (self.Min, other.Min)
        assert self.Max == other.Max, (self.Max, other.Max)

        return 0

    # ----------------------------------------------------------------------
    def __lt__(self, other):
        return self.__cmp__(other) < 0

    # ----------------------------------------------------------------------
    def __eq__(self, other):
        return self.__cmp__(other) == 0

# ----------------------------------------------------------------------
class TypeInfo(Interface):
    """
    Base class for information about a type.

    Derived types can be integers, strings, dictitionaries, or anything
    else. Type information is used in a number of different metaprogramming
    tasks including python parameter validation and code generation
    activities.
    """

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    @abstractproperty
    def Desc(self):
        """
        A description of the type.
        
        The resulting string may include instance-specific constraints, such
        as the minimum length of a string type.
        """
        raise Exception("Abstract property")

    @abstractproperty
    def ConstraintsDesc(self):
        """
        Description about the constraints associated with the type.

        This can be an empty string if not constraints are associated with the
        type.
        """
        raise Exception("Abstract property")

    # In theory, this should be an abstractproperty. However, some implementations
    # have a callable ExpectedType, which will cause Interface validation to fail.
    # If someone forgets to implement the property/method, they will see an exception
    # raised on the first invocation.
    #
    # @abstractproperty
    def ExpectedType(self):
        """Returns the expected python type associated with the type."""
        raise Exception("Abstract property")

    @property
    def ExpectedTypeIsCallable(self):
        """Returns True if ExpectedType is a callable method rather than a property"""
        return False

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    def __init__( self,
                  arity=None,                           # [optional] Arity object or string; default is Arity(1, 1)
                  validation_func=None,                 # [optional] def Func(value) -> string on error
                  collection_validation_func=None,      # [optional] def Func(values) -> string on error
                ):
        if isinstance(arity, six.string_types):
            arity = Arity.FromString(arity)
        else:
            arity = arity or Arity(1, 1)

        if collection_validation_func and not arity.IsCollection:
            raise Exception("'collection_validation_func' can only be used with types that are collections")

        self.Arity                          = arity
        self.ValidationFunc                 = validation_func
        self.CollectionValidationFunc       = collection_validation_func

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    def IsExpectedType(self, item):
        """Returns True if the item is the expected Python type"""
        if self.ExpectedTypeIsCallable:
            return self.ExpectedType(item)              # <Class '<name>' has no '<attr>' member> pylint: disable = E1101

        return isinstance(item, self.ExpectedType)      # <Class '<name>' has no '<attr>' member> pylint: disable = E1101

    # ----------------------------------------------------------------------
    def IsValid(self, item_or_items, **custom_args):
        """
        Returns True if the input is considered valid.
        
        This method is aware of collections.
        """
        return self.ValidateNoThrow(item_or_items, **custom_args) is None

    # ----------------------------------------------------------------------
    def IsValidItem(self, item, **custom_args):
        """
        Returns True if the input is considered valid.

        This method is NOT aware of collections.
        """
        return self.ValidateItemNoThrow(item, **custom_args) is None

    # ----------------------------------------------------------------------
    def IsValidArity(self, item_or_items):
        """
        Returns True if the input is considered valid based on arity.
        """
        return self.ValidateArityNoThrow(item_or_items) is None

    # ----------------------------------------------------------------------
    def Validate(self, item_or_items, **custom_args):
        """
        Raises ValidationException if the input is considered invalid.

        This method is aware of collections.
        """
        result = self.ValidateNoThrow(item_or_items, **custom_args)
        if result is not None:
            raise ValidationException(result)

    # ----------------------------------------------------------------------
    def ValidateItem(self, item, **custom_args):
        """
        Raises ValidationException if the input is considered invalid.

        This method is NOT aware of collections.
        """
        result = self.ValidateItemNoThrow(item, **custom_args)
        if result is not None:
            raise ValidationException(result)

    # ----------------------------------------------------------------------
    def ValidateArity(self, item_or_items):
        """
        Raises ValidationException if the input is considered invalid based
        on arity alone.
        """
        result = self.ValidateArityNoThrow(item_or_items)
        if result is not None:
            raise ValidationException(result)

    # ----------------------------------------------------------------------
    # TODO: This is here for back-compat with v2. Remove once SimpleSchemaCodeGenerator
    #       has been updated.
    def ValidateArityCount(self, count):
        result = self.ValidateArityCountNoThrow(count)
        if result is not None:
            raise ValidationException(result)

    def ValidateArityCountNoThrow(self, count):
        if not self.Arity.IsCollection:
            if (count == 0 and not self.Arity.IsOptional) or count > 1:
                return "1 item was expected"

            return None

        if self.Arity.Min != None and count < self.Arity.Min:
            return "At least {} {} expected".format( inflect.no("item", self.Arity.Min),
                                                     inflect.plural_verb("was", self.Arity.Min),
                                                   )

        if self.Arity.Max != None and count > self.Arity.Max:
            return "At most {} {} expected".format( inflect.no("item", self.Arity.Max),
                                                    inflect.plural_verb("was", self.Arity.Max),
                                                  )

        return None

    # TODO: End

    # ----------------------------------------------------------------------
    def ValidateNoThrow(self, item_or_items, **custom_args):
        """Returns an error string if the input is not valid."""

        result = self.ValidateArityNoThrow(item_or_items)
        if result is not None:
            return result

        if not self.Arity.IsCollection:
            item_or_items = [ item_or_items, ]
        elif item_or_items is None:
            item_or_items = []

        result = (self.CollectionValidationFunc or (lambda item_or_items: None))(item_or_items)
        if result is not None:
            return result

        for item in item_or_items:
            result = self.ValidateItemNoThrow(item, **custom_args)
            if result is not None:
                return result

        return None

    # ----------------------------------------------------------------------
    def ValidateItemNoThrow(self, item, **custom_args):
        """Returns an error string if the input is not valid."""

        if self.Arity.IsOptional and item is None:
            return None

        if not self.IsExpectedType(item):
            return "'{}' is not {}".format(item, inflect.a(self._GetExpectedTypeString()))

        result = self._ValidateItemNoThrowImpl(item, **custom_args)
        if result is not None:
            return result

        result = (self.ValidationFunc or (lambda item: None))(item)
        if result is not None:
            return result

        return None

    # ----------------------------------------------------------------------
    def ValidateArityNoThrow(self, item_or_items):
        """Returns an error string if the input's arity is not valid."""

        if item_or_items is None:
            if self.Arity.Min != 0:
                return "An item was expected"

            return None

        if isinstance(item_or_items, (list, tuple)):
            if self.Arity.Max == 1:
                return "1 item was expected"

            if len(item_or_items) < self.Arity.Min:
                return "At least {} {} expected ({} found)".format( inflect.no("item", self.Arity.Min), 
                                                                    inflect.plural_verb("was", self.Arity.Min),
                                                                    len(item_or_items),
                                                                  )

            if self.Arity.Max is not None and len(item_or_items) > self.Arity.Max:
                return "At most {} {} expected ({} found)".format( inflect.no("item", self.Arity.Max),
                                                                   inflect.plural_verb("was", self.Arity.Max),
                                                                   len(item_or_items),
                                                                 )
        elif self.IsExpectedType(item_or_items):
            if self.Arity.IsCollection:
                return "A collection was expected"
        
        else:
            return "Invalid input"

        return None

    # ----------------------------------------------------------------------
    # |  
    # |  Protected Methods
    # |  
    # ----------------------------------------------------------------------
    def _GetExpectedTypeString(self):
        # ----------------------------------------------------------------------
        def GetTypeName(t):
            return getattr(t, "__name__", str(t))

        # ----------------------------------------------------------------------

        if self.ExpectedTypeIsCallable:
            return self.__class__.__name__

        if isinstance(self.ExpectedTypeIsCallable, tuple):
            return ', '.join([ GetTypeName(t) for t in self.ExpectedType ])     # <Class '<name>' has no '<attr>' member> pylint: disable = E1103

        return GetTypeName(self.ExpectedType)                                   # <Class '<name>' has no '<attr>' member> pylint: disable = E1103

    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _ValidateItemNoThrowImpl(item, **custom_args):
        """Returns a string on error"""
        raise Exception("Abstract method")
