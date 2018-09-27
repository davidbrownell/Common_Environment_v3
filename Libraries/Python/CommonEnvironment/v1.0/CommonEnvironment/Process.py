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
import sys

import six

from CommonEnvironment.CallOnExit import CallOnExit

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

def Execute( command_line,
             optional_output_stream_or_functor=None,    # def Func(content) -> Bool
             convert_newlines=False,                    # Converts '\r\n' into '\n'
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

    if sys.version_info[0] == 2 and environment:
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
def ConsumeOutput( input_stream,
                   output_func,             # def Func(content) -> True to continue, False to quit
                 ):
    """
    Reads chars from the provided stream, ensuring that escape sequences and multibyte chars are atomic.
    Returns the value provided by output_func.
    """

    return _ConsumeOutputProcessor( input_stream, 
                                    output_func,
                                  ).Execute()

# ----------------------------------------------------------------------
if sys.version_info[0] == 2:
    import unicodedata
    
    # ----------------------------------------------------------------------
    def ConvertUnicodeToAsciiString(item, errors="ignore"):
        return unicodedata.normalize('NFKD', item).encode('ascii', errors)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class _ConsumeOutputProcessor(object):
    # ----------------------------------------------------------------------
    def __init__( self, 
                  input_stream, 
                  output_func,              # def Func(content) -> True to continue, False to quit
                ):
        self._input_stream                  = input_stream
        self._output_func                   = output_func

        self._read_functor                  = self._ReadStandard
        self._process_functor               = self._ProcessStandard
        self._character_buffer              = []

    # ----------------------------------------------------------------------
    def Execute(self):
        hard_stop = False

        while True:
            value = self._read_functor()
            if value is None:
                break

            content = self._process_functor(value)
            if content is None:
                continue

            if self._output_func(self._ToString(content)) is False:
                hard_stop = True
                break

        if not hard_stop and self._character_buffer:
            hard_stop = self._output_func(self._ToString(self._character_buffer)) is False

        return not hard_stop

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    _a                                      = ord('a')
    _z                                      = ord('z')
    _A                                      = ord('A')
    _Z                                      = ord('Z')

    @classmethod
    def _IsAsciiLetter(cls, value):
        return (value >= cls._a and value <= cls._z) or (value >= cls._A and value <= cls._Z)

    # ----------------------------------------------------------------------
    @staticmethod
    def _IsNewlineish(value):
        return value in [ 10, 13, ]

    # ----------------------------------------------------------------------
    @staticmethod
    def _IsEscape(value):
        return value == 27

    # ----------------------------------------------------------------------
    @staticmethod
    def _ToStringImpl(value):
        if len(value) == 1:
            return chr(value[0])

        result = bytearray(value)

        for codec in [ "utf-8",
                       "utf-16",
                       "utf-32",
                     ]:
            try:
                return result.decode(codec)
            except (UnicodeDecodeError, LookupError):
                pass

        raise Exception("The content '{}' could not be decoded".format(result))

    # ----------------------------------------------------------------------
    if sys.version[0] == 2:
        @classmethod
        def _ToString(cls, value):
            return ConvertUnicodeToAsciiString(cls._ToStringImpl(value), "replace")
    else:
        @classmethod
        def _ToString(cls, value):
            return cls._ToStringImpl(value)

    # ----------------------------------------------------------------------
    def _ReadStandard(self):
        result = self._input_stream.read(1)
        if not result:
            return None

        if isinstance(result, (six.string_types, bytes)):
            result = ord(result)

        return result

    # ----------------------------------------------------------------------
    def _ReadBufferedImpl(self, value):
        # ----------------------------------------------------------------------
        def Impl():
            self._read_functor = self._ReadStandard
            return value

        # ----------------------------------------------------------------------

        return Impl

    # ----------------------------------------------------------------------
    def _ProcessStandard(self, value):
        assert not self._character_buffer

        if self._IsEscape(value):
            self._process_functor = self._ProcessEscape
            self._character_buffer.append(value)

            return None

        if self._IsNewlineish(value):
            self._process_functor = self._ProcessLineReset
            self._character_buffer.append(value)

            return None

        if value >> 6 == 0b11:
            # This is the first char of a multibyte char
            self._process_functor = self._ProcessMultiByte
            self._character_buffer.append(value)

            return None

        return [ value, ]

    # ----------------------------------------------------------------------
    def _ProcessEscape(self, value):
        assert self._character_buffer
        self._character_buffer.append(value)

        if not self._IsAsciiLetter(value):
            return None

        self._process_functor = self._ProcessStandard

        content = self._character_buffer
        self._character_buffer = []

        return content

    # ----------------------------------------------------------------------
    def _ProcessLineReset(self, value):
        assert self._character_buffer
        
        if self._IsNewlineish(value):
            self._character_buffer.append(value)
            return None

        self._process_functor = self._ProcessStandard
        self._read_functor = self._ReadBufferedImpl(value)

        content = self._character_buffer
        self._character_buffer = []

        return content

    # ----------------------------------------------------------------------
    def _ProcessMultiByte(self, value):
        assert self._character_buffer

        if value >> 6 == 0b10:
            # Continuation char
            self._character_buffer.append(value)
            return None

        self._process_functor = self._ProcessStandard
        self._read_functor = self._ReadBufferedImpl(value)

        content = self._character_buffer
        self._character_buffer = []

        return content
