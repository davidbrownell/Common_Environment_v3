# ----------------------------------------------------------------------
# |  
# |  Process.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-04 18:57:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains methods usefull when interacting with processes"""

import os
import subprocess
import string
import sys

import six

from CommonEnvironment.CallOnExit import CallOnExit

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

def Execute( command_line,
             optional_output_stream_or_functor=None,    # def Func(content) -> Bool
             convert_newlines=True,                     # Converts '\r\n' into '\n'
             line_delimited_output=False,               # Buffer calls to the provided functor by lines
             environment=None,                          # Environment vars to make available to the process
           ):
    """
    Invokes the given command line.



    Returns the exit code if output_output_stream_or_functor is not None, otherwise
    ( <exit_code>, <output> )
    """

    assert command_line

    sink = None
    output = None

    if optional_output_stream_or_functor is None:
        sink = six.moves.StringIO()
        output = sink.write

    elif hasattr(optional_output_stream_or_functor, "write"):
        output_stream = optional_output_stream_or_functor
        output = output_stream.write

    else:
        output = optional_output_stream_or_functor

    if convert_newlines:
        newlines_original_output = output

        # ----------------------------------------------------------------------
        def ConvertNewlines(content):
            content = content.replace('\r\n', '\n')
            return newlines_original_output(content)

        # ----------------------------------------------------------------------

        output = ConvertNewlines

    if line_delimited_output:
        line_delimited_original_output = output

        internal_content = []

        # ----------------------------------------------------------------------
        def OutputFunctor(content):
            if '\n' in content:
                assert content.endswith('\n'), content

                content = "{}{}".format(''.join(internal_content), content)
                internal_content[:] = []

                return line_delimited_original_output(content)

            else:
                internal_content.append(content)

            return None

        # ----------------------------------------------------------------------
        def Flush():
            if internal_content:
                line_delimited_original_output(''.join(internal_content))
                internal_content[:] = []

        # ----------------------------------------------------------------------

        output = OutputFunctor

    else:
        # ----------------------------------------------------------------------
        def Flush():
            pass

        # ----------------------------------------------------------------------

    if environment and sys.version_info[0] == 2:
        # Keys and values must be strings, which can be a problem if the environment was extraced from unicode data
        import unicodedata

        # ----------------------------------------------------------------------
        def ConvertToString(item):
            return unicodedata.normalize('NFKD', item).encode('ascii', 'ignore')

        # ----------------------------------------------------------------------

        for key in list(six.iterkeys(environment)):
            value = environment[key]

            if isinstance(key, unicode):                # <Undefined variable> pylint: disable = E0602
                del environment[key]
                key = ConvertToString(key)

            if isinstance(value, unicode):              # <Undefined variable> pylint: disable = E0602
                value = ConvertToString(value)

            environment[key] = value

    result = subprocess.Popen( command_line,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               env=environment,
                             )
    
    ( CharacterStack_Escape,
      CharacterStack_LineReset,
      CharacterStack_Buffered,
    ) = range(3)

    # Handle differences between bytes and strings in Python 3
    if sys.version_info[0] == 2:
        char_to_value = lambda c: c
        is_ascii_letter = lambda c: c in string.ascii_letters
        is_newline = lambda c: c in [ '\r', '\n', ]
        is_esc = lambda c: c == '\033'
        to_ascii_string = lambda c: ''.join(c)
    else:
        char_to_value = lambda c: ord(c)
        is_ascii_letter = lambda c: (c >= ord('a') and c <= ord('z')) or (c >= ord('A') and c <= ord('Z'))
        is_newline = lambda c: c in [ 10, 13, ]
        is_esc = lambda c: c == 27

        # ----------------------------------------------------------------------
        def ToAsciiString(c):
            result = bytearray(c)

            for codec in [ "utf-8",
                           "ansi",
                         ]:
                try:
                    return result.decode(codec)
                except UnicodeDecodeError:
                    pass

            raise UnicodeDecodeError()

        # ----------------------------------------------------------------------

        to_ascii_string = ToAsciiString

    with CallOnExit(Flush):
        try:
            character_stack = []
            character_stack_type = None

            hard_stop = False

            while True:
                if character_stack_type == CharacterStack_Buffered:
                    value = character_stack.pop()

                    assert not character_stack
                    character_stack_type = None

                else:
                    c = result.stdout.read(1)
                    if not c:
                        break

                    value = char_to_value(c)

                content = None

                if character_stack_type == CharacterStack_Escape:
                    character_stack.append(value)

                    if not is_ascii_letter(value):
                        continue

                    content = character_stack

                    character_stack = []
                    character_stack_type = None

                elif character_stack_type == CharacterStack_LineReset:
                    if is_newline(value):
                        character_stack.append(value)
                        continue

                    content = character_stack

                    character_stack = [ value, ]
                    character_stack_type = CharacterStack_Buffered

                else:
                    assert character_stack_type is None, character_stack_type

                    if is_esc(value):
                        character_stack.append(value)
                        character_stack_type = CharacterStack_Escape

                        continue

                    elif is_newline(value):
                        character_stack.append(value)
                        character_stack_type = CharacterStack_LineReset

                        continue

                    content = [ value, ]

                assert content

                if output(to_ascii_string(content)) == False:
                    hard_stop = True
                    break

            if not hard_stop and character_stack:
                output(to_ascii_string(character_stack))

            result = result.wait() or 0

        except IOError:
            result = -1

    if sink is None:
        return result

    return result, sink.getvalue()
