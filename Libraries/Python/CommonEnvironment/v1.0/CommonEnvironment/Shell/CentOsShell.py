# ----------------------------------------------------------------------
# |
# |  CentOsShell.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-08-30 19:25:23
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-22.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains the CentOsShell object"""

import os

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.Shell.LinuxShellImpl import LinuxShellImpl

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Method '<...>' is abstract in class '<...>' but is not overridden> pylint: disable = W0223


@staticderived
class CentOsShell(LinuxShellImpl):
    """Shell for CentOS systems"""

    Name                                    = DerivedProperty("CentOS")

    # ----------------------------------------------------------------------
    @staticderived
    @override
    class CommandVisitor(LinuxShellImpl.CommandVisitor):
        try:
            import distro

            if int(distro.major_version()) < 7:
                # ----------------------------------------------------------------------
                @classmethod
                @override
                def OnSymbolicLink(cls, command):
                    # Older versions of CentOS do not support relative paths
                    return super(CentOsShell.CommandVisitor, cls).OnSymbolicLink(
                        command,
                        no_relative_flag=True,
                    )

        except ImportError:
            pass
