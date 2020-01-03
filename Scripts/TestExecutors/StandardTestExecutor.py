# ----------------------------------------------------------------------
# |  
# |  StandardTestExecutor.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-28 12:03:36
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-20.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the TestExecutor object"""

import datetime
import os
import time

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment import Process
from CommonEnvironment.TestExecutorImpl import TestExecutorImpl

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class TestExecutor(TestExecutorImpl):
    """Executor that invokes the test but doesn't generated code coverage information"""

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = DerivedProperty("Standard")
    Description                             = DerivedProperty("Executes the test without extracting code coverage information.")

    # ----------------------------------------------------------------------
    # |  Public Methods
    @staticmethod
    @override
    def IsSupportedCompiler(compiler):
        # All compilers are supported
        return True

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def Execute( cls,
                 on_status_update,
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
