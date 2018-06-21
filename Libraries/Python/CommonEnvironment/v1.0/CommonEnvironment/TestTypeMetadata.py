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

import enum
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
    class DeploymentType(enum.Enum):
        Local                               = 1
        ProductionLike                      = 2
        Production                          = 3

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
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)

# ----------------------------------------------------------------------
# <Line too long> pylint: disable = C0301
# <Wrong hanging indentation> pylint: disable = C0330

TEST_TYPES                                  = [                   # Name                        Code Coverage   Execute in Parallel     Deployment                                          Description                 
                                                TestTypeMetadata( "UnitTests",                  True,           True,                   None,                                               "Tests that exercise a single function or method" ),
                                                TestTypeMetadata( "FunctionalTests",            True,           True,                   None,                                               "Tests that exercise multiple functions or methods" ),
                                                TestTypeMetadata( "IntegrationTests",           False,          True,                   TestTypeMetadata.DeploymentType.Local,              "Tests that exercise 1-2 components with local setup requirements" ),
                                                TestTypeMetadata( "SystemTests",                False,          False,                  TestTypeMetadata.DeploymentType.ProductionLike,     "Tests that exercise 1-2 components with production-like setup requirements" ),
                                                TestTypeMetadata( "LocalEndToEndTests",         False,          False,                  TestTypeMetadata.DeploymentType.Local,              "Tests that exercise 2+ components with local setup requirements" ),
                                                TestTypeMetadata( "EndToEndTests",              False,          True,                   TestTypeMetadata.DeploymentType.Production,         "Tests that exercise 2+ components with production setup requirements" ),
                                                TestTypeMetadata( "BuildVerificationTests",     False,          False,                  TestTypeMetadata.DeploymentType.Production,         "Tests intended to determine at a high level if a build/deployment is working as expected" ),
                                                TestTypeMetadata( "PerformanceTests",           False,          False,                  TestTypeMetadata.DeploymentType.Production,         "Tests measuring performance across a variety of dimensions" ),
                                              ]
