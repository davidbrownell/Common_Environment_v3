# ----------------------------------------------------------------------
# |  
# |  Configuration.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-02 21:37:56
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Types used to customize repository setup and activation."""

import os

from RepositoryBootstrap.Impl import CommonEnvironmentImports

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironmentImports.CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Too few public methods> pylint: disable = R0903

# ----------------------------------------------------------------------
class VersionInfo(object):
    """Mapping of a specific tool or library and its version."""

    # ----------------------------------------------------------------------
    def __init__(self, name, version):
        self.Name                           = name
        self.Version                        = version

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)

# ----------------------------------------------------------------------
class VersionSpecs(object):
    """\
    Collection of tool and/or library version info.

    Note that library specs are organized by language in an attempt to
    minimize the potential of name collisions.
    """

    # ----------------------------------------------------------------------
    def __init__( self,
                  tools,                    # [ VersionInfo, ... ]
                  libraries,                # { "<language>" : [ VersionInfo, ... ], }
                ):
        self.Tools                          = tools
        self.Libraries                      = libraries

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)

# ----------------------------------------------------------------------
class Dependency(object):
    """
    Information provided when one repository takes a dependency upon another.

    This information will be used to discover the other dependency at setup time.
    """

    # ----------------------------------------------------------------------
    def __init__( self,
                  repository_id,
                  friendly_name,
                  configuration=None,
                  get_clone_uri_func=None,  # def Func(scm_or_none) -> string
                ):
        self.RepositoryId                   = repository_id
        self.FriendlyName                   = friendly_name
        self.Configuration                  = configuration
        self.GetCloneUri                    = get_clone_uri_func or (lambda scm_or_none: None)

        self.RepositoryRoot                 = None      # Populated during setup

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)

# ----------------------------------------------------------------------
class Configuration(object):
    """
    A named configuration specified during activation time.

    A repository can have many configurations, where each configuration
    activates different sets of libraries and dependencies.

    An example of different configurations with a repository could be
    "development" and "production" configurations, where the "development"
    configuration uses libraries and repositories useful while writing
    code in the repository, while "production" only includes those 
    dependencies that are necessary when running the code.
    """

    # ----------------------------------------------------------------------
    def __init__( self,
                  description,
                  dependencies=None,
                  version_specs=None,
                ):
        self.Description                    = description
        self.Dependencies                   = dependencies or []
        self.VersionSpecs                   = version_specs or VersionSpecs([], {})
        self.Fingerprint                    = None      # Populated during setup

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)
