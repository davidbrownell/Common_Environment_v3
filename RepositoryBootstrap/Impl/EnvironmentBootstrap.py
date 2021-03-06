# ----------------------------------------------------------------------
# |
# |  EnvironmentBootstrap.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-03 15:30:58
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-21.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains the EnvironmentBootstrap object."""

import copy
import json
import os
import textwrap

import six

from RepositoryBootstrap import Constants

from RepositoryBootstrap.Impl import CommonEnvironmentImports

from RepositoryBootstrap.SetupAndActivate import Configuration

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironmentImports.CommonEnvironment.ThisFullpath()
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
    @staticmethod
    def GetEnvironmentDir(*prefix_values):
        """Appends a decorated environment name to the given prefix values"""

        path = os.path.join(*prefix_values)

        if not (
            path.endswith(CommonEnvironmentImports.CurrentShell.CategoryName)
            or path.endswith(CommonEnvironmentImports.CurrentShell.Name)
        ):
            path = os.path.join(path, CommonEnvironmentImports.CurrentShell.CategoryName)

        path = os.path.join(path, os.getenv(Constants.DE_ENVIRONMENT_NAME))

        return path

    # ----------------------------------------------------------------------
    @classmethod
    def Load(cls, repo_root):
        # ----------------------------------------------------------------------
        def RestoreRelativePath(value):
            fullpath = os.path.normpath(os.path.join(repo_root, value.replace('/', os.path.sep)))

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
                                                 CommonEnvironmentImports.CurrentShell.CreateScriptName(Constants.SETUP_ENVIRONMENT_NAME),
                                               ))

            return fullpath

        # ----------------------------------------------------------------------

        filename = os.path.join(
            cls.GetEnvironmentDir(
                repo_root,
                Constants.GENERATED_DIRECTORY_NAME,
            ),
            Constants.GENERATED_BOOTSTRAP_JSON_FILENAME,
        )
        if not os.path.isfile(filename):
            raise Exception("'{}' does not exist; please setup this repository".format(filename))

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

            # Get the IgnoreConflictedLibraryNames
            ignore_conflicted_repository_names = config_info.get("IgnoreConflictedRepositoryNames", [])
            ignore_conflicted_library_names = config_info.get("IgnoreConflictedLibraryNames", [])

            # Update the fingerprint
            fingerprint = config_info["Fingerprint"]

            for old_key in list(six.iterkeys(fingerprint)):
                new_key =old_key.replace('/', os.path.sep)

                if new_key not in fingerprint:
                    fingerprint[new_key] = fingerprint[old_key]
                    del fingerprint[old_key]

            # Create the config info
            configurations[config_name] = Configuration.Configuration( config_info["Description"],
                                                                       dependencies,
                                                                       Configuration.VersionSpecs(tools, libraries),
                                                                       ignore_conflicted_repository_names=ignore_conflicted_repository_names or None,
                                                                       ignore_conflicted_library_names=ignore_conflicted_library_names or None,
                                                                     )
            configurations[config_name].Fingerprint = fingerprint

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
    def Save(self, repo_root):
        fundamental_repo = CommonEnvironmentImports.FileSystem.GetRelativePath(repo_root, self.FundamentalRepo).replace(os.path.sep, '/')

        configurations = copy.deepcopy(self.Configurations)

        for config_info in six.itervalues(configurations):
            for dependency in config_info.Dependencies:
                dependency.RepositoryRoot = CommonEnvironmentImports.FileSystem.GetRelativePath(repo_root, dependency.RepositoryRoot).replace(os.path.sep, '/')

            for old_key in  list(six.iterkeys(config_info.Fingerprint)):
                new_key = old_key.replace(os.path.sep, '/')
                if new_key not in config_info.Fingerprint:
                    config_info.Fingerprint[new_key] = config_info.Fingerprint[old_key]
                    del config_info.Fingerprint[old_key]

        # Write the output files
        output_dir = self.GetEnvironmentDir(repo_root, Constants.GENERATED_DIRECTORY_NAME)
        CommonEnvironmentImports.FileSystem.MakeDirs(output_dir, as_user=True)

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

        CommonEnvironmentImports.CurrentShell.UpdateOwnership(output_filename)

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

        CommonEnvironmentImports.CurrentShell.UpdateOwnership(output_filename)

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)
