# ----------------------------------------------------------------------
# |
# |  StringHelpers.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-03 14:33:14
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-22.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Various methods that help when working with strings."""

import os
import re
import textwrap

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def Prepend( prefix,
             content,
             skip_first_line=True,
             skip_empty_lines=False,
           ):
    """Prepends the prefix to each line of the provided content."""

    lines = content.split('\n')

    # We don't want to append the prefix to a trailing newline, regardless
    # of the setting of skip_empty_lines.
    if lines and len(lines) > 1 and not lines[-1]:
        trailing_newline = True
        lines.pop()
    else:
        trailing_newline = False

    # Create the new content
    content = []

    for line in lines:
        if skip_first_line:
            skip_first_line = False
        elif line or not skip_empty_lines:
            line = "{}{}".format(prefix, line)

        content.append(line)

    content = '\n'.join(content)

    if trailing_newline:
        content += '\n'

    return content

# ----------------------------------------------------------------------
def LeftJustify( content,
                 indentation,
                 skip_first_line=True,
                 skip_empty_lines=True,
               ):
    """Left justifies the provided content."""

    return Prepend( ' ' * indentation,
                    content,
                    skip_first_line=skip_first_line,
                    skip_empty_lines=skip_empty_lines,
                  )

# ----------------------------------------------------------------------
_Wrap_preserve_newline_regex = re.compile(
    textwrap.dedent(
        r"""(?#
            Initial whitespace              )(?P<prefix>\s*)(?#
            Group Begin                     )(?P<content>(?#
                List Item                   )[-\*\+](?#
                Numbered Item               )|(?:\d+[\)\.])(?#
            Group End                       ))(?#
            Trailing Whtiespace             )(?P<suffix>\s*)(?#
        )""",
    ),
)

_Wrap_regex = re.compile(r"(?P<suffix>(?:\r?\n[ \t]*\r?\n)+)", re.MULTILINE)

def Wrap( content,
          width=70,
          expand_tabs=True,
          replace_whitespace=False,
        ):
    """Wraps text according to the specified column width."""

    from CommonEnvironment.RegularExpression import Generate

    # Get any whitespace at the beginning or end of the content.
    index = 0
    while index < len(content) and content[index].isspace():
        index += 1

    prefix = content[:index] if not replace_whitespace else ''
    content = content[index:]

    index = -1
    while len(content) > -index and content[index].isspace():
        index -= 1

    if index == -1:
        suffix = ''
    else:
        index += 1
        suffix = content[index:] if not replace_whitespace else ''
        content = content[:index]

    # ----------------------------------------------------------------------
    class Wrapper(textwrap.TextWrapper):
        # ----------------------------------------------------------------------
        def wrap(self, content):
            lines = []

            for paragraph_match in Generate(_Wrap_regex, content):
                paragraph_lines = paragraph_match[None].split("\n")

                paragraph_line_index = 0

                while paragraph_line_index != len(paragraph_lines):
                    paragraph_line = paragraph_lines[paragraph_line_index]

                    preserve_newline_match = _Wrap_preserve_newline_regex.match(paragraph_line)
                    if preserve_newline_match:
                        wrapped_lines = textwrap.TextWrapper.wrap(self, paragraph_line)

                        if len(wrapped_lines) > 1:
                            # Add any prefix whitespace to the new lines
                            prefix = "{}{}{}".format(
                                preserve_newline_match.group("prefix"),
                                " " * len(preserve_newline_match.group("content")),
                                preserve_newline_match.group("suffix"),
                            )

                            for wrapped_index, wrapped_line in enumerate(wrapped_lines[1:]):
                                wrapped_lines[wrapped_index + 1] = "{}{}".format(
                                    prefix,
                                    wrapped_line,
                                )

                        lines += wrapped_lines
                        paragraph_line_index += 1

                        continue

                    paragraph_line_start = paragraph_line_index

                    while (
                        paragraph_line_index != len(paragraph_lines)
                        and not _Wrap_preserve_newline_regex.match(paragraph_lines[paragraph_line_index])
                    ):
                        paragraph_lines[paragraph_line_index] = paragraph_lines[paragraph_line_index].rstrip() + " "
                        paragraph_line_index += 1

                    lines += textwrap.TextWrapper.wrap(self, "".join(paragraph_lines[paragraph_line_start:paragraph_line_index]))

                if "suffix" in paragraph_match:
                    suffix = paragraph_match["suffix"]

                    # If there is already content, it will have a newline after it -
                    # remove one of the explicit newlines
                    if lines:
                        if suffix[0] == '\r': suffix = suffix[1:]
                        if suffix[0] == '\n': suffix = suffix[1:]

                    # Remove an explicit newline from the end, as it will be added
                    # when the lines are joined
                    assert suffix
                    assert suffix.endswith('\n'), suffix

                    suffix = suffix[:-1]
                    if suffix.endswith('\r'):
                        suffix = suffix[:-1]

                    lines.append(suffix)

            return lines

    # ----------------------------------------------------------------------

    wrapper = Wrapper( width=width,
                       expand_tabs=expand_tabs,
                       replace_whitespace=replace_whitespace,
                     )

    return "{}{}{}".format( prefix,
                            wrapper.fill(content),
                            suffix,
                          )

# ----------------------------------------------------------------------
def ToPascalCase(s):
    """Returns APascalCase string"""

    if not s:
        return s

    parts = s.split('_')

    # Handle the corner case where the original string starts or ends with an
    # underscore.
    index = 0
    while index < len(parts) and not parts[index]:
        parts[index] = '_'
        index += 1

    index = -1
    while len(parts) > -index and not parts[index]:
        parts[index] = '_'
        index -= 1

    return ''.join([ "{}{}".format(part[0].upper(), part[1:]) for part in parts ])

# ----------------------------------------------------------------------
_ToSnakeCase_regex                          = re.compile(r"((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")

def ToSnakeCase(s):
    """Returns a_snake_case string"""

    # Extract prefix and suffix underscores
    index = 0
    while index < len(s) and s[index] == '_':
        index += 1

    prefix = '_' * index
    s = s[index:]

    index = -1
    while len(s) > -index and s[index] == '_':
        index -= 1

    if index == -1:
        suffix = ''
    else:
        index += 1

        suffix = '_' * -index
        s = s[:index]

    return "{}{}{}".format( prefix,
                            _ToSnakeCase_regex.sub(r'_\1', s).lower().replace('__', '_'),
                            suffix,
                          )
