# ----------------------------------------------------------------------
# |
# |  __init__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-03-11 09:40:51
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains for FormatterImpl object"""

import os

import CommonEnvironment
from CommonEnvironment import Interface

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class FormatterImpl(Interface.Interface):
    """\
    Abstract base class for formatters (automated functionality able to format 
    source code according to an established coding standard).
    """

    # ----------------------------------------------------------------------
    # |  Properties
    @Interface.abstractproperty
    def Name(self):
        """Name of the formatter"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def Description(self):
        """Description of the formatter"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def InputTypeInfo(self):
        """Type information for required input types"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  Methods
    @staticmethod
    @Interface.abstractmethod
    def Format(filename_or_content, *plugin_input_dirs, **plugin_args):
        """Formats the given input"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.extensionmethod
    def HasChanges(cls, filename_or_content, *plugin_input_dirs, **plugin_args):
        """Return True if the content would be changed by formatting if applied"""
        
        return cls.Format(filename_or_content, *plugin_input_dirs, **plugin_args)[1]
