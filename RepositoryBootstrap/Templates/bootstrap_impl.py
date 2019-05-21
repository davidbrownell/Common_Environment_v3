# ----------------------------------------------------------------------
# |
# |  bootstrap_impl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-05-21 08:23:15
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Performs repository bootstrap activities (Enlistment and setup)"""

import os
import shutil
import sys
import textwrap

from collections import OrderedDict

import inflect as inflect_mod
import six

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import StringHelpers

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# Tuples in the form:
#   ("<repo name>", "<clone command line>", "<setup command suffix>" or None) 
_REPO_DATA                                  = [
    ( "Common_cpp_Clang_8", 'git clone https://github.com/davidbrownell/Common_cpp_Clang_8 "{output_dir}"', "/configuration=python"),
]

_ACTIVATION_REPO_NAME                       = "Common_cpp_Clang_8"
_ACTIVATION_REPO_CONFIGURATION              = "python"

raise Exception("Remove this exception when '_REPO_DATA', '_ACTIVATION_REPO_NAME', and '_ACTIVATION_REPO_CONFIGURATION' have been updated for your environment")

# ----------------------------------------------------------------------
inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints(
    output_dir=CommandLine.DirectoryTypeInfo(),
    output_stream=None,
)
def EntryPoint(
    output_dir,
    output_stream=sys.stdout,
):
    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        repo_data = OrderedDict()
        enlistment_repositories = []
        activation_repo_dir = None

        dm.stream.write("Calculating enlistment repositories...")
        with dm.stream.DoneManager(
            done_suffix=lambda: "{} found".format(inflect.no("repository", len(enlistment_repositories))),
            suffix="\n",
        ) as this_dm:
            for data in _REPO_DATA:
                repo_name = data[0]

                output_dir = os.path.join(output_dir, repo_name.replace("_", os.path.sep))
                if not os.path.isdir(output_dir):
                    enlistment_repositories.append((output_dir, data))

                repo_data[output_dir] = data

                if repo_name == _ACTIVATION_REPO_NAME:
                    assert activation_repo_dir is None, activation_repo_dir
                    activation_repo_dir = output_dir

        if activation_repo_dir is None:
            raise Exception("'{}' was not found; is it in _REPO_DATA?".format(_ACTIVATION_REPO_NAME))

        if enlistment_repositories:
            dm.stream.write("Enlisting in {}...".format(inflect.no("repository", len(enlistment_repositories))))
            with dm.stream.DoneManager(
                suffix="\n",
            ) as enlist_dm:
                for index, (output_dir, data) in enumerate(enlistment_repositories):
                    enlist_dm.stream.write("'{}' ({} of {})...".format(data[0], index + 1, len(enlistment_repositories)))
                    with enlist_dm.stream.DoneManager() as this_dm:
                        temp_directory = CurrentShell.CreateTempDirectory()

                        command_line = data[1].format(
                            output_dir=temp_directory,
                        )

                        this_dm.result, output = Process.Execute(
                            data[1].format(
                                output_dir=temp_directory,
                            ),
                        )
                        if this_dm.result != 0:
                            this_dm.stream.write(output)
                            return this_dm.result

                        FileSystem.MakeDirs(os.path.dirname(output_dir))
                        shutil.move(temp_directory, output_dir)

        dm.stream.write("Setting up {}...".format(inflect.no("repository", len(repo_data))))
        with dm.stream.DoneManager(
            suffix="\n",
        ) as setup_dm:
            command_line_template = "Setup{} {{suffix}}".format(CurrentShell.ScriptExtension)

            for index, (output_dir, data) in enumerate(six.iteritems(repo_data)):
                setup_dm.stream.write("'{}' ({} of {})...".format(data[0], index + 1, len(repo_data)))
                with setup_dm.stream.DoneManager() as this_dm:
                    prev_dir = os.getcwd()
                    os.chdir(output_dir)

                    with CallOnExit(lambda: os.chdir(prev_dir)):
                        command_line = command_line_template.format(
                            suffix=data[2] or "",
                        )

                        if CurrentShell.CategoryName == "Windows":
                            command_line = command_line.replace("=", "_EQ_")
                        elif CurrentShell.CategoryName == "Linux":
                            command_line = "./{}".format(command_line)

                        this_dm.result, output = Process.Execute(command_line)
                        if this_dm.result != 0:
                            this_dm.stream.write(output)
                            return this_dm.result

        dm.stream.write(
            StringHelpers.LeftJustify(
                textwrap.dedent(
                    """\
                    
                    
                    
                    
                    
                    
                    # ----------------------------------------------------------------------
                    # ----------------------------------------------------------------------
                    # ----------------------------------------------------------------------

                    The enlistment and setup of all repositories was successful. To begin
                    development activities, please run the following command. Note that
                    this command must be run every time you open a new terminal window.

                        {} {}

                    # ----------------------------------------------------------------------
                    # ----------------------------------------------------------------------
                    # ----------------------------------------------------------------------

                    """,
                ).format(
                    os.path.join(activation_repo_dir, "Activate{}".format(CurrentShell.ScriptExtension)),
                    _ACTIVATION_REPO_CONFIGURATION or "",
                ),
                16,
                skip_first_line=False,
            ),
        )

        return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
