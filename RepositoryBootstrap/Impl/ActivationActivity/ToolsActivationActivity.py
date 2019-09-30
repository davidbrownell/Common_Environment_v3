# ----------------------------------------------------------------------
# |
# |  ToolsActivationActivity.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-06 22:40:57
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains the ToolsActivationActivity object"""

import os

import inflect as inflect_mod

from RepositoryBootstrap import Constants
from RepositoryBootstrap.Impl import CommonEnvironmentImports
from RepositoryBootstrap.Impl.ActivationActivity import ActivationActivity

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironmentImports.CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
IGNORE_AS_TOOL_DIR_FILENAME                 = "IgnoreAsTool"

# ----------------------------------------------------------------------
@CommonEnvironmentImports.Interface.staticderived
class ToolsActivationActivity(ActivationActivity):

    # ----------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ----------------------------------------------------------------------
    Name                                    = CommonEnvironmentImports.Interface.DerivedProperty("Tools")
    DelayExecute                            = CommonEnvironmentImports.Interface.DerivedProperty(False)

    # ----------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ----------------------------------------------------------------------
    @classmethod
    @CommonEnvironmentImports.Interface.override
    def _CreateCommandsImpl(
        cls,
        output_stream,
        verbose_stream,
        configuration,
        repositories,
        version_specs,
        generated_dir,
    ):
        version_info = [] if not version_specs else version_specs.Tools

        nonlocals = CommonEnvironmentImports.CommonEnvironment.Nonlocals(
            tools=0,
        )

        actions = []
        paths = []

        verbose_stream.write("Searching...")
        with verbose_stream.DoneManager(
            done_suffix=lambda: "{} found".format(inflect.no("tool", nonlocals.tools)),
        ) as dm:
            for repository in repositories:
                potential_tools_fullpath = os.path.join(
                    repository.Root,
                    Constants.TOOLS_SUBDIR,
                )
                if not os.path.isdir(potential_tools_fullpath):
                    continue

                for item in os.listdir(potential_tools_fullpath):
                    fullpath = os.path.join(potential_tools_fullpath, item)
                    if not os.path.isdir(fullpath):
                        continue

                    if os.path.exists(
                        os.path.join(fullpath, IGNORE_AS_TOOL_DIR_FILENAME),
                    ):
                        continue

                    try:
                        fullpath = cls.GetVersionedDirectory(version_info, fullpath)
                        assert os.path.isdir(fullpath), fullpath

                    except Exception as ex:
                        dm.stream.write("WARNING: {}\n".format(str(ex)))
                        continue

                    # If the tool is just there to prevent warnings, don't count it as an
                    # offical tool
                    subdirs = os.listdir(fullpath)

                    if len(subdirs) == 1 and subdirs[0].lower() == "readme.txt":
                        continue

                    # If here, we are looking at a valid tool
                    nonlocals.tools += 1

                    # Look for an activation customization script here. If it exists, invoke that rather than our custom activities
                    potential_activate_fullpath = os.path.join(
                        fullpath,
                        CommonEnvironmentImports.CurrentShell.CreateScriptName(
                            Constants.ACTIVATE_ENVIRONMENT_NAME,
                        ),
                    )
                    if os.path.isfile(potential_activate_fullpath):
                        actions.append(
                            CommonEnvironmentImports.CurrentShell.Commands.Call(
                                potential_activate_fullpath,
                            ),
                        )
                        continue

                    # Add well-known suffixes to the path if they exist
                    existing_paths = []

                    for potential_suffix in [
                        "bin",
                        "sbin",
                        os.path.join("usr", "bin"),
                        os.path.join("usr", "sbin"),
                    ]:
                        potential_path = os.path.join(fullpath, potential_suffix)
                        if os.path.isdir(potential_path):
                            existing_paths.append(potential_path)

                    if not existing_paths:
                        existing_paths.append(fullpath)

                    paths += existing_paths

        if paths:
            actions.append(
                CommonEnvironmentImports.CurrentShell.Commands.AugmentPath(paths),
            )

        return actions
