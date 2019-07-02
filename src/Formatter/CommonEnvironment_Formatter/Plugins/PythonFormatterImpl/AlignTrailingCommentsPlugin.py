# ----------------------------------------------------------------------
# |
# |  AlignTrailingCommentsPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-29 14:43:48
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

from PythonFormatterImpl.AlignAssignmentsPlugin import Plugin as AlignAssignmentsPlugin
from PythonFormatterImpl.Impl.HorizontalAlignmentImpl import HorizontalAlignmentImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Plugin(HorizontalAlignmentImpl):
    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("AlignTrailingComments")
    Priority                                = Interface.DerivedProperty(AlignAssignmentsPlugin().Priority + 1)

    # ----------------------------------------------------------------------
    # |  Private Properties
    _AlignToLinesWithoutAlignmentToken      = Interface.DerivedProperty(True)

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    @Interface.override
    def _GetAlignmentToken(line, is_initial_line):
        comment_token = None

        if line.comments:
            # We only need to look at the first comment, as they are ordered left-to-right,
            # and the first comment symbol means everything that comes after it is also
            # a comment.
            comment_token = line.comments[0][1]

        if comment_token is None:
            for index, token in enumerate(line.leaves):
                if token.value.startswith("#") and (not is_initial_line or index != 0):
                    comment_token = token
                    break

        if comment_token and comment_token.value.startswith("# BugBug"):
            comment_token = None

        return comment_token
