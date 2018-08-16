# ----------------------------------------------------------------------
# |  
# |  Build.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-08-15 16:09:30
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Builds the Common_Environment Python distribution"""

import os
import sys

from CommonEnvironment import BuildImpl
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
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
            dm.stream.write("No content was found.\n")

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
        dm.result = Process.Execute( "twine upload --repository-url {url} dist/*".format( url="https://pypi.org/" if production else "https://test.pypi.org/legacy/",
                                                                                        ),
                                     dm.stream,
                                   )
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
