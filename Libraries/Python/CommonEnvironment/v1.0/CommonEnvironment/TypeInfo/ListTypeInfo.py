# ----------------------------------------------------------------------
# |  
# |  ListTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 20:52:06
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the ListTypeInfo object"""

import os

import CommonEnvironment
from CommonEnvironment.Interface import override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class ListTypeInfo(TypeInfo):
    """
    Validates lists of items:

        values = [ [ 1, 2 ], [ 3, 4, 5 ], ... ]

    Note that this object should only be used for list of lists; single dimension
    lists should be implemented via a TypeInfo's arity.
    """

    Desc                                    = DerivedProperty("List")
    ExpectedType                            = (list, tuple)
    
    # ----------------------------------------------------------------------
    def __init__( self,
                  element_type_info,
                  **type_info_args
                ):
        super(ListTypeInfo, self).__init__(**type_info_args)

        if element_type_info is None:
            raise Exception("'element_type_info' is None'")
            
        self.ElementTypeInfo                = element_type_info

    # ----------------------------------------------------------------------
    @property
    @override
    def ConstraintsDesc(self):
        desc = [ "List of '{}' values".format(self.ElementTypeInfo.Desc), ]

        constraint_desc = self.ElementTypeInfo.ConstraintsDesc
        if constraint_desc:
            desc.append(" where each {}{}".format(constraint_desc[0].lower(), constraint_desc[1:]))

        return ''.join(desc)

    # ----------------------------------------------------------------------
    @override
    def _ValidateItemNoThrowImpl(self, item):
        return self.ElementTypeInfo.ValidateNoThrow(item)
