# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 14:13:00
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the OutputMixin object"""

import os
import sys

from CommonEnvironment.Interface import Interface, abstractmethod

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class OutputMixin(Interface):
    """Object that implements strategies for processing output"""

    # ----------------------------------------------------------------------
    # |  Methods defined in CompilerImpl; these methods forward to Impl
    # |  functions to clearly indicate to CompilerImpl that they are handled,
    # |  while also creating methods that must be implemented by derived
    # |  mixins.
    # ----------------------------------------------------------------------
    @classmethod
    def _GetOutputFilenames(cls, *args, **kwargs):
        return _GetOutputFilenamesImpl(*args, **kwargs)

    # ----------------------------------------------------------------------
    @classmethod
    def _CleanImpl(cls, *args, **kwargs):
        return _CleanImplEx(*args, **kwargs)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @abstractmethod
    @staticmethod
    def _GetOutputFilenamesImpl(context):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @abstractmethod
    @staticmethod
    def _CleanImplEx(context, output_stream):
        raise Exception("Abstract method")
