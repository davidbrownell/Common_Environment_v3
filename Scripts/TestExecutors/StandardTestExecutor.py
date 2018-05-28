# ----------------------------------------------------------------------
# |  
# |  StandardTestExecutor.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-28 12:03:36
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the TestExecutor object"""

import datetime
import os
import sys
import time

from CommonEnvironment.Interface import staticderived
from CommonEnvironment import Process
from CommonEnvironment.TestExecutorImpl import TestExecutorImpl

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class TestExecutor(TestExecutorImpl):
    """Executor that invokes the test but doesn't generated code coverage information"""

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = "Standard"
    Description                             = "Executes the test without extracting code coverage information."

    # ----------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    def IsSupportedCompiler(compiler):
        # Any compile is supported
        return True

    # ----------------------------------------------------------------------
    @classmethod
    def Execute( cls,
                 compiler,
                 context,
                 command_line,
                 includes=None,
                 excludes=None,
                 verbose=False,
               ):
        start_time = time.time()

        result, output = Process.Execute(command_line)

        return cls.ExecuteResult( result,
                                  output,
                                  str(datetime.timedelta(seconds=(time.time() - start_time))),
                                )
