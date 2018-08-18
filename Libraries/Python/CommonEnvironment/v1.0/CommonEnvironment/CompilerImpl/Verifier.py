# ----------------------------------------------------------------------
# |  
# |  Verifier.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 20:33:22
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Verifier object"""

import os
import sys

from CommonEnvironment.Interface import DerivedProperty

from CommonEnvironment.CompilerImpl import CompilerImpl
from CommonEnvironment.CompilerImpl.CommandLine import CommandLineInvoke
from CommonEnvironment.CompilerImpl.InputProcessingMixin.IndividualInputProcessingMixin import IndividualInputProcessingMixin
from CommonEnvironment.CompilerImpl.InvocationQueryMixin.AlwaysInvocationQueryMixin import AlwaysInvocationQueryMixin
from CommonEnvironment.CompilerImpl.OutputMixin.NoOutputMixin import NoOutputMixin

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Method is abstract in class> pylint: disable = W0223

# ----------------------------------------------------------------------
class Verifier( IndividualInputProcessingMixin,
                AlwaysInvocationQueryMixin,
                NoOutputMixin,
                CompilerImpl,
              ):
    # ----------------------------------------------------------------------
    # |  Public Properties
    IsVerifier                              = True
    InvokeVerb                              = DerivedProperty("Verifying")

    # ----------------------------------------------------------------------
    # |  Public Methods
    @classmethod
    def Verify(cls, context, status_stream, verbose=False):
        return cls._Invoke(context, status_stream, verbose)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
CommandLineVerify                           = CommandLineInvoke
