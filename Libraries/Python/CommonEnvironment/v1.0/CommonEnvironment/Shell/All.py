# ----------------------------------------------------------------------
# |  
# |  All.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-01 08:55:20
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""All items from this module"""

import os
import sys

from CommonEnvironment.Shell.UbuntuShell import UbuntuShell
from CommonEnvironment.Shell.WindowsShell import WindowsShell
from CommonEnvironment.Shell.WindowsPowerShell import WindowsPowerShell

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
ALL_TYPES                                   = [ WindowsPowerShell,
                                                WindowsShell, 
                                                UbuntuShell,
                                              ]

# ----------------------------------------------------------------------
def _GetShell():
    # ----------------------------------------------------------------------
    def GetPlatform():
        result = os.getenv("DEVELOPMENT_ENVIRONMENT_LINUX_NAME_OVERRIDE")
        if result:
            return result.lower()

        try:
            import distro
            
            result = distro.linux_distribution(full_distribution_name=False)[0].lower()
            if result == "debian":
                result = "ubuntu"

            return result

        except ImportError:
            pass

        return os.name.lower()

    # ----------------------------------------------------------------------

    plat = GetPlatform()
    
    for shell in ALL_TYPES:
        if shell.IsActive(plat):
            return shell.DecorateWithCommands()

    raise Exception("No shell found for '{}'".format(plat))

# ----------------------------------------------------------------------

CurrentShell                                = _GetShell()
