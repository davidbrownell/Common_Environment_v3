# ----------------------------------------------------------------------
# |  
# |  FilenameTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-22 23:54:06
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the FilenameTypeInfo object."""

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

class FilenameTypeInfo(TypeInfo):
    """Type info for a filename."""

    Desc                                    = DerivedProperty("Filename")
    ExpectedType                            = six.string_types

    # ----------------------------------------------------------------------
    def __init__( self,
                  ensure_exists=True,
                  match_any=False,                      # Match files or directories
                  validation_expression=None,           # Regex string
                  **type_info_args
                ):
        super(FilenameTypeInfo, self).__init__(**type_info_args)

        self.EnsureExists                   = ensure_exists
        self.MatchAny                       = match_any
        self.ValidationExpression           = validation_expression

    # ----------------------------------------------------------------------
    @property
    @override
    def ConstraintsDesc(self):
        constraints = []

        if self.EnsureExists:
            if self.MatchAny:
                suffix = " or directory"
            else:
                suffix = ''

            constraints.append("be a valid file{}".format(suffix))

        if self.ValidationExpression:
            constraints.append("match the regular expression '{}'".format(self.ValidationExpression))

        if not constraints:
            return ''

        return "Value must {}".format(', '.join(constraints))

    # ----------------------------------------------------------------------
    @override
    def _ValidateItemNoThrowImpl(self, item):
        if self.EnsureExists:
            if self.MatchAny:
                if not os.path.exists(item):
                    return "'{}' is not a valid file or directory".format(item)
            else:
                if not os.path.isfile(item):
                    return "'{}' is not a valid file".format(item)

        if self.ValidationExpression:
            if not hasattr(self, "_validation_regex"):
                self._validation_regex = re.compile("^{}$".format(self.ValidationExpression))

            if not self._validation_regex.match(item):
                return "'{}' does not match the validation expression '{}'".format(item, self.ValidationExpression)
