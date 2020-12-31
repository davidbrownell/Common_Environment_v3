# ----------------------------------------------------------------------
# |
# |  Build.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-06-04 21:44:40
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Generates code for Tester.Benchmarks.SimpleSchema"""

import os
import sys

import CommonEnvironment
from CommonEnvironment import BuildImpl
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
    output_stream=None,
)
def Build(
    force=False,
    verbose=False,
    output_stream=sys.stdout,
):
    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        schema_filename = os.path.realpath(os.path.join(_script_dir, "..", "..", "..", "..", "..", "..", "..", "Scripts", "Tester", "Benchmarks.SimpleSchema"))
        assert os.path.isfile(schema_filename), schema_filename

        command_line = '{script} Generate PythonJson Tester_Benchmarks "{output_dir}" "/input={input}"{force}{verbose}'.format(
            script=CurrentShell.CreateScriptName("SimpleSchemaGenerator"),
            output_dir=os.path.join(_script_dir, "..", "GeneratedCode"),
            input=schema_filename,
            force=" /force" if force else "",
            verbose=" /verbose" if verbose else "",
        )

        dm.stream.write("Generating code...")
        with dm.stream.DoneManager() as this_dm:
            this_dm.result, output = Process.Execute(command_line)

            if this_dm.result != 0 or verbose:
                this_dm.stream.write(output)

                if this_dm.result != 0:
                    return this_dm.result

        with open(os.path.join(_script_dir, "..", "GeneratedCode", "__init__.py"), "w") as f:
            # Nothing to write
            pass

        return dm.result


# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints(
    output_stream=None,
)
def Clean(
    output_stream=sys.stdout,
):
    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        output_dir = os.path.join(_script_dir, "..", "GeneratedCode")
        if os.path.isdir(output_dir):
            dm.stream.write("Removing '{}'...".format(output_dir))
            with dm.stream.DoneManager():
                FileSystem.RemoveTree(output_dir)

        return dm.result


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(
            BuildImpl.Main(
                BuildImpl.Configuration(
                    name="Common_Environment_TestParserImpl_SimpleSchemaBuildEnvironment",
                    requires_output_dir=False,
                ),
            ),
        )
    except KeyboardInterrupt:
        pass
