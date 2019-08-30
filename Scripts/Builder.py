# ----------------------------------------------------------------------
# |
# |  Builder.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-20 22:51:45
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""General purpose build executor."""

import os
import sys

from collections import namedtuple

import inflect as inflect_mod

import CommonEnvironment
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import StringHelpers

from CommonEnvironment.BuildImpl import CompleteConfiguration as Configuration

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------

BUILD_FILENAME                              = "Build.py"
BUILD_FILENAME_IGNORE                       = "{}-ignore".format(BUILD_FILENAME)

BUILD_LOG_TEMPLATE                          = "Build.{mode}.log"

COMPLETE_CONFIGURATION_NAME                 = "Complete"
STANDARD_CONFIGURATION_NAMES                = ["Debug", "Release"]

# ----------------------------------------------------------------------
@CommandLine.EntryPoint(
    mode=CommandLine.EntryPoint.Parameter('Defaults to [ "clean", "build", ]'),
)
@CommandLine.Constraints(
    root_dir=CommandLine.DirectoryTypeInfo(),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
    ),
    mode=CommandLine.StringTypeInfo(
        arity="*",
    ),
    output_stream=None,
)
def Execute(
    root_dir,
    output_dir,
    mode=None,
    debug_only=False,
    release_only=False,
    build_filename=BUILD_FILENAME,
    build_filename_ignore=BUILD_FILENAME_IGNORE,
    output_stream=sys.stdout,
    verbose=False,
):
    """Recursively calls Build files with the desired mode(s)"""

    assert os.path.isdir(root_dir), root_dir
    assert output_dir
    modes = mode or ["clean", "build"]
    del mode
    assert output_stream

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        build_infos = _GetBuildInfos(
            root_dir,
            dm.stream,
            build_filename,
            build_filename_ignore,
        )
        if not build_infos:
            return dm.result

        # Find all the build files that have configurations that we can process
        build_configurations = []

        dm.stream.write("Processing build files...")
        with dm.stream.DoneManager(
            done_suffix=lambda: "{} found".format(
                inflect.no("configuration", len(build_configurations)),
            ),
        ) as this_dm:
            # ----------------------------------------------------------------------
            def GetSupportedConfigurations(configurations):
                # If there is a configuration that indicates completeness, execute that
                # and skip everything else.
                if COMPLETE_CONFIGURATION_NAME in configurations:
                    yield COMPLETE_CONFIGURATION_NAME
                    return

                for potential_config in STANDARD_CONFIGURATION_NAMES:
                    potential_config_lower = potential_config.lower()

                    if (
                        (debug_only and "debug" in potential_config_lower)
                        or (release_only and "release" in potential_config_lower)
                        or (not debug_only and not release_only)
                    ):
                        yield potential_config

            # ----------------------------------------------------------------------

            for build_info in build_infos:
                if not build_info.configuration.Configurations:
                    build_configurations.append(
                        (build_info.filename, build_info.configuration, None),
                    )
                else:
                    for config in GetSupportedConfigurations(
                        build_info.configuration.Configurations,
                    ):
                        build_configurations.append(
                            (build_info.filename, build_info.configuration, config),
                        )

        if not build_configurations:
            return dm.result

        dm.stream.write("\n")

        for mode_index, mode in enumerate(modes):
            dm.stream.write(
                "Invoking '{}' ({} of {})...".format(mode, mode_index + 1, len(modes)),
            )
            with dm.stream.DoneManager(
                suffix="\n",
            ) as mode_dm:
                for build_index, (build_filename, config, configuration) in enumerate(
                    build_configurations,
                ):
                    mode_dm.stream.write(
                        "Processing '{}'{} ({} of {})...".format(
                            build_filename,
                            " - '{}'".format(configuration) if configuration else "",
                            build_index + 1,
                            len(build_configurations),
                        ),
                    )
                    with mode_dm.stream.DoneManager() as build_dm:
                        build_output_dir = os.path.join(
                            output_dir,
                            config.SuggestedOutputDirLocation,
                            configuration or "Build",
                        )
                        FileSystem.MakeDirs(build_output_dir)

                        command_line = 'python "{build_filename}" {mode}{configuration}{output_dir}'.format(
                            build_filename=build_filename,
                            mode=mode,
                            configuration=' "{}"'.format(
                                configuration,
                            ) if configuration else "",
                            output_dir=' "{}"'.format(
                                build_output_dir,
                            ) if config.RequiresOutputDir else "",
                        )

                        build_dm.result, output = Process.Execute(command_line)

                        # It is possible that the cleaning process deleted the output directory. Recreate it
                        # if necessary to store the log file.
                        FileSystem.MakeDirs(build_output_dir)

                        with open(
                            os.path.join(
                                build_output_dir,
                                BUILD_LOG_TEMPLATE.format(
                                    mode=mode,
                                ),
                            ),
                            "w",
                        ) as f:
                            f.write(output)

                        if build_dm.result != 0:
                            build_dm.stream.write(output)
                        elif verbose:
                            build_dm.stream.write(
                                StringHelpers.LeftJustify(
                                    "INFO: {}".format(output),
                                    len("INFO: "),
                                ),
                            )

        return dm.result


# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints(
    root_dir=CommandLine.DirectoryTypeInfo(),
    output_stream=None,
)
def List(
    root_dir,
    build_filename=BUILD_FILENAME,
    build_filename_ignore=BUILD_FILENAME_IGNORE,
    output_stream=sys.stdout,
):
    assert os.path.isdir(root_dir), root_dir
    assert output_stream

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        for build_info in _GetBuildInfos(
            root_dir,
            dm.stream,
            build_filename,
            build_filename_ignore,
        ):
            dm.stream.write(
                "{filename:<120}  {priority}\n".format(
                    filename="{}:".format(build_info.filename),
                    priority=build_info.configuration.Priority,
                ),
            )

        return dm.result


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
_BuildInfo                                  = namedtuple("_BuildInfo", ["filename", "configuration"])

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GetBuildInfos(root_dir, output_stream, build_filename, build_filename_ignore):
    root_dir = os.path.realpath(root_dir)

    build_infos = []

    output_stream.write("\nSearching for build files...")
    with output_stream.DoneManager(
        done_suffix=lambda: "{} found".format(inflect.no("build file", len(build_infos))),
        suffix="\n",
    ):
        name, ext = os.path.splitext(build_filename)

        for fullpath in FileSystem.WalkFiles(
            root_dir,
            include_file_base_names=[name],
            include_file_extensions=[ext],
        ):
            if os.path.exists(
                os.path.join(os.path.dirname(fullpath), build_filename_ignore),
            ):
                continue

            build_infos.append(
                _BuildInfo(
                    fullpath,
                    Configuration.FromBuildFile(
                        fullpath,
                        strip_path=root_dir,
                    ),
                ),
            )

        build_infos.sort(
            key=lambda item: item.configuration.Priority,
        )

    return build_infos


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
