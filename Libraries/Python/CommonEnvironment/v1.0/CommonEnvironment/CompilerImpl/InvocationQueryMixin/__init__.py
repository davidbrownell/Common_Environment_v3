# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 14:09:14
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the InvocationQueryMixin object"""

import os
import sys

from CommonEnvironment.Interface import Interface, abstractmethod, override, mixin

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# <Too few public methods> pylint: disable = R0903
@mixin
class InvocationQueryMixin(Interface):
    """Object that implements strategies for determining if a compiler should be invoked based on input."""

    ( InvokeReason_Always,
      InvokeReason_Force,
      InvokeReason_PrevContextMissing,
      InvokeReason_NewerGenerators,
      InvokeReason_MissingOutput,
      InvokeReason_DifferentOutput,
      InvokeReason_NewerInput,
      InvokeReason_DifferentInput,
      InvokeReason_DifferentMetadata,
      InvokeReason_OptIn,
    ) = range(10)

    # ----------------------------------------------------------------------
    # |  Methods defined in CompilerImpl; these methods forward to Impl
    # |  functions to clearly indicate to CompilerImpl that they are handled,
    # |  while also creating methods that must be implemented by derived
    # |  mixins.
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetInvokeReason(cls, *args, **kwargs):
        return cls._GetInvokeReasonImpl(*args, **kwargs)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _PersistContext(cls, *args, **kwargs):
        return cls._PersistContextImpl(*args, **kwargs)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GetInvokeReasonImpl(context, output_stream):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _PersistContextImpl(context):
        raise Exception("Abstract method")
