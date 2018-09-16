# ----------------------------------------------------------------------
# |  
# |  RegularExpression.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-25 14:23:12
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Methods helpful when working with regular expressions."""

import os
import re
import sys
import textwrap

import six

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
_TemplateStringToRegex_tag_regex                        = re.compile(textwrap.dedent(
                                                               r"""(?#
                                                                LBracket:           )\{\s*(?#
                                                                Tag:                )(?P<tag>.+?)(?#
                                                                [optional begin]    )(?:(?#
                                                                    Delimiter:      )\:.*?(?#
                                                                [optional end]      ))?(?#
                                                                RBracket:           )\s*\}(?#
                                                                )"""))

def TemplateStringToRegex( content,
                           optional_tags=None,          # [set] Tags that do not require population
                           as_string=False,             # If True, returns the regex string rather than regex object
                           match_whole_string=True,
                         ):
    """
    Converts a template string into a regular expression whose matches capture all
    template values.

    Examples:
        "{foo}  {bar}  {baz}" -> "(?P<foo>.+)  (?P<bar>.+)  (?P<baz>.+)"
    """

    optional_tags = optional_tags or set()

    # Replace newline chars with placeholders so they don't get escaped.
    newline_placeholder = "__<<!!??Newline??!!>>__"

    content = re.sub( r"\r?\n",
                      lambda match: newline_placeholder,
                      content,
                      re.DOTALL | re.MULTILINE,
                    )
    output = []
    prev_index = 0
    found_tags = set()

    for match in _TemplateStringToRegex_tag_regex.finditer(content):
        # Escape everything before this match
        output.append(re.escape(content[prev_index : match.start()]))

        # Modify the match
        tag = match.group("tag")
        if tag in found_tags:
            output.append("(?P={})".format(tag))
        else:
            found_tags.add(tag)
            output.append(r"(?P<{tag}>.{arity}?)".format( tag=tag,
                                                          arity='*' if tag in optional_tags else '+',
                                                        ))

        prev_index = match.end()

    output.append(re.escape(content[prev_index :]))

    output = ''.join(output)

    if match_whole_string:
        output = "^{}$".format(output)

    output = output.replace(re.escape(newline_placeholder), r"\r?\n")
    output = output.replace(r"\ ", ' ')
    
    if as_string:
        return output

    return re.compile(output, re.DOTALL | re.MULTILINE)

# ----------------------------------------------------------------------
def PythonToJavaScript(regex_string):
    """Converts from a python to JavaScript regular expression."""

    for expr, sub in [ ( re.compile(r"\(\?#.+?\)", re.MULTILINE | re.DOTALL), lambda match: '' ),
                       ( re.compile(r"\(\?P<.+?>", re.MULTILINE | re.DOTALL), lambda match: '(' ),
                     ]:
        regex_string = expr.sub(sub, regex_string)

    return regex_string

# ----------------------------------------------------------------------
def WildcardSearchToRegularExpression( value,
                                       as_string=False,
                                     ):
    """Converts from a wildcard expression (supporting '*' and '?') to a regular expression)"""

    value = re.escape(value)

    for source, dest in [ ( r"\*", ".*" ),
                          ( r"\?", "." ),
                        ]:
        value = value.replace(source, dest)

    value = "^{}$".format(value)

    if as_string:
        return value

    return re.compile(value)

# ----------------------------------------------------------------------
def Generate( regex_or_regex_string, 
              content,
              leading_delimiter=False,
            ):
    """
    Handles some of the wonkiness associated with re.split by providing
    a consistent experience, regardless of the input and matches.

    If 'leading_delimiter' is False, the generated items will be text and
    delimiter information that follows it.

    If 'leading_delimiter' is True, the generated items will be text and
    delimiter information that proceeded it.
    """

    if isinstance(regex_or_regex_string, six.string_types):
        regex = re.compile(regex_or_regex_string)
    else:
        regex = regex_or_regex_string

    results = regex.split(content)
    
    if regex.groups:
        if len(results) == 1:
            # If here, there weren't any matches
            yield { None : results[0] }
            return

        assert len(results) % (regex.groups + 1) in [ 0, 1 ], len(results)

        if leading_delimiter:
            # If there is 1 extra element in the list of the results, that will be the
            # first element that doesn't have a corresponding match
            if len(results) % (regex.groups + 1) == 1:
                index_offset = 1

                if results[0]:
                    yield { None : results[0] }
                
            else:
                index_offset = 0

            for index in six.moves.range(index_offset, len(results), regex.groups + 1):
                result = { None : results[index + regex.groups], }

                for group_index, group_name in enumerate(six.iterkeys(regex.groupindex)):
                    result[group_name] = results[index + group_index]

                yield result
        else:
            for index in six.moves.range(0, len(results), regex.groups + 1):
                result = { None : results[index], }

                if index != len(results) - 1:
                    for group_index, group_name in enumerate(six.iterkeys(regex.groupindex)):
                        result[group_name] = results[index + group_index + 1]

                if len(result) == 1 and not result[None]:
                    continue

                yield result
    else:
        for result in results:
            yield result
