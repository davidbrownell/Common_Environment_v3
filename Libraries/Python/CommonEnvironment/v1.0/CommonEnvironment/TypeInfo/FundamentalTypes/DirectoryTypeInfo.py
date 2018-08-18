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
import re
import sys

import six

from CommonEnvironment.Interface import override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class DirectoryTypeInfo(TypeInfo):

    Desc                                    = DerivedProperty("Directory")
    ExpectedType                            = six.string_types

    # ----------------------------------------------------------------------
    def __init__( self,
                  ensure_exists=True,
                  validation_expression=None,           # Regex string
                  **type_info_args
                ):
        super(DirectoryTypeInfo, self).__init__(**type_info_args)

        self.EnsureExists                   = ensure_exists
        self.ValidationExpression           = validation_expression

    # ----------------------------------------------------------------------
    @property
    @override
    def ConstraintsDesc(self):
        constraints = []

        if self.EnsureExists:
            constraints.append("be a valid directory")

        if self.ValidationExpression:
            constraints.append("match the regular expression '{}'".format(self.ValidationExpression))

        if not constraints:
            return ''

        return "Value must {}".format(', '.join(constraints))

    # ----------------------------------------------------------------------
    @override
    def _ValidateItemNoThrowImpl(self, item):
        if self.EnsureExists and not os.path.isdir(item):
            return "'{}' is not a valid directory".format(item)

        if self.ValidationExpression:
            if not hasattr(self, "_validation_regex"):
                self._validation_regex = re.compile("^{}$".format(self.ValidationExpression))

            if not self._validation_regex.match(item):
                return "'{}' does not match the validation expression '{}'".format(item, self.ValidationExpression)
