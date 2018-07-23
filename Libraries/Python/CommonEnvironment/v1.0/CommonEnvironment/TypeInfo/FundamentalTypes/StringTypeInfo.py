# ----------------------------------------------------------------------
# |  
# |  StringTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 10:09:51
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the StringTypeInfo object."""

import os
import re
import sys

import inflect as inflect_mod
import six

from CommonEnvironment.Interface import override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
class StringTypeInfo(TypeInfo):
    """Type info for a string value."""

    Desc                                    = DerivedProperty("String")
    ExpectedType                            = six.string_types

    # ----------------------------------------------------------------------
    def __init__( self,
                  validation_expression=None,           # regex string
                  min_length=None,
                  max_length=None,
                  **type_info_args
                ):
        super(StringTypeInfo, self).__init__(**type_info_args)

        if validation_expression is not None:
            if min_length is not None or max_length is not None:
                raise Exception("'min_length' and 'max_length' cannot be provided when 'validation_expression' is provided")
        elif min_length is None:
            min_length = 1

        if min_length is not None and min_length < 0:
            raise Exception("Invalid argument - 'min_length'")

        if min_length is not None and max_length is not None and max_length < min_length:
            raise Exception("Invalid argument - 'max_length'")

        self.ValidationExpression           = validation_expression
        self.MinLength                      = min_length
        self.MaxLength                      = max_length

    # ----------------------------------------------------------------------
    @property
    @override
    def ConstraintsDesc(self):
        constraints = []

        if self.ValidationExpression:
            constraints.append("match the regular expression '{}'".format(self.ValidationExpression))

        if self.MinLength is not None:
            constraints.append("have more than {}".format(inflect.no("character", self.MinLength)))

        if self.MaxLength is not None:
            constraints.append("have less than {}".format(inflect.no("character", self.MaxLength)))

        if not constraints:
            return ''

        return "Value must {}".format(', '.join(constraints))

    # ----------------------------------------------------------------------
    @override
    def _ValidateItemNoThrowImpl(self, item):
        if self.ValidationExpression:
            if not hasattr(self, "_validation_regex"):
                self._validation_regex = re.compile(self.ValidationExpression)

            if not self._validation_regex.match(item):
                return "'{}' does not match the validation expression '{}'".format(item, self.ValidationExpression)

        item_length = len(item)

        if self.MinLength is not None and item_length < self.MinLength:
            return "{} found in the item '{}' (At least {} expected)".format( inflect.no("character", item_length),
                                                                              item,
                                                                              inflect.no("character", self.MinLength),
                                                                            )

        if self.MaxLength is not None and item_length > self.MaxLength:
            return "{} found in the item '{}' (At most {} expected)".format( inflect.no("character", item_length),
                                                                             item,
                                                                             inflect.no("character", self.MaxLength),
                                                                           )

