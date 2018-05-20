# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 14:02:41
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the InputProcessingMixin object"""

import os
import sys

from CommonEnvironment.Interface import Interface, abstractmethod

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class InputProcessingMixin(Interface):
    """Object that implements strategies for processing input"""

    # ----------------------------------------------------------------------
    # |  Methods defined in CompilerImpl; these methods forward to Impl
    # |  functions to clearly indicate to CompilerImpl that they are handled,
    # |  while also creating methods that must be implemented by derived
    # |  mixins.
    # ----------------------------------------------------------------------
    @classmethod
    def _GenerateMetadataItems(cls, *args, **kwargs):
        return _GenerateMetadataItemsImpl(*args, **kwargs)

    # ----------------------------------------------------------------------
    @classmethod
    def _GetInputItems(cls, *args, **kwargs):
        return _GetInputItemsImpl(*args, **kwargs)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @abstractmethod
    @staticmethod
    def _GenerateMetadataItemsImpl(invocation_group_inputs, metadata):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @abstractmethod
    @staticmethod
    def _GetInputItemsImpl(context):
        raise Exception("Abstract method")
