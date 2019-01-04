# ----------------------------------------------------------------------
# |
# |  __init__.py
# |
# |  David Brownell <david.brownell@microsoft.com>
# |      2018-12-16 20:56:21
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Plugin object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Plugin(Interface.Interface):
    # ----------------------------------------------------------------------
    # |  Types
    STANDARD_PRIORITY                       = 10000

    # ----------------------------------------------------------------------
    # |  Properties
    @Interface.abstractproperty
    def Name(self):
        """Name of the plugin"""
        raise Exception("Abstract property")

    @Interface.abstractproperty
    def Priority(self):
        """Integer priority value; plugins with lower priorities are executed first"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  Methods
    @staticmethod
    @Interface.extensionmethod
    def PreprocessLines(lines):
        """Preprocesses the provided lines"""
        return lines
    
    # ----------------------------------------------------------------------
    @staticmethod
    @Interface.abstractmethod
    def Decorate(lines, *args, **kwargs):
        """Returns a list of decorated lines"""
        raise Exception("Abstract method")
