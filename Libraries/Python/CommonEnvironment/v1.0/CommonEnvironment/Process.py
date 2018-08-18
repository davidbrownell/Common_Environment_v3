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
from enum import Enum

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

    # Prepare the environment

    # if not environment: 
    #     environment = dict(os.environ)
    # 
    # if "PYTHONIOENCODING" not in environment:
    #     environment["PYTHONIOENCODING"] = "UTF_8"

    if sys.version_info[0] == 2:
        import unicodedata

        # ----------------------------------------------------------------------
        def ConvertUnicodeToAsciiString(item, errors="ignore"):
            return unicodedata.normalize('NFKD', item).encode('ascii', errors)

        # ----------------------------------------------------------------------

        if environment:
            # Keys and values must be strings, which can be a problem if the environment was extraced from unicode data
            for key in list(six.iterkeys(environment)):
                value = environment[key]

                if isinstance(key, unicode):                # <Undefined variable> pylint: disable = E0602
                    del environment[key]
                    key = ConvertUnicodeToAsciiString(key)

                if isinstance(value, unicode):              # <Undefined variable> pylint: disable = E0602
                    value = ConvertUnicodeToAsciiString(value)

                environment[key] = value

    # Prepare the output
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

    # Execute
    result = subprocess.Popen( command_line,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               env=environment,
                             )
    
    with CallOnExit(Flush):
        try:
            ConsumeOutput(result.stdout, output)
            result = result.wait() or 0

        except IOError:
            result = -1

    if sink is None:
        return result

    return result, sink.getvalue()

# ----------------------------------------------------------------------
if sys.version_info[0] == 2:
    import unicodedata
    
    # ----------------------------------------------------------------------
    def ConvertUnicodeToAsciiString(item, errors="ignore"):
        return unicodedata.normalize('NFKD', item).encode('ascii', errors)

# ----------------------------------------------------------------------
def ConsumeOutput( input_stream,
                   output_func,             # def Func(content) -> True to continue, False to quit
                 ):
    """
    Reads chars from the provided stream, ensuring that escape sequences and multibyte chars are atomic.
    Returns the value provided by output_func.
    """

    # ----------------------------------------------------------------------
    class CharacterStack(Enum):
        Escape = 1
        LineReset = 2
        Buffered = 3
        MultiByte = 4

    # ----------------------------------------------------------------------
    def IsAsciiLetter(value):
        return (value >= ord('a') and value <= ord('z')) or (value >= ord('A') and value <= ord('Z'))

    # ----------------------------------------------------------------------
    def IsNewlineish(value):
        return value in [ 10, 13, ]

    # ----------------------------------------------------------------------
    def IsEscape(value):
        return value == 27

    # ----------------------------------------------------------------------
    def ToString(value):
        result = bytearray(value)
        s = None

        for codec in [ "utf-8",
                       "ansi",
                       "ascii",
                     ]:
            try:
                s = result.decode(codec)
                break

            except (UnicodeDecodeError, LookupError):
                pass

        if s is None:
            raise Exception("The content '{}' could not be decoded".format(result))

        if sys.version[0] == 2:
            # Convert the Unicode string back to an ascii string
            s = ConvertUnicodeToAsciiString(s, "replace")

        return s

    # ----------------------------------------------------------------------

    character_stack = []
    character_stack_type = None

    hard_stop = False

    while True:
        # Get the next character
        if character_stack_type == CharacterStack.Buffered:
            value = character_stack.pop()

            assert not character_stack
            character_stack_type = None

        else:
            c = input_stream.read(1)
            if not c:
                break

            value = ord(c)

        content = None

        # Process the character
        if character_stack_type == CharacterStack.Escape:
            character_stack.append(value)

            if not IsAsciiLetter(value):
                continue

            content = character_stack

            character_stack = []
            character_stack_type = None

        elif character_stack_type == CharacterStack.LineReset:
            if IsNewlineish(value):
                character_stack.append(value)
                continue

            content = character_stack

            character_stack = [ value, ]
            character_stack_type = CharacterStack.Buffered

        elif character_stack_type == CharacterStack.MultiByte:
            if value >> 6 == 0b10:
                # Continuation char
                character_stack.append(value)
                continue

            content = character_stack

            character_stack = [ value, ]
            character_stack_type = CharacterStack.Buffered

        else:
            assert character_stack_type is None, character_stack_type

            if IsEscape(value):
                character_stack.append(value)
                character_stack_type = CharacterStack.Escape

                continue

            elif IsNewlineish(value):
                character_stack.append(value)
                character_stack_type = CharacterStack.LineReset

                continue

            elif value >> 6 == 0b11:
                # If the high bit is set, this is the first part of a multi-byte character
                character_stack.append(value)
                character_stack_type = CharacterStack.MultiByte

                continue

            content = [ value, ]

        assert content

        if output_func(ToString(content)) == False:
            hard_stop = True
            break

    if not hard_stop and character_stack:
        hard_stop = not output_func(ToString(character_stack))

    return not hard_stop

