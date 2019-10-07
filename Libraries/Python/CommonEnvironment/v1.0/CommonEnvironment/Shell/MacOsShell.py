# ----------------------------------------------------------------------
# |
# |  MacOsShell.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-10-07 19:25:23
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains the MacOsShell object"""

import os

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, DerivedProperty
from CommonEnvironment.Shell.LinuxShellImpl import LinuxShellImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Method '<...>' is abstract in class '<...>' but is not overridden> pylint: disable = W0223


@staticderived
class MacOsShell(LinuxShellImpl):
    """Shell for MacOS systems"""

    Name                                    = DerivedProperty("Darwin")
