# ----------------------------------------------------------------------
# |
# |  PyPiBuildImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-03-18 20:46:54
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains methods that help when writing build files that interact with PyPi"""

import os
import sys
import textwrap

import six

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
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def CreateBuildFunc(script_dir):
    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    @CommandLine.Constraints(
        output_stream=None,
    )
    def Build(
        output_stream=sys.stdout,
    ):
        """Builds a python package"""

        with StreamDecorator(output_stream).DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            dm.result = Process.Execute("python setup.py sdist", dm.stream)
            return dm.result

    # ----------------------------------------------------------------------

    return Build


# ----------------------------------------------------------------------
def CreateCleanFunc(script_dir):
    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    @CommandLine.Constraints(
        output_stream=None,
    )
    def Clean(
        output_stream=sys.stdout,
    ):
        """Cleans previously built python package contents"""

        with StreamDecorator(output_stream).DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            found_dir = False

            for item in os.listdir(script_dir):
                fullpath = os.path.join(script_dir, item)
                if not os.path.isdir(fullpath):
                    continue

                if item == "dist" or os.path.splitext(item)[1] == ".egg-info":
                    dm.stream.write("Removing '{}'...".format(item))
                    with dm.stream.DoneManager():
                        FileSystem.RemoveTree(fullpath)

                    found_dir = True

            if not found_dir:
                dm.stream.write("No content found.\n")

            return dm.result

    # ----------------------------------------------------------------------

    return Clean


# ----------------------------------------------------------------------
def CreateDeployFunc(script_dir):
    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    @CommandLine.Constraints(
        output_stream=None,
    )
    def Deploy(
        production=False,
        output_stream=sys.stdout,
    ):
        with StreamDecorator(output_stream).DoneManager(
            line_prefix="",
            prefix="\nResults: ",
            suffix="\n",
        ) as dm:
            temp_directory = CurrentShell.CreateTempDirectory()
            assert os.path.isdir(temp_directory), temp_directory

            with CallOnExit(lambda: FileSystem.RemoveTree(temp_directory)):
                import getpass

                username = six.moves.input("Enter your PyPi username: ")
                if not username:
                    dm.result = 1
                    return dm.result

                password = getpass.getpass("Enter your PyPi password: ")
                if not password:
                    dm.result = 1
                    return dm.result

                with open(os.path.join(temp_directory, ".pypirc"), "w") as f:
                    f.write(
                        textwrap.dedent(
                            """\
                            [distutils]
                            index-servers =
                                pypi

                            [pypi]
                            repository: {repo}
                            username: {username}
                            password: {password}
                            """,
                        ).format(
                            repo="https://upload.pypi.org/legacy/" if production else "https://test.pypi.org/legacy/",
                            username=username,
                            password=password,
                        ),
                    )

                os.environ["HOME"] = temp_directory

                previous_dir = os.getcwd()
                os.chdir(script_dir)

                with CallOnExit(lambda: os.chdir(previous_dir)):
                    dm.result = Process.Execute('twine upload "dist/*"', dm.stream)

                return dm.result

    # ----------------------------------------------------------------------

    return Deploy
