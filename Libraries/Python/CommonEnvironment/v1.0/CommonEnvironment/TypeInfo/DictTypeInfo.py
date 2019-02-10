# ----------------------------------------------------------------------
# |  
# |  DictTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 19:50:09
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the DictTypeInfo object"""

import os

import six

import CommonEnvironment
from CommonEnvironment.Interface import extensionmethod, override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class DictTypeInfo(TypeInfo):
    """Type info that validates a dictionary object."""

    Desc                                    = DerivedProperty("Dictionary")
    ExpectedType                            = dict

    # ----------------------------------------------------------------------
    def __init__( self,
                  items=None,               # { "<attribute>" : <TypeInfo>, }
                  require_exact_match=None,

                  # TypeInfo args; we are calling them out here so that they
                  # aren't consumed by the kwargs below.
                  arity=None,
                  validation_func=None,
                  collection_validation_func=None,

                  **kwargs
                ):
        super(DictTypeInfo, self).__init__( arity=arity,
                                            validation_func=validation_func,
                                            collection_validation_func=collection_validation_func,
                                          )

        items = items or {}

        for k, v in six.iteritems(kwargs):
            assert k not in items, k
            items[k] = v

        if any(ti is None for ti in six.itervalues(items)):
            raise Exception("All type info objects must be valid")

        self.Items                          = items
        self.RequireExactMatchDefault       = require_exact_match

        if require_exact_match and not self.Items:
            raise Exception("Attributes must be provided")

    # ----------------------------------------------------------------------
    @property
    @override
    def ConstraintsDesc(self):
        if not self.Items:
            return ''

        return "Value must contain the attributes {}".format( ', '.join([ "'{}' <{}>".format(k, v.Desc) for k, v in six.iteritems(self.Items) ]))

    # ----------------------------------------------------------------------
    @override
    def _ValidateItemNoThrowImpl( self,
                                  item, 
                                  recurse=True,
                                  require_exact_match=None,
                                  exclude=None,                             # set of names to exclude from the search
                                ):
        if require_exact_match is None:
            require_exact_match = self.RequireExactMatchDefault if self.RequireExactMatchDefault is not None else True

        exclude = exclude or set()

        attributes = { a for a in self._GetAttributes(item) if not a.startswith('_') }

        for attribute_name, type_info in six.iteritems(self.Items):
            if attribute_name not in attributes:
                if type_info.Arity.Min == 0:
                    continue

                return "The required attribute '{}' was not found".format(attribute_name)

            attributes.remove(attribute_name)

            if attribute_name in exclude:
                continue

            attribute_value = self._GetAttributeValue(item, attribute_name, type_info)

            if recurse:
                result = type_info.ValidateNoThrow(attribute_value)
            else:
                result = type_info.ValidateArityNoThrow(attribute_value)

            if result is not None:
                return "The attribute '{}' is not valid - {}".format(attribute_name, result)

        if require_exact_match:
            for attribute_name in exclude:
                attributes.discard(attribute_name)

            if attributes:
                return "The item contains extraneous data: {}".format(', '.join([ "'{}'".format(attr) for attr in attributes ]))

        return None

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def _GetAttributes(item):
        """Return the attributes for the given item."""
        return item

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def _GetAttributeValue(item, name, type_info):
        """Returns the value for the given attribute."""
        return item[name]
