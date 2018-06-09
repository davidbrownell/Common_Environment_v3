# ----------------------------------------------------------------------
# |  
# |  EnvironmentBootstrap.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-03 15:30:58
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the EnvironmentBootstrap object."""

import copy
import json
import os
import sys
import textwrap

import six

from RepositoryBootstrap import Constants

from RepositoryBootstrap.Impl import CommonEnvironmentImports

from RepositoryBootstrap.SetupAndActivate import Configuration

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class EnvironmentBootstrap(object):
    """
    Object that persists environment bootstrap data.

    This data is created during Setup and used as a part of activation.
    """

    NoneJsonKeyReplacementName              = "__None__"

    # ----------------------------------------------------------------------
    @classmethod
    def Load( cls,
              repo_root,
              shell=None,
            ):
        shell = shell or CommonEnvironmentImports.CurrentShell

        # ----------------------------------------------------------------------
        def RestoreRelativePath(value):
            fullpath = os.path.normpath(os.path.join(repo_root, value))

            if not os.path.exists(fullpath):
                raise Exception(textwrap.dedent(
                                    # <Wrong hanging indentation> pylint: disable = C0330
                                    """
                                    '{}' does not exist.

                                    This is usually an indication that something fundamental has changed
                                    or the repository has moved on the file system. To address either issue,
                                    please run this command for the repository:

                                        {}

                                    """).format( fullpath,
                                                 shell.CreateScriptName(Constants.SETUP_ENVIRONMENT_NAME),
                                               ))

            return fullpath

        # ----------------------------------------------------------------------

        filename = os.path.join(repo_root, Constants.GENERATED_DIRECTORY_NAME, shell.CategoryName, Constants.GENERATED_BOOTSTRAP_JSON_FILENAME)
        assert os.path.isfile(filename), filename
        
        with open(filename) as f:
            data = json.load(f)

        fundamental_repo = RestoreRelativePath(data["fundamental_repo"])
        is_mixin_repo = data["is_mixin_repo"]
        is_configurable = data["is_configurable"]

        configurations = {}

        for config_name, config_info in six.iteritems(data["configurations"]):
            # Get the dependencies
            dependencies = []

            for dependency in config_info["Dependencies"]:
                dependencies.append(Configuration.Dependency( dependency["RepositoryId"],
                                                              dependency["FriendlyName"],
                                                              dependency["Configuration"],
                                                            ))
                dependencies[-1].RepositoryRoot = RestoreRelativePath(dependency["RepositoryRoot"])

            # Get the VersionSpecs
            tools = []

            for tool in config_info["VersionSpecs"]["Tools"]:
                tools.append(Configuration.VersionInfo(tool["Name"], tool["Version"]))

            libraries = {}

            for k, version_infos in six.iteritems(config_info["VersionSpecs"]["Libraries"]):
                libraries[k] = [ Configuration.VersionInfo(vi["Name"], vi["Version"]) for vi in version_infos ]

            # Create the config info
            configurations[config_name] = Configuration.Configuration( config_info["Description"],
                                                                       dependencies,
                                                                       Configuration.VersionSpecs(tools, libraries),
                                                                     )
            configurations[config_name].Fingerprint = config_info["Fingerprint"]

        if cls.NoneJsonKeyReplacementName in configurations:
            configurations[None] = configurations[cls.NoneJsonKeyReplacementName]
            del configurations[cls.NoneJsonKeyReplacementName]

        return cls( fundamental_repo,
                    is_mixin_repo,
                    is_configurable,
                    configurations,
                  )
    
    # ----------------------------------------------------------------------
    def __init__( self,
                  fundamental_repo,
                  is_mixin_repo,
                  is_configurable,
                  configurations,
                ):
        assert os.path.isdir(fundamental_repo), fundamental_repo

        self.FundamentalRepo                = fundamental_repo
        self.IsMixinRepo                    = is_mixin_repo
        self.IsConfigurable                 = is_configurable
        self.Configurations                 = configurations

    # ----------------------------------------------------------------------
    def Save( self,
              repo_root,
              shell=None,
            ):
        shell = shell or CommonEnvironmentImports.CurrentShell

        fundamental_repo = CommonEnvironmentImports.FileSystem.GetRelativePath(repo_root, self.FundamentalRepo)
        
        configurations = copy.deepcopy(self.Configurations)
        dependencies_converted = set()

        for config_info in six.itervalues(configurations):
            for dependency in config_info.Dependencies:
                if dependency not in dependencies_converted:
                    dependency.RepositoryRoot = CommonEnvironmentImports.FileSystem.GetRelativePath(repo_root, dependency.RepositoryRoot)
                    dependencies_converted.add(dependency)

        # Write the output files
        output_dir = os.path.join(repo_root, Constants.GENERATED_DIRECTORY_NAME, shell.CategoryName)
        CommonEnvironmentImports.FileSystem.MakeDirs(output_dir)

        # Write the json file
        output_filename = os.path.join(output_dir, Constants.GENERATED_BOOTSTRAP_JSON_FILENAME)

        # JSON can't handle dictionary keys that are None, so change it if necessary
        if None in configurations:
            configurations[self.NoneJsonKeyReplacementName] = configurations[None]
            del configurations[None]

        with open(output_filename, 'w') as f:
            # ----------------------------------------------------------------------
            class Encoder(json.JSONEncoder):
                # <An attribute defined in json.encoder line 158 hides this method> pylint: disable = E0202
                def default(self, obj):
                    return obj.__dict__

            # ----------------------------------------------------------------------

            json.dump( { "fundamental_repo" : fundamental_repo,
                         "is_mixin_repo" : self.IsMixinRepo,
                         "is_configurable" : self.IsConfigurable,
                         "configurations" : configurations,
                       },
                       f,
                       cls=Encoder,
                     )

        # Write the data file
        output_filename = os.path.join(output_dir, Constants.GENERATED_BOOTSTRAP_DATA_FILENAME)

        with open(output_filename, 'w') as f:
            f.write(textwrap.dedent(
                """\
                fundamental_repo={fundamental_repo}
                is_mixin_repo={is_mixin_repo}
                is_configurable={is_configurable}
                """).format( fundamental_repo=fundamental_repo,
                             is_mixin_repo="1" if self.IsMixinRepo else "0",
                             is_configurable="1" if self.IsConfigurable else "0",
                           ))

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjectStrImpl(self)
