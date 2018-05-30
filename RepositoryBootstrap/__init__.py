# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-01 18:32:46
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Code helpful during the bootstrap process."""

import os
import sys

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def GetFundamentalRepository():
    """Returns the location of the fundamental repository."""

    from RepositoryBootstrap import Constants

    value = os.getenv(Constants.DE_FUNDAMENTAL_ROOT_NAME)
    if value is None:
        # If here, we aren't running in a standard environment and are likely
        # running as part of a frozen exe. See if we are running within a file
        # system that is similar to Common_Environment.
        assert "python" not in sys.executable.lower(), sys.executable

        potential_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        if os.path.isdir(potential_dir):
            value = potential_dir

    if value is not None and value.endswith(os.path.sep):
        value = value[:-len(os.path.sep)]

    return value

# ----------------------------------------------------------------------

# This file may be invoked by our included version of python; if so, all imports
# will work as expected. However, this file may be invoked by a frozen executable.
# In those cases, go through a bit more work to ensure that these imports work as
# expected.
try:
    import inflect
    import six
    import wrapt

    # If here, everything was found and all is good

except ImportError:

    # If here, we are in a frozen environment. Hard-code an import path to
    # a known python location relative to the fundamental dir; this implies
    # that the environment has been at least setup.
    #
    # It doesn't matter which version of python we use, as they should be
    # a part of all of them.

    fundamental_repo = GetFundamentalRepository()

    python_root = os.path.join(fundamental_repo, "Tools", "Python", "v2.7.14")
    assert os.path.isdir(python_root), python_root

    for suffix in [ os.path.join("Windows", "Lib", "site-packages"),
                    os.path.join("Ubuntu", "lib", "python2.7", "site-packages"),
                  ]:
        potential_dir = os.path.join(python_root, suffix)
        if os.path.isdir(potential_dir):
            sys.path.insert(0, potential_dir)
            break

    # Try to import again

    # <Imports are not grouped> pylint: disable = C0412
    import inflect
    import six
    import wrapt

    del sys.path[0]

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
@wrapt.decorator
def ToolRepository(wrapped, instance, args, kwargs):
    """
    Signals that a repository is a tool repository (a repository that
    contains items that help in the development process but doesn't contain
    primitives used by other dependent repositories). Tool repositories
    must be activated on top of other repositories and make not may any 
    assumptions about the state of the repository on which they are activated.
    """
    return wrapped(*args, **kwargs)
