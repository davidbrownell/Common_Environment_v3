# ----------------------------------------------------------------------
# |  
# |  Build.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-06-02 21:36:36
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-20.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Builds the Common_Environment Docker image"""

import os
import sys

import CommonEnvironment
from CommonEnvironment import BuildImpl
from CommonEnvironment.BuildImpl import DockerBuildImpl
from CommonEnvironment import CommandLine

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

APPLICATION_NAME                            = "Docker_CommonEnvironment"

Build                                       = DockerBuildImpl.CreateRepositoryBuildFunc( "Common_Environment",
                                                                                         os.path.join(_script_dir, "..", ".."),
                                                                                         "dbrownell",
                                                                                         "common_environment",
                                                                                         "phusion/baseimage:latest",
                                                                                         "David Brownell <db@DavidBrownell.com>",
                                                                                         repository_source_excludes=[],
                                                                                         repository_activation_configurations=[ "python36",
                                                                                                                                "python27",
                                                                                                                              ],
                                                                                       )

Clean                                       = DockerBuildImpl.CreateRepositoryCleanFunc()


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
