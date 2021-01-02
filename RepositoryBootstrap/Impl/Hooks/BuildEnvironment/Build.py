# ----------------------------------------------------------------------
# |
# |  Build.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-18 13:52:55
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-21
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
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
    output_stream=sys.stdout,
    verbose=False,
):
    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        dm.result = Process.Execute(
            '"{script}" Generate PythonJson HookScript "{output_dir}" "/input={input_file}"{force}{verbose}'.format(
                script=CurrentShell.CreateScriptName("SimpleSchemaGenerator"),
                output_dir=os.path.join(_script_dir, "..", "GeneratedCode"),
                input_file=os.path.join(_script_dir, "..", "HookScript.SimpleSchema"),
                force=" /force" if force else "",
                verbose=" /verbose" if verbose else "",
            ),
            dm.stream,
        )

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
        if not os.path.isdir(output_dir):
            dm.stream.write("The output dir '{}' does not exist.\n".format(output_dir))
            return dm.result

        dm.stream.write("Removing '{}'...".format(output_dir))
        with dm.stream.DoneManager() as this_dm:
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
                    "Hooks",
                    requires_output_dir=False,
                ),
            ),
        )
    except KeyboardInterrupt:
        pass
