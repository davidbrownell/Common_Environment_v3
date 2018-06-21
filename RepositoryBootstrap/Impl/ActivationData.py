# ----------------------------------------------------------------------
# |  
# |  ActivationData.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-05 11:27:19
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Repository and ActivationData objects"""

import json
import os
import sys
import textwrap

from collections import OrderedDict

import six

from RepositoryBootstrap import Constants

from RepositoryBootstrap.Impl import CommonEnvironmentImports
from RepositoryBootstrap.Impl.EnvironmentBootstrap import EnvironmentBootstrap
from RepositoryBootstrap.Impl import Utilities

from RepositoryBootstrap.SetupAndActivate import Configuration

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class Repository(object):
    """Information generated dynamically about a repository."""

    # ----------------------------------------------------------------------
    @classmethod
    def Create(cls, repo_root, configuration=None):
        if CommonEnvironmentImports.CurrentShell.IsSymLink(repo_root):
            repo_root = CommonEnvironmentImports.CurrentShell.ResolveSymLink(repo_root)

        repo_name, repo_guid = Utilities.GetRepositoryUniqueId(repo_root)

        return cls( repo_guid,
                    repo_name,
                    repo_root,
                    configuration=configuration,
                  )

    # ----------------------------------------------------------------------
    def __init__( self,
                  id,
                  name,
                  root,
                  configuration=None,
                  is_mixin_repo=False,
                ):
        self.Id                             = id
        self.Name                           = name
        self.Root                           = root
        self.Configuration                  = configuration
        self.IsMixinRepo                    = is_mixin_repo # Overridden during activation

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)

# ----------------------------------------------------------------------
class ActivationData(object):
    """Data generated dynamically during activation"""

    # ----------------------------------------------------------------------
    @classmethod
    def Load( cls,
              repository_root,
              configuration,
              is_fast_environment,
              force=False,
            ):
        if not force and os.getenv(Constants.DE_REPO_ROOT_NAME):
            repository_root = os.getenv(Constants.DE_REPO_ROOT_NAME)
            configuration = os.getenv(Constants.DE_REPO_CONFIGURATION_NAME)

        filename = cls._GetFilename(repository_root, configuration, is_fast_environment)

        if not force and os.path.isfile(filename):
            try:
                # Load the json
                with open(filename, 'r') as f:
                    data = json.load(f)

                # Convert the json structure into concrete types
                tool_version_specs = [ Configuration.VersionInfo( vi_data["Name"],
                                                                  vi_data["Version"],
                                                                )
                                       for vi_data in data["VersionSpecs"]["Tools"]
                                     ]

                library_version_specs = { language : [ Configuration.VersionInfo( vi_data["Name"],
                                                                                  vi_data["Version"],
                                                                                )
                                                       for vi_data in language_version_infos
                                                     ]
                                          for language, language_version_infos in six.iteritems(data["VersionSpecs"]["Libraries"])
                                        }

                return cls( data["Id"],
                            data["Root"],
                            data["IsMixinRepo"],
                            data["Configuration"],
                            [ Repository( repo_data["Id"],
                                          repo_data["Name"],
                                          repo_data["Root"],
                                          repo_data["Configuration"],
                                          repo_data["IsMixinRepo"],
                                        )
                              for repo_data in data["PrioritizedRepositories"]
                            ],
                            Configuration.VersionSpecs( tool_version_specs,
                                                        library_version_specs,
                                                      ),
                          )

            except:
                pass

        # Generate the data
        repository_root = CommonEnvironmentImports.FileSystem.Normalize(repository_root)
        assert os.path.isdir(repository_root), repository_root

        repositories = OrderedDict()

        tool_version_info = []
        library_version_info = {}
        version_info_lookup = {}

        # ----------------------------------------------------------------------
        def Walk( referencing_repo,
                  repo,
                  priority_modifier,
                ):
            if repo.Id not in repositories:
                bootstrap_info = EnvironmentBootstrap.Load(repo.Root)

                bootstrap_info.Repo = repo
                bootstrap_info.ReferencingRepo = referencing_repo
                bootstrap_info.priority_modifier = 0

                repositories[repo.Id] = bootstrap_info

                recurse = True
            else:
                recurse = False

            bootstrap_info = repositories[repo.Id]
            bootstrap_info.priority_modifier += priority_modifier

            # Ensure that the configuration name is valid
            if bootstrap_info.IsConfigurable and not repo.Configuration:
                raise Exception("The repository at '{}' is configurable, but no configuration was provided.".format(repo.Root))

            if not bootstrap_info.IsConfigurable and repo.Configuration:
                raise Exception("The repository at '{}' is not configurable, but a configuration was provided ({}).".format(repo.Root, repo.Configuration))

            if repo.Configuration not in bootstrap_info.Configurations:
                raise Exception(textwrap.dedent(
                    """\
                    The configuration '{config}' is not a valid configuration for the repository at '{root}'.
                    Valid configuration values are:
                    {configs}
                    """).format( config=repo.Configuration,
                                 root=repo.Root,
                                 configs='\n'.join([ "    - {}".format(config or "<None>") for config in six.iterkeys(bootstrap_info.Configurations) ]),
                               ))

            # Check for consistent repo locations
            if repo.Root != bootstrap_info.Repo.Root:
                raise Exception(textwrap.dedent(
                    """\
                    There is a mismatch in repository locations.

                    Repository:                 {name} <{id}>
        
                    New Location:               {new_value}
                    Referenced By:              {new_name} <{new_id}> [{new_root}]
        
                    Original Location:          {original_value}
                    Referenced By:              {original_name} <{original_id}> [{original_root}]
                    """).format( name=repo.Name,
                                 id=repo.Id,
        
                                 new_value=repo.Root,
                                 new_name=referencing_repo.Name,
                                 new_id=referencing_repo.Id,
                                 new_root=referencing_repo.Root,
        
                                 original_value=bootstrap_info.Repo.Root,
                                 original_name=bootstrap_info.Repo.Name,
                                 original_id=bootstrap_info.Repo.Id,
                                 original_root=bootstrap_info.Repo.Root,
                               ))

            # Check for consistent configurations
            if repo.Configuration != bootstrap_info.Repo.Configuration:
                raise Exception(textwrap.dedent(
                    """\
                    There is a mismatch in repository configurations:
        
                    Repository:                 {name} <{id}>
        
                    New Configuration:          {new_value}
                    Referenced By:              {new_name} <{new_id}> [{new_root}]
        
                    Original Configuration:     {original_value}
                    Referenced By:              {original_name} <{original_id}> [{original_root}]
                    """).format( name=repo.Name,
                                 id=repo.Id,
        
                                 new_value=repo.Configuration,
                                 new_name=referencing_repo.Name,
                                 new_id=referencing_repo.Id,
                                 new_root=referencing_repo.Root,
        
                                 original_value=bootstrap_info.Repo.Configuration,
                                 original_name=bootstrap_info.Repo.Name,
                                 original_id=bootstrap_info.Repo.Id,
                                 original_root=bootstrap_info.Repo.Root,
                               ))
        
            # Process the version info

            # ----------------------------------------------------------------------
            def OnVersionMismatch(type_, version_info, existing_version_info):
                original_repo = version_info_lookup[existing_version_info]
        
                raise Exception(textwrap.dedent(
                    """\
                    There was a mismatch in version information.
        
                    Item:                       {name} <{type_}>
        
                    New Version:                {new_value}
                    Specified By:               {new_name} ({new_config}) <{new_id}> [{new_root}]
        
                    Original Version:           {original_value}
                    Specified By:               {original_name} ({original_config}) <{original_id}> [{original_root}]
                    """).format( name=version_info.Name,
                                 type_=type_,
        
                                 new_value=version_info.Version,
                                 new_name=repo.Name,
                                 new_config=repo.Configuration,
                                 new_id=repo.Id,
                                 new_root=repo.Root,
        
                                 original_value=existing_version_info.Version,
                                 original_name=original_repo.Name,
                                 original_config=original_repo.Configuration,
                                 original_id=original_repo.Id,
                                 original_root=original_repo.Root,
                               ))
        
            # ----------------------------------------------------------------------
        
            for version_info in bootstrap_info.Configurations[repo.Configuration].VersionSpecs.Tools:
                existing_version_info = next((tvi for tvi in tool_version_info if tvi.Name == version_info.Name), None)
                
                if existing_version_info is None:
                    tool_version_info.append(version_info)
                    version_info_lookup[version_info] = repo

                elif version_info.Version != existing_version_info.Version:
                    OnVersionMismatch("Tools", version_info, existing_version_info)

            for library_language, version_info_items in six.iteritems(bootstrap_info.Configurations[repo.Configuration].VersionSpecs.Libraries):
                for version_info in version_info_items:
                    existing_version_info = next((lvi for lvi in library_version_info.get(library_language, []) if lvi.Name == version_info.Name), None)

                    if existing_version_info is None:
                        library_version_info.setdefault(library_language, []).append(version_info)
                        version_info_lookup[version_info] = repo

                    elif version_info.Version != existing_version_info.Version:
                        OnVersionMismatch("{} Libraries".format(library_language), version_info, existing_version_info)

            # Process this repository's dependencies
            if recurse:
                for dependency_info in bootstrap_info.Configurations[repo.Configuration].Dependencies:
                    Walk( repo,
                          Repository.Create(dependency_info.RepositoryRoot, dependency_info.Configuration),
                          priority_modifier + 1,
                        )

        # ----------------------------------------------------------------------

        this_repository = Repository.Create(repository_root, configuration)

        Walk(None, this_repository, 1)

        # Order the results from the most- to least-frequently requested
        priority_values = [ (id, info.priority_modifier) for id, info in six.iteritems(repositories) ]
        priority_values.sort(key=lambda x: x[1], reverse=True)

        this_bootstrap_info = repositories[priority_values[-1][0]]
        this_configuration = this_bootstrap_info.Configurations[configuration]

        # Check the fingerprints
        calculated_fingerprint = Utilities.CalculateFingerprint( [ repository_root, ] + [ dependency.RepositoryRoot for dependency in this_configuration.Dependencies ],
                                                                 repository_root,
                                                               )
        if this_configuration.Fingerprint != calculated_fingerprint:
            lines = []

            line_template = "{0:<80}  :  {1}"

            for k, v in six.iteritems(calculated_fingerprint):
                if k not in this_configuration.Fingerprint:
                    lines.append(line_template.format(k, "Added"))
                else:
                    lines.append(line_template.format(k, "Identical" if v == this_configuration.Fingerprint[k] else "Modified"))

            for k in six.iterkeys(this_configuration.Fingerprint):
                if k not in calculated_fingerprint:
                    lines.append(line_template.format(k, "Removed"))

            assert lines
            raise Exception(textwrap.dedent(
                """\
                ********************************************************************************
                ********************************************************************************
                It appears that one or more of the repositories that this repository depends on
                have changed.

                Please run '{setup}' again.
        
                    {status}
        
                ********************************************************************************
                ********************************************************************************
                """).format( setup=CommonEnvironmentImports.CurrentShell.CreateScriptName(Constants.SETUP_ENVIRONMENT_NAME),
                             status=CommonEnvironmentImports.StringHelpers.LeftJustify('\n'.join(lines), 4),
                           ))

        # Create the object
        return cls( this_repository.Id,
                    repository_root,
                    this_bootstrap_info.IsMixinRepo,
                    configuration,
                    is_fast_environment,
                    [ repositories[id].Repo for id, _ in priority_values ],
                    Configuration.VersionSpecs(tool_version_info, library_version_info),
                  )

    # ----------------------------------------------------------------------
    def __init__( self,
                  id,
                  repository_root,
                  is_mixin_repo,
                  configuration,
                  is_fast_environment,
                  prioritized_repositories,
                  version_specs,
                ):
        self.Id                             = id
        self.Root                           = repository_root
        self.IsMixinRepo                    = is_mixin_repo
        self.Configuration                  = configuration
        self.IsFastEnvironment              = is_fast_environment
        self.PrioritizedRepositories        = prioritized_repositories
        self.VersionSpecs                   = version_specs

    # ----------------------------------------------------------------------
    def Save(self):
        with open(self._GetFilename(self.Root, self.Configuration, self.IsFastEnvironment), 'w') as f:
            # ----------------------------------------------------------------------
            class Encoder(json.JSONEncoder):
                def default(self, obj):                 # <An attribute defined in <...> hides this method> pylint: disable = E0202
                    return obj.__dict__

            # ----------------------------------------------------------------------

            json.dump( self,
                       f,
                       cls=Encoder,
                     )

    # ----------------------------------------------------------------------
    def GetActivationDir(self):
        return self._GetActivationDir(self.Root, self.Configuration, self.IsFastEnvironment)

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _GetActivationDir(repository_root, configuration, is_fast_environment):

        result = os.path.join( repository_root,
                               Constants.GENERATED_DIRECTORY_NAME,
                               CommonEnvironmentImports.CurrentShell.CategoryName,
                               configuration or "Default",
                             )
        if is_fast_environment:
            result += ".fast"

        return result

    # ----------------------------------------------------------------------
    @classmethod
    def _GetFilename(cls, repository_root, configuration, is_fast_environment):
        return os.path.join( cls._GetActivationDir( repository_root,
                                                    configuration,
                                                    is_fast_environment,
                                                  ),
                             Constants.GENERATED_ACTIVATION_FILENAME,
                           )
