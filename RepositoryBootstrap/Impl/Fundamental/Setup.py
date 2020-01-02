# ----------------------------------------------------------------------
# |  
# |  Setup.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-14 22:45:41
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-20.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Fundamental-specific repo setup"""

import os
import sys

sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
from RepositoryBootstrap.Impl import CommonEnvironmentImports
from RepositoryBootstrap.Impl.ActivationActivity.PythonActivationActivity import PythonActivationActivity
del sys.path[0]

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironmentImports.CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# For convenience, this script is taking all of the arguments that RepositoryBootstrap/Impl/Setup.py takes.
# In order to decrease coupling, don't using CommandLine (which takes a concrete list of arguments), but
# rather extract the arguments that we need from the actual args.

verbose = False
for arg in sys.argv[1:]:
    if arg.lower().endswith("verbose"):
        verbose = True
        break

PythonActivationActivity.Setup( CommonEnvironmentImports.StreamDecorator(sys.stdout),
                                verbose=verbose,
                              )
