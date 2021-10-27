# ----------------------------------------------------------------------
# |
# |  PythonProfilerRunner.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-10-26 07:38:10
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Runs the python profiler and postprocesses generated output."""

import os
import pstats
import sys
import textwrap

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints(
    output_filename=CommandLine.FilenameTypeInfo(
        ensure_exists=False,
    ),
    python_script_filename=CommandLine.FilenameTypeInfo(),
    argument=CommandLine.StringTypeInfo(
        arity="*",
    ),
    output_stream=None,
)
def Execute(
    output_filename,
    python_script_filename,
    argument,
    output_stream=sys.stdout,
):
    """Invokes the script with the profiler."""

    arguments = argument
    del argument

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        return _Impl(output_filename, python_script_filename, arguments, dm)


# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints(
    output_filename=CommandLine.FilenameTypeInfo(
        ensure_exists=False,
    ),
    python_script_filename=CommandLine.FilenameTypeInfo(),
    function_name=CommandLine.StringTypeInfo(),
    argument=CommandLine.StringTypeInfo(
        arity="*",
    ),
    output_stream=None,
)
def ExecuteFunction(
    output_filename,
    python_script_filename,
    function_name,
    argument,
    output_stream=sys.stdout,
):
    """Invokes functionality by calling the provided method with the profiler."""

    arguments = argument
    del argument

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        temp_script_name = CurrentShell.CreateTempFilename(suffix=".py")

        dm.stream.write("Creating temporary file...")
        with dm.stream.DoneManager():
            dirname, basename = os.path.split(python_script_filename)
            dirname = dirname.replace(os.path.sep, "/")
            basename_noext = os.path.splitext(basename)[0]

            with open(temp_script_name, "w") as f:
                f.write(
                    textwrap.dedent(
                        """\
                        import sys

                        sys.path.insert(0, "{dirname}")
                        import {basename_noext}

                        sys.exit({basename_noext}.{function_name}(*sys.argv[1:]))
                        """,
                    ).format(
                        dirname=dirname,
                        basename_noext=basename_noext,
                        function_name=function_name,
                    ),
                )

        dm.stream.write("\n")

        with CallOnExit(lambda: FileSystem.RemoveFile(temp_script_name)):
            return _Impl(output_filename, temp_script_name, arguments, dm)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _Impl(output_filename, script_filename, arguments, dm):
    temp_filename = CurrentShell.CreateTempFilename(suffix=".raw.prof")

    # Invoke the script
    dm.stream.write("Running script...")
    with dm.stream.DoneManager() as script_dm:
        command_line = 'python -m cProfile -o "{output_filename}" "{script_filename}" {arguments}'.format(
            output_filename=temp_filename,
            script_filename=script_filename,
            arguments=" ".join(['"{}"'.format(arg.replace('"', '\\"')) for arg in arguments]),
        )

        script_dm.result = Process.Execute(command_line, script_dm.stream)
        if script_dm.result != 0:
            return script_dm.result

    dm.stream.write("\n")

    # Postprocess the output
    with CallOnExit(lambda: FileSystem.RemoveFile(temp_filename)):
        dm.stream.write("Postprocessing output...")
        with dm.stream.DoneManager() as postprocess_dm:
            FileSystem.MakeDirs(os.path.dirname(output_filename))

            with open(output_filename, "w") as f:
                stats = pstats.Stats(temp_filename, stream=f)
                stats.sort_stats("tottime")
                stats.print_stats()

            postprocess_dm.stream.write("Profile data written to '{}'.\n".format(output_filename))

    return dm.result


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(
            CommandLine.Main()
        )
    except KeyboardInterrupt:
        pass
