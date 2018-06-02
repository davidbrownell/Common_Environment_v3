# ----------------------------------------------------------------------
# |  
# |  CommandLine.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 20:39:53
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains command line utilities used with compilers"""

import os
import sys

from CommonEnvironment import FileSystem
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def CommandLineInvoke( compiler,
                       inputs,
                       output_stream,
                       verbose,
                       _output_via_stderr=False,
                       _output_start_line=None,
                       _output_end_line=None,
                       **compiler_kwargs
                     ):
    # ----------------------------------------------------------------------
    def Invoke(context, output_stream):
        if compiler.IsCompiler:
            method_name = "Compile"
        elif compiler.IsCodeGenerator:
            method_name = "Generate"
        elif compiler.IsVerifier:
            method_name = "Verify"
        else:
            assert False, compiler

        return getattr(compiler, method_name)(context, output_stream, verbose)

    # ----------------------------------------------------------------------

    return _CommandLineImpl( compiler,
                             inputs,
                             Invoke,
                             output_stream,
                             compiler_kwargs,
                             output_via_stderr=_output_via_stderr,
                             output_start_line=_output_start_line,
                             output_end_line=_output_end_line,
                           )

# ----------------------------------------------------------------------
def CommandLineClean( compiler,
                      inputs,
                      output_stream,
                      **compiler_kwargs
                    ):
    return _CommandLineImpl( compiler,
                             inputs,
                             compiler.Clean,
                             output_stream,
                             compiler_kwargs,
                           )

# ----------------------------------------------------------------------
def CommandLineCleanOutputDir(output_dir, output_stream):
    output_stream = StreamDecorator(output_stream)

    if not os.path.isdir(output_dir):
        output_stream.write("'{}' does not exist.\n".format(output_dir))
    else:
        output_stream.write("Removing '{}'...".format(output_dir))
        with output_stream.DoneManager():
            FileSystem.RemoveTree(output_dir)

    return 0

# ----------------------------------------------------------------------
def CommandLineCleanOutputFilename(output_filename, output_stream):
    output_stream = StreamDecorator(output_stream)

    if not os.path.isfile(output_filename):
        output_stream.write("'{}' does not exist.\n".format(output_filename))
    else:
        output_stream.write("Removing '{}'...".format(output_filename))
        with output_stream.DoneManager():
            FileSystem.RemoveFile(output_filename)

    return 0

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _CommandLineImpl( compiler,
                      inputs,
                      functor,                          # def Func(context, output_stream) -> rval
                      output_stream,
                      compiler_kwargs,
                      output_via_stderr=False,          # <Unused variable> pylint: disable = W0613
                      output_start_line=None,           # <Unused variable> pylint: disable = W0613
                      output_end_line=None,             # <Unused variable> pylint: disable = W0613
                    ):
    assert compiler
    assert inputs
    assert output_stream

    result = compiler.ValidateEnvironment()
    if result:
        output_stream.write("{}\n".format(result.rstrip()))
        return -1

    # Execute
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResult: ",
                                                     suffix='\n',
                                                     display_exceptions=False,
                                                   ) as dm:
        dm.stream.write("\nGenerating context...")
        with dm.stream.DoneManager() as this_dm:
            try:
                inputs = [ os.path.realpath(input) for input in inputs ]    # <Redefinig built-in type> pylint: disable = W0622

                contexts = list(compiler.GenerateContextItems(inputs, **compiler_kwargs))
            except Exception as ex:
                this_dm.result = -1

                if getattr(ex, "IsDiagnosticException", False):
                    this_dm.stream.write("{}\n".format(str(ex)))

                    contexts = []
                else:
                    raise

        for context in contexts:
            dm.stream.flush()

            result = functor(context, dm.stream)

            if dm.result == 0 or (dm.result > 0 and result < 0):
                dm.result = result

        return dm.result
            