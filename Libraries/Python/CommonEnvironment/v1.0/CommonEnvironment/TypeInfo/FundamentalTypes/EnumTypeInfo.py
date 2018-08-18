# ----------------------------------------------------------------------
# |  
# |  EnumTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 23:29:04
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the EnumTypeInfo object."""

import os
import sys

import six

from CommonEnvironment.Interface import override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class EnumTypeInfo(TypeInfo):
    """Type info for an enumeration value."""

    Desc                                    = DerivedProperty("Enum")
    ExpectedType                            = six.string_types

    # ----------------------------------------------------------------------
    def __init__( self,
                  values,
                  friendly_values=None,
                  **type_info_args
                ):
        super(EnumTypeInfo, self).__init__(**type_info_args)

        if not values:
            raise Exception("A list of values must be provided")

        if not isinstance(values, list):
            values = list(values)

        if friendly_values is not None:
            if not isinstance(friendly_values, list):
                friendly_values = list(friendly_values)

            if len(friendly_values) != len(values):
                raise Exception("The number of 'friendly_values' must match the number of 'values'")

        self.Values                         = values
        self.FriendlyValues                 = friendly_values

    # ----------------------------------------------------------------------
    @property
    @override
    def ConstraintsDesc(self):
        if len(self.Values) == 1:
            return 'Value must be "{}"'.format(self.Values[0])

        return "Value must be one of {}".format(', '.join([ '"{}"'.format(value) for value in self.Values ]))

    # ----------------------------------------------------------------------
    @override
    def _ValidateItemNoThrowImpl(self, item):
        if item not in self.Values:
            return "'{}' is not a valid value ({} expected)".format( item, 
                                                                     ', '.join([ '"{}"'.format(value) for value in self.Values ]),
                                                                   )

