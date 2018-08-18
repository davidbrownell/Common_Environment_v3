# ----------------------------------------------------------------------
# |  
# |  CommandLineInvocationMixin.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 14:26:49
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the CommandLineInvocationMixin"""

import os
import sys
import textwrap

import six

from CommonEnvironment.Interface import abstractmethod, override, mixin
from CommonEnvironment import Process

from CommonEnvironment.CompilerImpl.InvocationMixin import InvocationMixin
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@mixin
class CommandLineInvocationMixin(InvocationMixin):
    """Implements invocation by invoking a command line"""

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def CreateInvokeCommandLine(context, verbose_stream):
        """Returns the command line"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _InvokeImplEx(cls, invoke_reason, context, status_stream, verbose_stream, verbose):
        command_line = cls.CreateInvokeCommandLine(context, verbose_stream)

        sink = six.moves.StringIO()

        result = Process.Execute(command_line, StreamDecorator([ sink, verbose_stream, ]))

        if result != 0 and not verbose:
            status_stream.write(sink.getvalue())

        return result

    # ----------------------------------------------------------------------
    # |  
    # |  Protected Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    def QuoteArguments( command_line_groups,            # list of lists
                      ):
        """Quotes all arguments"""

        is_windows = CurrentShell.CategoryName == "Windows"

        new_command_line_groups = []

        for group in command_line_groups:
            new_command_line_groups.append([ group[0], ])

            for arg in group[1:]:
                if is_windows and arg.endswith(os.path.sep):
                    arg += os.path.sep

                new_command_line_groups[-1].append('"{}"'.format(arg))

        return new_command_line_groups

    # ----------------------------------------------------------------------
    @staticmethod
    def PrintCommandLine( command_line_groups,
                          output_stream=None,
                        ):
        """Prints a command line to the provided output_stream or sys.stdout"""

        assert command_line_groups
        output_stream = output_stream or sys.stdout

        output = []

        if isinstance(command_line_groups, str):
            output.append(command_line_groups)
        else:
            for group in command_line_groups:
                output.append("{}\n{}\n".format( group[0],
                                                 '\n'.join([ "    {}".format(arg[1:-1]) for arg in group[1:] ]),
                                               ))

        output_stream.write(textwrap.dedent(
            """\
            ****************************************
            {}
            ****************************************
            """).format('\n'.join(output)))

    # ----------------------------------------------------------------------
    @staticmethod
    def CreateResponseFile( filename,
                            command_line_items,
                            requires_utf16,
                            arg_delimiter=' ',
                            command_line_arg_prefix='@',
                          ):
        """
        Creates a response file with the provided arguments and returns a command line using that
        response file.

        This is useful for command lines that will be very large; potentially larger than the
        underlying system can handle.
        """

        assert filename
        assert command_line_items

        if requires_utf16:
            import codecs
            open_func = lambda: codecs.open(filename, 'w', encoding="utf-16")
        else:
            open_func = lambda: open(filename, 'w')

        with open_func():
            f.write(arg_delimiter.join([ arg.replace('\\', '\\\\') for arg in command_line_items[1:] ]))

        return [ command_line_items[0],
                 "{}{}".format( command_line_arg_prefix,
                                filename,
                              ),
               ]
