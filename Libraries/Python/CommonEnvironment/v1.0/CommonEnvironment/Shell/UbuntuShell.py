# ----------------------------------------------------------------------
# |  
# |  UbuntuShell.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-11 12:48:23
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the UbuntuShell object"""

import os
import sys

from CommonEnvironment.Interface import staticderived, DerivedProperty
from CommonEnvironment.Shell.LinuxShellImpl import LinuxShellImpl

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Method '<...>' is abstract in class '<...>' but is not overridden> pylint: disable = W0223

@staticderived
class UbuntuShell(LinuxShellImpl):
    """Shell for Ubuntu systems"""

    Name                                    = DerivedProperty("Ubuntu")
