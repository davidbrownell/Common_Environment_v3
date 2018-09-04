# ----------------------------------------------------------------------
# |  
# |  CodeGenerator.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-31 21:07:04
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the CodeGenerator object"""

import os
import sys

from CommonEnvironment.Interface import DerivedProperty

from CommonEnvironment.CompilerImpl import CompilerImpl
from CommonEnvironment.CompilerImpl.CommandLine import CommandLineInvoke, CommandLineCleanOutputDir

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# <Method '<...>' is abstract in class '<...>' but is not overridden> pylint: disable = W0223
class CodeGenerator(CompilerImpl):

    # ----------------------------------------------------------------------
    # |  Public Properties
    IsCodeGenerator                         = True
    InvokeVerb                              = DerivedProperty("Generating")

    # ----------------------------------------------------------------------
    # |  Public Methods
    @classmethod
    def Generate(cls, context, status_stream, verbose=False):
        return cls._Invoke(context, status_stream, verbose)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
CommandLineGenerate                         = CommandLineInvoke
CommandLineClean                            = CommandLineCleanOutputDir
