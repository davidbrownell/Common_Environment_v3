# ----------------------------------------------------------------------
# |  
# |  DirectoryTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 23:07:17
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the DirectoryTypeInfo object."""

import os
import sys

import six

import CommonEnvironment
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class DirectoryTypeInfo(TypeInfo):

    Desc                                    = "Directory"
    ExpectedType                            = six.string_types

    # ----------------------------------------------------------------------
    def __init__( self,
                  ensure_exists=True,
                  **type_info_args
                ):
        super(DirectoryTypeInfo, self).__init__(**type_info_args)

        self.EnsureExists                   = ensure_exists

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self, include_private=False)

    # ----------------------------------------------------------------------
    @property
    def ConstraintsDesc(self):
        return "Value must be a valid directory" if self.EnsureExists else ''

    # ----------------------------------------------------------------------
    def _ValidateItemNoThrowImpl(self, item, **custom_args):
        if self.EnsureExists and not os.path.isdir(item):
            return "'{}' is not a valid directory".format(item)
