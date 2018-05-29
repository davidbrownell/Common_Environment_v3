# ----------------------------------------------------------------------
# |  
# |  TestTypeMetadata.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-28 20:54:57
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the TestTypeMetadata object and default values"""

import os
import sys

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class TestTypeMetadata(object):
    """
    Information about tests; this information can be used by other scripts
    to customize behavior based on these properties.
    """

    # ----------------------------------------------------------------------
    # |  Public Types
    ( DeploymentType_Local,
      DeploymentType_ProductionLike,
      DeploymentType_Production,
    ) = range(3)

    # ----------------------------------------------------------------------
    def __init__( self,
                  name,
                  use_code_coverage,
                  execute_in_parallel,
                  deployment,
                  description,
                ):
        self.Name                           = name
        self.UseCodeCoverage                = use_code_coverage
        self.ExecuteInParallel              = execute_in_parallel
        self.Deployment                     = deployment
        self.Description                    = description

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
TEST_TYPES                                  = [                   # Name                        Code Coverage   Execute in Parallel     Deployment                                          Description                 
                                                TestTypeMetadata( "UnitTests",                  True,           True,                   None,                                               "Tests that exercise a single function or method" ),
                                                TestTypeMetadata( "FunctionalTests",            True,           True,                   None,                                               "Tests that exercise multiple functions or methods" ),
                                                TestTypeMetadata( "IntegrationTests",           False,          True,                   TestTypeMetadata.DeploymentType_Local,              "Tests that exercise 1-2 components with local setup requirements" ),
                                                TestTypeMetadata( "SystemTests",                False,          False,                  TestTypeMetadata.DeploymentType_ProductionLike,     "Tests that exercise 1-2 components with production-like setup requirements" ),
                                                TestTypeMetadata( "LocalEndToEndTests",         False,          False,                  TestTypeMetadata.DeploymentType_Local,              "Tests that exercise 2+ components with local setup requirements" ),
                                                TestTypeMetadata( "EndToEndTests",              False,          True,                   TestTypeMetadata.DeploymentType_Production,         "Tests that exercise 2+ components with production setup requirements" ),
                                                TestTypeMetadata( "BuildVerificationTests",     False,          False,                  TestTypeMetadata.DeploymentType_Production,         "Tests intended to determine at a high level if a build/deployment is working as expected" ),
                                                TestTypeMetadata( "PerformanceTests",           False,          False,                  TestTypeMetadata.DeploymentType_Production,         "Tests measuring performance across a variety of dimensions" ),
                                              ]
