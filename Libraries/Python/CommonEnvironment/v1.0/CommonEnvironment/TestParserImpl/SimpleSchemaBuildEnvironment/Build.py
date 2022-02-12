# ----------------------------------------------------------------------
# |
# |  Build.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-06-04 21:44:40
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020-22
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
        schema_info = [
            # Filename, Plugin, Name, Args
            ("Benchmarks.SimpleSchema", "PythonJson", "Tester_Benchmarks", []),
            ("JUnit.SimpleSchema", "PythonXml", "Tester_JUnit", ["no_deserialization:true"]),
        ]

        command_line_template = '{script} Generate {{plugin}} {{name}} "{output_dir}" "/input={{input}}" "/output_data_filename_prefix={{name}}" {{args}}{force}{verbose}'.format(
            script=CurrentShell.CreateScriptName("SimpleSchemaGenerator"),
            output_dir=os.path.join(_script_dir, "..", "GeneratedCode"),
            force=" /force" if force else "",
            verbose=" /verbose" if verbose else "",
        )

        for schema_info_index, (schema_basename, plugin, name, args) in enumerate(schema_info):
            dm.stream.write("Processing '{}' ({} of {})...".format(schema_basename, schema_info_index + 1, len(schema_info)))
            with dm.stream.DoneManager(
                suffix="\n",
            ) as this_dm:
                schema_filename = os.path.realpath(os.path.join(_script_dir, "..", "..", "..", "..", "..", "..", "..", "Scripts", "Tester", schema_basename))
                assert os.path.isfile(schema_filename), schema_filename

                command_line = command_line_template.format(
                    plugin=plugin,
                    name=name,
                    input=schema_filename,
                    args=" ".join(['"/plugin_arg={}"'.format(arg) for arg in args]),
                )

                this_dm.stream.write("Generating code...")
                with this_dm.stream.DoneManager() as execute_dm:
                    execute_dm.result, output = Process.Execute(command_line)

                    if execute_dm.result != 0 or verbose:
                        execute_dm.stream.write(output)

                        if execute_dm.result != 0:
                            return execute_dm.result

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
