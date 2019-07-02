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
    # |  Public Methods
    @classmethod
    @Interface.override
    def PreprocessLines(cls, lines):
        # We don't want the length of a comment to cause line wrapping in black. Remote the comment's
        # contents here, and then restore it once complete.
        for line in lines:
            for _, comment in line.comments:
                if not hasattr(comment, cls._ORIGINAL_VALUE_ATTRIBUTE_NAME):
                    setattr(comment, cls._ORIGINAL_VALUE_ATTRIBUTE_NAME, comment.value)
                    comment.value = "#"

        return lines

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def PostprocessLines(cls, lines):
        # Restore the original comments
        for line in lines:
            for _, comment in line.comments:
                if hasattr(comment, cls._ORIGINAL_VALUE_ATTRIBUTE_NAME):
                    comment.value = getattr(comment, cls._ORIGINAL_VALUE_ATTRIBUTE_NAME)
                    delattr(comment, cls._ORIGINAL_VALUE_ATTRIBUTE_NAME)

        return lines

    # ----------------------------------------------------------------------
    # |  Private Properties
    _ORIGINAL_VALUE_ATTRIBUTE_NAME          = "_align_trailing_comment_original_value"

    _AlignToLinesWithoutAlignmentToken      = Interface.DerivedProperty(True)

    # ----------------------------------------------------------------------
    # |  Private Methods
    @classmethod
    @Interface.override
    def _GetAlignmentToken(cls, line, is_initial_line):
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

        if comment_token and getattr(
            comment_token,
            cls._ORIGINAL_VALUE_ATTRIBUTE_NAME,
        ).startswith("# BugBug"):
            comment_token = None

        return comment_token
