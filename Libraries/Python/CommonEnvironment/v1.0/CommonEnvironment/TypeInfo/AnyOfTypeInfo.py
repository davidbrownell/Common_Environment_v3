# ----------------------------------------------------------------------
# |  
# |  AnyOfTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 18:36:55
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the AnyOfTypeInfo object"""

import os
import sys

from CommonEnvironment.Interface import override
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class AnyOfTypeInfo(TypeInfo):
    """TypeInfo object where an item may be any number of the specified types."""

    # ----------------------------------------------------------------------
    def __init__( self,
                  type_info_list,
                  **type_info_args
                ):
        super(AnyOfTypeInfo, self).__init__(**type_info_args)

        if not type_info_list:
            raise Exception("A list of TypeInfo objects must be provided")

        self.ElementTypeInfos               = type_info_list

    # ----------------------------------------------------------------------
    # |  Properties
    @property
    @override
    def Desc(self):
        return "Any of {}".format(', '.join([ "'{}'".format(eti.Desc) for eti in self.ElementTypeInfos ]))

    @property
    @override
    def ConstraintsDesc(self):
        items = []

        for eti in self.ElementTypeInfos:
            constraint_desc = eti.ConstraintsDesc
            if constraint_desc:
                items.append("{}: {}".format(eti.Desc, constraint_desc))

        if not items:
            return ''

        return "Value where - {}".format(' / '.join(items))

    ExpectedTypeIsCallable                  = True

    # ----------------------------------------------------------------------
    # |  Public Methods
    def ExpectedType(self, item):
        return bool(self._GetElementTypeInfo(item))

    # ----------------------------------------------------------------------
    # |  Private Methods
    def _GetElementTypeInfo(self, item):
        for eti in self.ElementTypeInfos:
            if eti.IsExpectedType(item):
                return eti

    # ----------------------------------------------------------------------
    @override
    def _ValidateItemNoThrowImpl(self, item, **custom_args):
        eti = self._GetElementTypeInfo(item)
        if eti is None:
            return "'{}' is not a supported type".format(item)

        return eti.ValidateItemNoThrow(item, **custom_args)
