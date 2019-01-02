# ----------------------------------------------------------------------
# |  
# |  CommonEnvironmentImports.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-02 13:33:29
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""
Imports from the Common_Environment repository used during the bootstrap process.
This file is imported early within the boostrapping process, and in a variety of
different environments. We can't make too many assumptions about the state of the
system when we are here.
"""

# <third part inport <...> should be placed before <...>> pylint: disable = C0411
# <Unused import> pylint: disable = W0611

import os
import sys

import RepositoryBootstrap
from RepositoryBootstrap import Constants

# ----------------------------------------------------------------------
COMMON_ENVIRONMENT_PATH                     = os.path.join(RepositoryBootstrap.GetFundamentalRepository(), Constants.LIBRARIES_SUBDIR, "Python", "CommonEnvironment", "v1.0")

assert os.path.isdir(COMMON_ENVIRONMENT_PATH), COMMON_ENVIRONMENT_PATH
sys.path.insert(0, COMMON_ENVIRONMENT_PATH)

import CommonEnvironment

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Interface
from CommonEnvironment import Process
from CommonEnvironment import RegularExpression
from CommonEnvironment.Shell.All import CurrentShell, ALL_TYPES as Shell_ALL_TYPES
from CommonEnvironment.SourceControlManagement.All import GetSCM, ALL_TYPES as SourceControlManagement_ALL_TYPES
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import StringHelpers
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization as FundamentalTypesStringSerialization

del sys.path[0]
