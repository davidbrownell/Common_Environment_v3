# ----------------------------------------------------------------------
# |  
# |  Setup_custom.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-03 22:12:13
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
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
fundamental_repo = os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
assert os.path.isdir(fundamental_repo), fundamental_repo

sys.path.insert(0, fundamental_repo)
from RepositoryBootstrap.SetupAndActivate import CurrentShell               # <Unused import> pylint: disable = W0614
from RepositoryBootstrap.SetupAndActivate.Configuration import *            # <Unused import> pylint: disable = W0614
del sys.path[0]

# ----------------------------------------------------------------------
def GetDependencies():
    """
    Returns information about the dependencies required by this repository.

    The return value should be an OrderedDict if the repository supports multiple configurations
    (aka is configurable) or a single Configuration if not.
    """

    return OrderedDict([ ( "python36", Configuration( "Python 3.6.5",
                                                      [],
                                                      VersionSpecs( [ VersionInfo("Python", "v3.6.5"), ],
                                                                    {},
                                                                  ),
                                                    ) ),
                         ( "python27", Configuration( "Python 2.7.14",
                                                      [],
                                                      VersionSpecs( [ VersionInfo("Python", "v2.7.14"), ],
                                                                    {},
                                                                  ),
                                                    ) ),
                       ])

# ----------------------------------------------------------------------
def GetCustomActions(debug, verbose, explicit_configurations):
    """
    Returns an action or list of actions that should be invoked as part of the setup process.

    Actions are generic command line statements defined in 
    <Common_Environment>/Libraries/Python/CommonEnvironment/v1.0/CommonEnvironment/Shell/Commands/__init__.py
    that are converted into statements appropriate for the current scripting language (in most
    cases, this is Bash on Linux systems and Batch or Powershell on Windows systems.
    """

    return [
        CurrentShell.Commands.SymbolicLink(
            os.path.join(fundamental_repo, "Scripts", "Formatter.py"),
            os.path.join(fundamental_repo, "src", "Formatter", "CommonEnvironment_Formatter", "Formatter.py"),
        )
    ]
