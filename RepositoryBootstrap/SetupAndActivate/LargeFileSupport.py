# ----------------------------------------------------------------------
# |
# |  LargeFileSupport.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-28 10:07:18
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Functionality that supports the deconstruction and reconstruction of large files invoked during a repository's setup process."""

import os
import sys
import textwrap

import CommonEnvironment
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.SourceControlManagement.All import GetAnySCM
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


@CommandLine.EntryPoint
@CommandLine.Constraints(
    filename=CommandLine.FilenameTypeInfo(),
    output_stream=None,
)
def Deconstruct(
    filename,
    output_stream=sys.stdout,
):
    """Splits a large binary into multiple parts"""

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        dm.stream.write("Deconstructing '{}'...".format(filename))
        with dm.stream.DoneManager(
            suffix="\n\n\n",
        ) as this_dm:
            dirname, basename = os.path.split(filename)
            basename = os.path.splitext(basename)[0]

            output = os.path.join(dirname, "_{}".format(basename))
            if not filename.endswith(".7z"):
                output += ".7z"

            command_line = '7za a -t7z "{output}" -v{size}b "{input}"'.format(
                output=output,
                size=25 * 1024 * 1024,
                input=filename,
            )

            this_dm.result = Process.Execute(command_line, this_dm.stream)
            if this_dm.result != 0:
                return this_dm.result

            if not output.endswith(".7z"):
                output += ".7z"

            output += ".001"
            assert os.path.isfile(output), output

            scm_root = GetAnySCM(dirname).GetRoot(dirname)
            output = FileSystem.TrimPath(output, scm_root)

        dm.stream.write(
            textwrap.dedent(
                """\
                To reconstruct this file, add the following code to the repository's
                `Setup_custom.py` file:

                    actions += [
                        CurrentShell.Commands.Execute(
                            'python "{{script}}" Reconstruct "{{filename}}"'.format(
                                script=os.path.join(
                                    os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"),
                                    "RepositoryBootstrap",
                                    "SetupAndActivate",
                                    "LargeFileSupport.py",
                                ),
                                filename=os.path.join(_script_dir, {relative_parts}),
                            ),
                        ),
                        CurrentShell.Commands.ExitOnError(),
                    ]

                """,
            ).format(
                relative_parts=", ".join(
                    ['"{}"'.format(part) for part in output.split(os.path.sep)],
                ),
            ),
        )

        return dm.result


# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints(
    filename=CommandLine.FilenameTypeInfo(),
    output_stream=None,
)
def Reconstruct(
    filename,
    output_stream=sys.stdout,
):
    """Reconstructs a previously deconstructed binary"""

    output_stream = StreamDecorator(output_stream)

    output_stream.write("Reconstructing '{}'...".format(filename))
    output_stream._flush_after_write
    with output_stream.DoneManager(
        suffix="\n",
    ) as dm:
        command_line = '7za x "{input}" "-o{output}"'.format(
            input=filename,
            output=os.path.dirname(filename),
        )

        dm.result, output = Process.Execute(command_line)
        if dm.result != 0:
            dm.stream.write(output)

        return dm.result


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
