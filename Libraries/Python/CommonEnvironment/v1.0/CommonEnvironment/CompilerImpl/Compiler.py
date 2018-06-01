# ----------------------------------------------------------------------
# |  
# |  Compiler.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-31 21:10:18
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Compiler object"""

import os
import sys

from CommonEnvironment.Interface import extensionmethod

from CommonEnvironment.CompilerImpl import CompilerImpl
from CommonEnvironment.CompilerImpl.CommandLine import CommandLineInvoke, CommandLineCleanOutputDir

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Compiler(CompilerImpl):

    # ----------------------------------------------------------------------
    # |  Public Properties
    IsCompiler                              = True
    InvokeVerb                              = "Compiling"

    # ----------------------------------------------------------------------
    # |  Public Methods
    @classmethod
    def Compile(cls, context, status_stream, verbose=False):
        return cls._Invoke(context, status_stream, verbose)

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def RemoveTemporaryArtifacts(context):
        """Remove any temporary files that where generated during the compliation process."""

        # Nothing to remove by default
        pass

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
CommandLineCompile                          = CommandLineInvoke
CommandLineClean                            = CommandLineCleanOutputDir
