# ----------------------------------------------------------------------
# |  
# |  Build.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-08-15 16:09:30
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Builds the Common_Environment Python distribution"""

import os
import re
import sys
import textwrap

import six

import CommonEnvironment
from CommonEnvironment import BuildImpl
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

APPLICATION_NAME                            = "Python_CommonEnvironment"

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( output_stream=None,
                        )
def Build( output_stream=sys.stdout,
         ):
    """Builds a python package"""

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        dm.result = Process.Execute("python setup.py sdist", dm.stream)
        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( output_stream=None,
                        )
def Clean( output_stream=sys.stdout,
         ):
    """Cleans previously build python package contents"""
    
    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        found_dir = False

        for potential_dir in [ "CommonEnvironment.egg-info",
                               "dist",
                             ]:
            fullpath = os.path.join(_script_dir, potential_dir)
            if not os.path.isdir(fullpath):
                continue

            dm.stream.write("Removing '{}'...".format(potential_dir))
            with dm.stream.DoneManager():
                FileSystem.RemoveTree(fullpath)

            found_dir = True

        if not found_dir:
            dm.stream.write("No content found.\n")

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( output_stream=None,
                        )
def Deploy( production=False,
            output_stream=sys.stdout,
          ):
    """Deploys a previously build python package to a test or production package repository"""

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        temp_directory = CurrentShell.CreateTempDirectory()
        assert os.path.isdir(temp_directory), temp_directory

        with CallOnExit(lambda: FileSystem.RemoveTree(temp_directory)):
            import getpass

            username = six.moves.input("Enter your username: ")
            if not username:
                dm.result = 1
                return dm.result

            password = getpass.getpass("Enter your password: ")
            if not password:
                dm.result = 1
                return dm.result
            
            with open(os.path.join(temp_directory, ".pypirc"), 'w') as f:
                f.write(textwrap.dedent(
                    """\
                    [distutils]
                    index-servers =
                        pypi

                    [pypi]
                    repository: {repo}
                    username: {username}
                    password: {password}
                    """).format( repo="https://upload.pypi.org/legacy/" if production else "https://test.pypi.org/legacy/",
                                 username=username,
                                 password=password,
                               ))

            os.environ["HOME"] = temp_directory

            dm.result = Process.Execute('twine upload "dist/*"', dm.stream)
            return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(BuildImpl.Main(BuildImpl.Configuration( name=APPLICATION_NAME,
                                                         requires_output_dir=False,
                                                       )))
    except KeyboardInterrupt:
        pass
