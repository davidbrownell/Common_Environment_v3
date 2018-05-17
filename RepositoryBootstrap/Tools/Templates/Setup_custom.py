# ----------------------------------------------------------------------
# |  
# |  Setup_custom.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-03 22:12:13
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  To setup an environment, run:
# | 
# |     Setup(.cmd|.ps1|.sh) [/debug] [/verbose] [/configuration=<config_name>]*
# |  
# ----------------------------------------------------------------------

import os
import sys

from collections import OrderedDict

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

fundamental_repo = os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
assert os.path.isdir(fundamental_repo), fundamental_repo

sys.path.insert(0, fundamental_repo)
from RepositoryBootstrap.Configuration import *
from RepositoryBootstrap.Impl.CommonEnvironmentImports import CurrentShell
del sys.path[0]

# ----------------------------------------------------------------------
def GetDependencies():
    """
    Returns information about the dependencies required by this repository.

    The return value should be an OrderedDict if the repository supports multiple configurations
    (aka is configurable) or a single Configuration if not.
    """

    raise Exception("Remove this exception once you have updated the configuration for your new repository (GetDependencies).")

    # To support multiple configurations...
    return OrderedDict([ ( "Config1", Configuration( "A description of Config1; this configuration uses python36",
                                                     [ Dependency( "0EAA1DCF22804F90AD9F5A3B85A5D706",  # Id for Common_Environment; found in <Common_Environment>/__RepositoryId__
                                                                   "Common_Environment",                # Name used if Common_Environment cannot be found during setup
                                                                   "python36",                          # Configuration value used when activating Common_Environment
                                                                 ),
                                                       # Other dependencies go here (if any)    
                                                     ],
                                                     # By default, the most recent version of all tools and libraries will be activated for this repository and its dependencies.
                                                     # If necessary, you can override this behavior by specifying specific versions for tools that should be used when activating
                                                     # this repository with this configuration.
                                                     VersionSpecs( # Tools
                                                                   [ VersionInfo("Some Tool", "v0.0.1"), ],
                                                                   # Libraries, organized by language
                                                                   { "Python" : [ VersionInfo("Some Library", "v1.2.3"), ],
                                                                   },
                                                                 ),
                                                    ) ),
                         ( "Config2", Configuration( "A descrption of Config2; this configuration uses python27",
                                                     [ Dependency( "0EAA1DCF22804F90AD9F5A3B85A5D706",  # Id for Common_Environment; found in <Common_Environment>/__RepositoryId__
                                                                  "Common_Environment",                # Name used if Common_Environment cannot be found during setup
                                                                  "python27",                          # Configuration value used when activating Common_Environment
                                                                ),
                                                       # Other dependencies go here (if any)
                                                     ],
                                                     # By default, the most recent version of all tools and libraries will be activated for this repository and its dependencies.
                                                     # If necessary, you can override this behavior by specifying specific versions for tools that should be used when activating
                                                     # this repository with this configuration.
                                                     VersionSpecs( # Tools
                                                                   [ VersionInfo("Some Other Tool", "v0.2.1"), ],
                                                                   # Libraries, organized by language
                                                                   { "C++" : [ VersionInfo("Some Library", "v1.2.3"), ],
                                                                   },
                                                                 ),
                                                   ) ),
                       ])

    # To support a single configuration...
    Configuration( "A description of Config1; this configuration uses python36",
                   [ Dependency( "0EAA1DCF22804F90AD9F5A3B85A5D706",  # Id for Common_Environment; found in <Common_Environment>/__RepositoryId__
                                 "Common_Environment",                # Name used if Common_Environment cannot be found during setup
                                 "python36",                          # Configuration value used when activating Common_Environment
                               ),
                     # Other dependencies go here (if any)    
                   ],
                   # By default, the most recent version of all tools and libraries will be activated for this repository and its dependencies.
                   # If necessary, you can override this behavior by specifying specific versions for tools that should be used when activating
                   # this repository with this configuration.
                   VersionSpecs( # Tools
                                 [ VersionInfo("Some Tool", "v0.0.1"), ],
                                 # Libraries, organized by language
                                 { "Python" : [ VersionInfo("Some Library", "v1.2.3"), ],
                                 },
                               ),
                 )

# ----------------------------------------------------------------------
def GetCustomActions(debug, verbose, explicit_configurations):
    """
    Returns an action or list of actions that should be invoked as part of the setup process.

    Actions are generic command line statements defined in 
    <Common_Environment>/Libraries/Python/CommonEnvironment/v1.0/CommonEnvironment/Shell/Commands/__init__.py
    that are converted into statements appropriate for the current scripting language (in most
    cases, this is Bash on Linux systems and Batch or Powershell on Windows systems.
    """

    raise Exception("Remove this exception once you have updated the configuration for your new repository (GetCustomActions).")

    return [ CurrentShell.Commands.Message("This is a sample message"),
           ]
