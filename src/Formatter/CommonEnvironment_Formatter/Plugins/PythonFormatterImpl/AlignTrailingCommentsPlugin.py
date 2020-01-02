# ----------------------------------------------------------------------
# |
# |  AlignTrailingCommentsPlugin.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-29 14:43:48
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os
import re
import sys
import textwrap

import CommonEnvironment
from CommonEnvironment import Interface
from CommonEnvironment import RegularExpression

from PythonFormatterImpl.AlignAssignmentsPlugin import Plugin as AlignAssignmentsPlugin # <Unable to import> pylint: disable = E0401

from PythonFormatterImpl.Impl.BlackImports import black, python_tokens
from PythonFormatterImpl.Impl.HorizontalAlignmentImpl import HorizontalAlignmentImpl # <Unable to import> pylint: disable = E0401

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

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
    def PreprocessContent(cls, content):
        # black doesn't handle comments well, especially those embedded within a
        # structure that would otherwise be split. Decorate comments that are
        # header comments - those that are vertically aligned with content directly
        # below it. Modify the contents so these special comments can be uniquely
        # identified and then restored after black has altered the content.
        regex = re.compile(
            textwrap.dedent(
                r"""(?#
                Initial Whitespace                      )^(?P<whitespace>\s*)(?#
                Comment                                 )(?P<content>#[^\r\n]*)(?#
                Newline                                 )(?P<newline>\r?\n)(?#
                Next Line Whitespace                    )(?P=whitespace)(?#
                Non-comment, Non-whitespace char        )(?P<first_char>[^#\s])(?#
                )""",
            ),
            re.MULTILINE,
        )

        # We don't want to decorate python code embedded in mutliline strings,
        # so remove that content first.
        multiline_strings = []

        multiline_string_regex = re.compile(
            r"(?P<quote>\"\"\"|\'\'\')(?P<content>.*?)(?P=quote)",
            re.DOTALL | re.MULTILINE,
        )

        # ----------------------------------------------------------------------
        def OnMultilineStripMatch(match):
            multiline_strings.append(match.group("content"))

            return "{quote}<<__stripped_content__>>{quote}".format(
                quote=match.group("quote"),
            )

        # ----------------------------------------------------------------------
        def OnMultilineRestoreMatch(match):
            assert multiline_strings

            return "{quote}{content}{quote}".format(
                quote=match.group("quote"),
                content=multiline_strings.pop(0),
            )

        # ----------------------------------------------------------------------

        content = multiline_string_regex.sub(OnMultilineStripMatch, content)

        # ----------------------------------------------------------------------
        def OnMatch(match):
            return "{ws}{comment}{newline}{ws}{first_char}".format(
                comment=cls._HEADER_SUB_TEMPLATE.format(
                    content=match.group("content"),
                ),
                newline=match.group("newline"),
                ws=match.group("whitespace"),
                first_char=match.group("first_char"),
            )

        # ----------------------------------------------------------------------

        content = regex.sub(OnMatch, content)
        content = multiline_string_regex.sub(OnMultilineRestoreMatch, content)

        return content

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def PreprocessLines(cls, lines):
        # We don't want the length of a comment to cause line wrapping in black. Remote the comment's
        # contents here, and then restore it once complete.

        # ----------------------------------------------------------------------
        def ProcessComment(comment):
            if not hasattr(comment, cls._ORIGINAL_VALUE_ATTRIBUTE_NAME):
                setattr(comment, cls._ORIGINAL_VALUE_ATTRIBUTE_NAME, comment.value)
                comment.value = "#"

        # ----------------------------------------------------------------------

        for line in lines:
            if len(line.leaves) == 1 and line.leaves[0].type == black.STANDALONE_COMMENT:
                ProcessComment(line.leaves[0])

            for _, comment in line.comments:
                ProcessComment(comment)

        return lines

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def PostprocessLines(cls, lines):
        # Restore the original comments

        regex = RegularExpression.TemplateStringToRegex(cls._HEADER_SUB_TEMPLATE)

        # ----------------------------------------------------------------------
        def ProcessComment(comment):
            if hasattr(comment, cls._ORIGINAL_VALUE_ATTRIBUTE_NAME):
                comment.value = getattr(comment, cls._ORIGINAL_VALUE_ATTRIBUTE_NAME)
                delattr(comment, cls._ORIGINAL_VALUE_ATTRIBUTE_NAME)

            match = regex.match(comment.value)
            if not match:
                return False

            comment.value = match.group("content")
            return True

        # ----------------------------------------------------------------------

        line_index = 0
        while line_index < len(lines):
            line = lines[line_index]

            if len(line.leaves) == 1 and line.leaves[0].type in [
                black.STANDALONE_COMMENT,
                python_tokens.COMMENT,
            ]:
                if ProcessComment(line.leaves[0]):
                    # Keep newlines but remove spaces
                    line.leaves[0].prefix = line.leaves[0].prefix.replace(" ", "")

                    assert line_index + 1 != len(lines)
                    line.depth = lines[line_index + 1].depth

            for _, comment in line.comments:
                ProcessComment(comment)

            line_index += 1

        return lines

    # ----------------------------------------------------------------------
    # |  Private Properties
    _ORIGINAL_VALUE_ATTRIBUTE_NAME          = "_align_trailing_comment_original_value"

    _HEADER_SUB_TEMPLATE                    = "# __HeaderComment<<??!!__: {content}"

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

        if comment_token and cls._GetCommentValue(comment_token).startswith("# BugBug"):
            comment_token = None

        return comment_token

    # ----------------------------------------------------------------------
    @classmethod
    def _GetCommentValue(cls, comment_token):
        return getattr(comment_token, cls._ORIGINAL_VALUE_ATTRIBUTE_NAME, comment_token.value)
