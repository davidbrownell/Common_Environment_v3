# ----------------------------------------------------------------------
# |  
# |  Setup.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-06-20 10:54:55
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""One-time environment preparation for a repository."""

import importlib
import json as json_mod
import os
import shutil
import sys
import textwrap

from collections import OrderedDict, namedtuple

import inflect as inflect_mod
import six

import RepositoryBootstrap
from RepositoryBootstrap import Constants

from RepositoryBootstrap.Impl import CommonEnvironmentImports
from RepositoryBootstrap.Impl.EnvironmentBootstrap import EnvironmentBootstrap
from RepositoryBootstrap.Impl import Utilities

from RepositoryBootstrap.SetupAndActivate.Configuration import Configuration

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
# These values influence the behavior of enumeration when searching for repositories.

# The following terms are given higher priority during search, as they contain names
# that are more likely to contain repositories.
CODE_DIRECTORY_NAMES                        = [ "code",
                                                "coding",
                                                "source",
                                                "src",
                                                "development",
                                                "develop",
                                                "dev",
                                              ]

ENUMERATE_EXCLUDE_DIRS                      = [ "generated", 
                                                ".hg",
                                                ".git",
                                              ]

_ScmConstraint                              = CommonEnvironmentImports.CommandLine.EnumTypeInfo([ scm.Name for scm in CommonEnvironmentImports.SourceControlManagement_ALL_TYPES ], arity='?')

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Filename for generated content or standard output if the value is 'stdout'"),
                                                  repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Root of the repository"),
                                                  recurse=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Invoke Setup on this repository and its dependencies"),
                                                  debug=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Write additional debug information to the console"),
                                                  verbose=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Write additional verbose information to the console"),
                                                  configuration=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Configurations to setup; all configurations defined will be setup if explicit values are not provided"),
                                                )
@CommonEnvironmentImports.CommandLine.Constraints( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
                                                   repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                   configuration=CommonEnvironmentImports.CommandLine.StringTypeInfo(arity='*'),
                                                   output_stream=None,
                                                 )
def Setup( output_filename_or_stdout,
           repository_root,
           recurse=False,
           debug=False,
           verbose=False,
           configuration=None,
           use_ascii=False,
           output_stream=sys.stdout,
         ):
    """Perform setup activities for this repository"""

    configurations = configuration or []; del configuration
    
    if debug:
        verbose = True

    output_stream = CommonEnvironmentImports.StreamDecorator(output_stream)

    customization_mod = _GetCustomizationMod(repository_root)

    # ----------------------------------------------------------------------
    def Execute():
        args = [ output_stream,
                 repository_root,
                 customization_mod,
                 debug,
                 verbose,
                 configurations,
               ]

        if recurse:
            # If here, invoke setup on this repo and all of its dependencies
            activities = [ _SetupRecursive,
                         ]

            args.append(use_ascii)
        else:
            # If here, setup this specific repo
            activities = [ _SetupBootstrap,
                           _SetupCustom,
                           _SetupShortcuts,
                           _SetupGeneratedPermissions,
                           _SetupScmHooks,
                         ]

        commands = []

        for func in activities:
            these_commands = func(*args)
            if these_commands:
                commands += these_commands

        return commands

    # ----------------------------------------------------------------------

    result, commands = Utilities.GenerateCommands(Execute, debug)
    
    if output_filename_or_stdout == "stdout":
        output_stream = sys.stdout
        close_stream_func = lambda: None
    else:
        output_stream = open(output_filename_or_stdout, 'w')
        close_stream_func = output_stream.close
    
    with CommonEnvironmentImports.CallOnExit(close_stream_func):
        output_stream.write(CommonEnvironmentImports.CurrentShell.GenerateCommands(commands))
    
    return result

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint( repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Root of the repository"),
                                                  recurse=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Recurse into the dependencies of dependencies"),
                                                  scm=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Specify the Source Control Management system to use when displaying clone uris"),
                                                  configuration=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Specific configurations to list for this repository; configurations not provided with be omitted"),
                                                  max_num_searches=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Limit the number of directories searched when looking for dependencies; this value can be used to reduce the overall time it takes to search for dependencies that ultimately can't be found"),
                                                  required_ancestor_dir=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("When searching for dependencies, limit the search to directories that are descenendants of this ancestor"),
                                                )
@CommonEnvironmentImports.CommandLine.Constraints( repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                   scm=_ScmConstraint,
                                                   configuration=CommonEnvironmentImports.CommandLine.StringTypeInfo(arity='*'),
                                                   max_num_searches=CommonEnvironmentImports.CommandLine.IntTypeInfo(min=1, arity='?'),
                                                   required_ancestor_dir=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(arity='?'),
                                                   output_stream=None,
                                                 )
def List( repository_root,
          recurse=False,
          scm=None,
          configuration=None,
          max_num_searches=None,
          required_ancestor_dir=None,
          use_ascii=False,
          json=False,
          output_stream=sys.stdout,
          verbose=False,
        ):
    """Lists repository information"""
    
    scm = _ScmParameterToScm(scm, repository_root)

    if json:
        repo_map = _CreateRepoMap( repository_root,
                                   configuration,
                                   recurse,
                                   CommonEnvironmentImports.StreamDecorator(None),
                                   verbose,
                                   max_num_searches=max_num_searches,
                                   required_ancestor_dir=required_ancestor_dir,
                                 )
        if isinstance(repo_map, int):
            return repo_map

        output_stream.write(json_mod.dumps([ { "name" : value.Name,
                                               "id" : value.Id,
                                               "root" : value.root,
                                               "clone_uri" : value.get_clone_uri_func(scm) if value.get_clone_uri_func else None,
                                             }
                                             for value in six.itervalues(repo_map)
                                           ]))
        return 0

    # ----------------------------------------------------------------------
    def Callback(output_stream, repo_map):
        for value in six.itervalues(repo_map):
            if value.root is None:
                return -1

        return 0

    # ----------------------------------------------------------------------

    return _SimpleFuncImpl( Callback,
                            repository_root,
                            recurse,
                            _ScmParameterToScm(scm, repository_root),
                            configuration,
                            output_stream,
                            verbose,
                            search_depth=None,
                            max_num_searches=max_num_searches,
                            required_ancestor_dir=required_ancestor_dir,
                            use_ascii=use_ascii,
                          )

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint( repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Root of the repository"),
                                                  repositories_root=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Root of all repositories; repositories not found under this directory will be cloned relative to it"),
                                                  recurse=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Recurse into the dependencies of dependencies"),
                                                  scm=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Specify the Source Control Management system to use when displaying clone uris"),
                                                  uri_dict=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Values used to populate clone uri templates"),
                                                  configuration=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Specific configurations to list for this repository; configurations not provided with be omitted"),
                                                  max_num_searches=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Limit the number of directories searched when looking for dependencies; this value can be used to reduce the overall time it takes to search for dependencies that ultimately can't be found"),
                                                )
@CommonEnvironmentImports.CommandLine.Constraints( repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                   repositories_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                   scm=_ScmConstraint,
                                                   uri_dict=CommonEnvironmentImports.CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                                                   configuration=CommonEnvironmentImports.CommandLine.StringTypeInfo(arity='*'),
                                                   max_num_searches=CommonEnvironmentImports.CommandLine.IntTypeInfo(min=1, arity='?'),
                                                   output_stream=None,
                                                 )
def Enlist( repository_root,
            repositories_root,
            recurse=False,
            scm=None,
            uri_dict=None,
            configuration=None,
            max_num_searches=None,
            use_ascii=False,
            output_stream=sys.stdout,
            verbose=False,
          ):
    """Enlists in provided repositories"""

    if not repository_root.startswith(repositories_root):
        output_stream.write("ERROR: The repository root '{}' does not begin with the repositories root '{}'.\n".format( repository_root,
                                                                                                                        repositories_root,
                                                                                                                      ))
        return -1

    scm = _ScmParameterToScm(scm, repository_root)

    nonlocals = CommonEnvironmentImports.CommonEnvironment.Nonlocals( should_continue=None,
                                                                    )

    # ----------------------------------------------------------------------
    def Callback(output_stream, repo_map):
        to_clone = []
        missing = []

        for value in six.itervalues(repo_map):
            if value.root is None:
                if value.get_clone_uri_func is not None:
                    clone_uri = value.get_clone_uri_func(scm)
                    if clone_uri is not None:
                        try:
                            clone_uri = clone_uri.format(**uri_dict)
                        except KeyError as ex:
                            output_stream.write("\nERROR: The key {} is used in the clone uri '{}' (defined in '{}') and must be provided on the command line using the 'uri_dict' argument.\n".format( str(ex), 
                                                                                                                                                                                                        clone_uri,
                                                                                                                                                                                                        value.root,
                                                                                                                                                                                                      ))
                            return -1

                        to_clone.append(( value, clone_uri ))
                        continue

                missing.append(value)

        if not to_clone:
            if missing:
                output_stream.write(textwrap.dedent(
                    """\
                    WARNING: Unable to clone these repositories:
                    {}
                    """).format('\n'.join([ "    - {} ({})".format(value.Name, value.Id) for value in missing ])))
                
                return 1

            output_stream.write("All repositories were found.\n")
            return 0

        output_stream.write("\n\nCloning {}...".format(inflect.no("repository", len(to_clone))))
        with output_stream.DoneManager() as dm:
            for index, (value, clone_uri) in enumerate(to_clone):
                dm.stream.write("Processing '{}' ({} of {})...".format( value.Name,
                                                                        index + 1,
                                                                        len(to_clone),
                                                                      ))
                with dm.stream.DoneManager() as clone_dm:
                    dest_dir = os.path.join(repositories_root, value.Name.replace('_', os.path.sep))
                    if os.path.isdir(dest_dir):
                        clone_dm.stream.write("WARNING: The output dir '{}' already exists and will not be replaced by the repo '{}'.\n".format(dest_dir, value.Name))
                        clone_dm.result = 1

                        continue

                    clone_dm.result, output = scm.Clone(clone_uri, dest_dir)
                    clone_dm.stream.write(output)
            
        nonlocals.should_continue = (dm.result == 0)
        return dm.result

    # ----------------------------------------------------------------------

    while True:
        nonlocals.should_continue = False

        result = _SimpleFuncImpl( Callback,
                                  repository_root,
                                  recurse,
                                  scm,
                                  configuration,
                                  output_stream,
                                  verbose,
                                  max_num_searches=max_num_searches,
                                  required_ancestor_dir=repositories_root,
                                  use_ascii=use_ascii,
                                )
        
        if result != 0 or not nonlocals.should_continue:
            break

    return result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _SetupRecursive( output_stream,
                     repository_root,
                     customization_mod,
                     debug,
                     verbose,
                     explicit_configurations,
                     use_ascii,
                   ):
    # ----------------------------------------------------------------------
    def Callback(output_stream, repo_map):
        Commands = CommonEnvironmentImports.CurrentShell.Commands

        with output_stream.DoneManager( display=False,
                                      ) as dm:
            dm.stream.write("\n\n")

            command_line_template = "{cmd}{debug}{verbose} {{}}".format( cmd=CommonEnvironmentImports.CurrentShell.CreateScriptName(Constants.SETUP_ENVIRONMENT_NAME),
                                                                         debug='' if not debug else " /debug",
                                                                         verbose='' if not verbose else " /verbose",
                                                                       )

            setup_error_variable_name = "_setup_error"

            values = list(six.itervalues(repo_map))

            for index, value in enumerate(values):
                dm.stream.write("Setting up '{} ({})' ({} of {})...".format( value.Name,
                                                                             value.Id,
                                                                             index + 1, 
                                                                             len(values),
                                                                           ))
                with dm.stream.DoneManager( suffix='\n',
                                          ) as this_dm:
                    if value.root is None:
                        this_dm.stream.write("This repository does not exist in the current filesystem.\n")
                        this_dm.result = 1

                        continue

                    commands = [ Commands.EchoOff(),
                                 Commands.PushDirectory(value.root),
                                 Commands.Call(command_line_template.format(' '.join([ "/configuration_EQ_{}".format(configuration) for configuration in six.iterkeys(value.dependents) if configuration is not None ]))),
                                 Commands.PersistError(setup_error_variable_name),
                                 Commands.PopDirectory(),
                                 Commands.ExitOnError(variable_name=setup_error_variable_name),
                               ]

                    this_dm.result = CommonEnvironmentImports.CurrentShell.ExecuteCommands( commands,
                                                                                            this_dm.stream,
                                                                                          )

            return dm.result

    # ----------------------------------------------------------------------

    _SimpleFuncImpl( Callback,
                     repository_root,
                     True, # recursive
                     _ScmParameterToScm(None, repository_root),
                     explicit_configurations=explicit_configurations,
                     output_stream=output_stream,
                     verbose=verbose,
                     use_ascii=use_ascii,
                   )

# ----------------------------------------------------------------------
def _SetupBootstrap( output_stream,
                     repository_root,
                     customization_mod,
                     debug,
                     verbose,
                     explicit_configurations,
                   ):
    repo_data = _RepoData.Create( customization_mod,
                                  supported_configurations=explicit_configurations,
                                )

    # A mixin repository cannot have configurations, dependencies or version specs
    if ( repo_data.IsMixinRepository and
         ( repo_data.HasConfigurations or
           next(six.itervalues(repo_data.Configurations)).Dependencies or 
           next(six.itervalues(repo_data.Configurations)).VersionSpecs.Tools or
           next(six.itervalues(repo_data.Configurations)).VersionSpecs.Libraries
         )
       ):
        raise Exception("A mixin repository cannot have configurations, dependencies, or version specs.")

    display_cols = [ 54, 32, 100, ]
    display_template = "{{0:<{0}}}  {{1:<{1}}}  {{2:<{2}}}".format(*display_cols)

    # ----------------------------------------------------------------------
    def InitialDisplay(repo_map):
        max_config_name_length = int(display_cols[0] * 0.75)
        config_display_info = []

        for config_name, config_info in six.iteritems(repo_data.Configurations):
            if config_name is None:
                continue

            max_config_name_length = max(max_config_name_length, len(config_name))
            config_display_info.append(( config_name, config_info.Description ))

        # ----------------------------------------------------------------------
        def GetUniqueConfigurations(map_value):
            configurations = set()

            for v in six.itervalues(map_value.dependents):
                for id, config_name in v:
                    if config_name is not None:
                        configurations.add(config_name)

            configurations = sorted(list(configurations), key=str.lower)
            return configurations

        # ----------------------------------------------------------------------

        if repo_data.HasConfigurations:
            configuration_info = textwrap.dedent(
                                    """\
                                    Based on these configurations:

                                        {}
                                    {}
                                    """).format( CommonEnvironmentImports.StringHelpers.LeftJustify( '\n'.join([ "- {0:<{1}}{2}".format( config_name,
                                                                                                                                         max_config_name_length,
                                                                                                                                         " : {}".format(description),
                                                                                                                                       )
                                                                                                                 for config_name, description in config_display_info
                                                                                                               ]),
                                                                                                     4,
                                                                                                   ),
                                                 '' if repo_data.AreConfigurationsFiltered else textwrap.dedent(
                                                                                                    """\

                                                                                                    To operate on specific configurations, specify this argument one or more times on the command line:
                                                                                                                                            
                                                                                                        /configuration=<configuration name>
                                                                                                    """).rstrip(),
                                               )
        else:
            configuration_info = ''

        output_stream.write(textwrap.dedent(
            """\

            Your system will be scanned for these repositories:

                {header}
                {sep}
                {values}

                {configurations}

            """).format( header=display_template.format("Repository Name", "Id", "Dependent Configurations"),
                         sep=display_template.format(*[ '-' * col_size for col_size in display_cols ]),
                         values='\n    '.join([ display_template.format(v.Name, k, ', '.join(GetUniqueConfigurations(v)))
                                                for k, v in six.iteritems(repo_map)
                                              ]),
                         configurations=CommonEnvironmentImports.StringHelpers.LeftJustify(configuration_info, 4),
                       ))
        
        return True

    # ----------------------------------------------------------------------

    repo_map = _RepositoriesMap.Create( repository_root,
                                        repo_data,
                                        recurse=False,
                                        output_stream=output_stream,
                                        verbose=verbose,
                                        on_search_begin_func=InitialDisplay,
                                      )

    remaining_repos = [ value for value in six.itervalues(repo_map) if value.root is None ]
    if remaining_repos:
        raise Exception(textwrap.dedent(
            """\
            Unable to find {repository}
            {repos}
            """).format( repository=inflect.no("repository", len(remaining_repos)),
                         repos='\n'.join([ "    - {} ({})".format(ri.Name, ri.Id) for ri in remaining_repos ]),
                       ))

    output_stream.write(textwrap.dedent(
        """\
        {repository} {was} found at {this} {location}

            {header}
            {sep}
            {values}


        """).format( repository=inflect.no("repository", len(repo_map)),
                     was=inflect.plural("was", len(repo_map)),
                     this=inflect.plural("this", len(repo_map)),
                     location=inflect.plural("location", len(repo_map)),
                     header=display_template.format("Repository Name", "Id", "Location"),
                     sep=display_template.format(*[ '-' * col_size for col_size in display_cols ]),
                     values=CommonEnvironmentImports.StringHelpers.LeftJustify( '\n'.join([ display_template.format( value.Name,
                                                                                                                     value.Id,
                                                                                                                     value.root,
                                                                                                                   )
                                                                                            for value in six.itervalues(repo_map)
                                                                                          ]),
                                                                                4,
                                                                              ),
                   ))

    # Populate the configurations and calculate the fingerprints
    for config_name, config_info in six.iteritems(repo_data.Configurations):
        repository_roots = []

        for dependency in config_info.Dependencies:
            assert dependency.RepositoryRoot is None, dependency.RepositoryRoot
            assert dependency.RepositoryId in repo_map, dependency.RepositoryId

            dependency.RepositoryRoot = repo_map[dependency.RepositoryId].root

            repository_roots.append(dependency.RepositoryRoot)

        config_info.Fingerprint = Utilities.CalculateFingerprint( [ repository_root, ] + repository_roots, 
                                                                  repository_root,
                                                                )

    return EnvironmentBootstrap( RepositoryBootstrap.GetFundamentalRepository(),
                                 repo_data.IsMixinRepository,
                                 repo_data.HasConfigurations,
                                 repo_data.Configurations,
                               ).Save(repository_root)

# ----------------------------------------------------------------------
# <Unused argument> pylint: disable = W0613
def _SetupCustom( output_stream,
                  repository_root,
                  customization_mod,
                  debug,
                  verbose,
                  explicit_configurations,
                ):
    if customization_mod is None or not hasattr(customization_mod, Constants.SETUP_ENVIRONMENT_ACTIONS_METHOD_NAME):
        return None

    func = CommonEnvironmentImports.Interface.CreateCulledCallable(getattr(customization_mod, Constants.SETUP_ENVIRONMENT_ACTIONS_METHOD_NAME))

    return func({ "debug" : debug,
                  "verbose" : verbose,
                  "explicit_configurations" : explicit_configurations,
                })

# ----------------------------------------------------------------------
# <Unused argument> pylint: disable = W0613
def _SetupShortcuts( output_stream,
                     repository_root,
                     customization_mod,
                     debug,
                     verbose,
                     explicit_configurations,
                   ):
    activate_script = CommonEnvironmentImports.CurrentShell.CreateScriptName(Constants.ACTIVATE_ENVIRONMENT_NAME)

    shortcut_target = os.path.join(_script_dir, activate_script)
    assert os.path.isfile(shortcut_target), shortcut_target

    return [ CommonEnvironmentImports.CurrentShell.Commands.SymbolicLink( os.path.join(repository_root, activate_script),
                                                                          shortcut_target,
                                                                        ),
           ]

# ----------------------------------------------------------------------
# <Unused argument> pylint: disable = W0613
def _SetupGeneratedPermissions( output_stream,
                                repository_root,
                                customization_mod,
                                debug,
                                verbose,
                                explicit_configurations,
                              ):
    generated_dir = os.path.join(repository_root, Constants.GENERATED_DIRECTORY_NAME, CommonEnvironmentImports.CurrentShell.CategoryName)
    assert os.path.isdir(generated_dir), generated_dir

    os.chmod(generated_dir, 0x777)

# ----------------------------------------------------------------------
# <Unused argument> pylint: disable = W0613
def _SetupScmHooks( output_stream,
                    repository_root,
                    customization_mod,
                    debug,
                    verbose,
                    explicit_configurations,
                  ):
    # ----------------------------------------------------------------------
    def Mercurial():
        hooks_filename = os.path.normpath(os.path.join(_script_dir, "Hooks", "Mercurial.py"))
        assert os.path.isfile(hooks_filename), hooks_filename

        import configparser

        config = configparser.ConfigParser( allow_no_value=True,
                                          )

        potential_hg_filename = os.path.join(repository_root, ".hg", "hgrc")
        if os.path.isfile(potential_hg_filename):
            with open(potential_hg_filename) as f:
                config.read_file(f)

        if not config.has_section("hooks"):
            config.add_section("hooks")

        relative_hooks_filename = CommonEnvironmentImports.FileSystem.GetRelativePath(repository_root, hooks_filename)

        config.set("hooks", "pretxncommit.CommonEnvironment", "python:{}:PreTxnCommit".format(relative_hooks_filename))
        config.set("hooks", "preoutgoing.CommonEnvironment", "python:{}:PreOutgoing".format(relative_hooks_filename))
        config.set("hooks", "pretxnchangegroup.CommonEnvironment", "python:{}:PreTxnChangeGroup".format(relative_hooks_filename))

        backup_hg_filename = "{}.bak".format(potential_hg_filename)
        if os.path.isfile(potential_hg_filename) and not os.path.isfile(backup_hg_filename):
            shutil.copyfile(potential_hg_filename, backup_hg_filename)

        with open(potential_hg_filename, 'w') as f:
            config.write(f)

    # ----------------------------------------------------------------------
    def Git():
        hooks_dir = os.path.join(repository_root, ".git", "hooks")
        CommonEnvironmentImports.FileSystem.MakeDirs(hooks_dir)

        hooks_impl_filename = os.path.normpath(os.path.join(_script_dir, "Hooks", "Git.py"))
        assert os.path.isfile(hooks_impl_filename), hooks_impl_filename
        
        relative_hooks_impl_filename = CommonEnvironmentImports.FileSystem.GetRelativePath(repository_root, hooks_impl_filename).replace(os.path.sep, '/')
        
        import io

        for name in [ "commit-msg",
                      "pre-push",
                      "pre-receive",
                    ]:
            with io.open( os.path.join(hooks_dir, name),
                          'w',
                          newline='\n',
                        ) as f:
                if name == "pre-receive":
                    # This hook is run from the .git dir on the server. The relative path is
                    # based on the root dir, so we need to move up an additional level to compensate
                    # for the .git dir.
                    this_relative_hooks_impl_filename = "../{}".format(relative_hooks_impl_filename)
                else:
                    this_relative_hooks_impl_filename = relative_hooks_impl_filename

                f.write(textwrap.dedent(
                    """\
                    #!/bin/sh
                    python {} {} "$*"
                    exit $?
                    """).format( this_relative_hooks_impl_filename, 
                                 name.replace('-', '_'),
                               ))

    # ----------------------------------------------------------------------

    if os.path.isdir(os.path.join(repository_root, ".hg")):
        return Mercurial()
    if os.path.isdir(os.path.join(repository_root, ".git")):
        return Git()

    return None

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class _RepoData(object):

    # ----------------------------------------------------------------------
    @classmethod
    def Create( cls,
                customization_mod,
                supported_configurations=None,
              ):
        if customization_mod:
            # Get the dependency info
            dependencies_func = getattr(customization_mod, Constants.SETUP_ENVIRONMENT_DEPENDENCIES_METHOD_NAME, None)
            if dependencies_func:
                configurations = dependencies_func()

                if configurations and not isinstance(configurations, dict):
                    configurations = { None : configurations, }

                # Mixin repos are specified via the MixinRepository decorator
                is_mixin_repository = ( hasattr(dependencies_func, "_self_wrapper") and 
                                        dependencies_func._self_wrapper.__name__ == "MixinRepository"
                                      )

                if supported_configurations:
                    for config_name in list(six.iterkeys(configurations)):
                        if config_name not in supported_configurations:
                            del configurations[config_name]

                return cls( configurations,
                            bool(supported_configurations),
                            is_mixin_repository,
                          )

        # Create a default configuration
        return cls( { None : Configuration("Default Configuration"), },
                    are_configurations_filtered=False,
                    is_mixin_repository=False,
                  )

    # ----------------------------------------------------------------------
    def __init__( self,
                  configurations,
                  are_configurations_filtered,
                  is_mixin_repository,
                ):
        self.Configurations                 = configurations
        self.AreConfigurationsFiltered      = are_configurations_filtered
        self.IsMixinRepository              = is_mixin_repository

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    @property
    def HasConfigurations(self):
        return len(self.Configurations) > 1 or next(six.iterkeys(self.Configurations)) is not None

# ----------------------------------------------------------------------
class _RepositoriesMap(OrderedDict):

    # ----------------------------------------------------------------------
    # |  Public Types
    class Value(object):
        # ----------------------------------------------------------------------
        def __init__(self, name, id, source):
            self.Name                       = name
            self.Id                         = id
            self.Source                     = source

            # Calculated values
            self.root                       = None
            self.get_clone_uri_func         = None

            self.dependents                 = OrderedDict()                 # { <config_name> : [ ( <dependent_repo_guid>, <dependent_config_name> ), ... ], ... }
            self.dependencies               = OrderedDict()                 # { <config_name> : [ ( <dependency_repo_guid>, <dependency_config_name> ), ... ], ... }

        # ----------------------------------------------------------------------
        def __repr__(self):
            return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    # |  Public Methods

    @classmethod
    def Create( cls,
                repository_root,
                repo_data,
                recurse,
                output_stream,
                verbose,
                search_depth=None,
                max_num_searches=None,
                required_ancestor_dir=None,
                on_search_begin_func=None,              # def Func(self) -> Bool
              ):
        self = cls()
        repo_cache = {}

        nonlocals = CommonEnvironmentImports.CommonEnvironment.Nonlocals( remaining_repos=0,
                                                                        )

        # ----------------------------------------------------------------------
        def AddRepo( name,
                     guid,
                     directory,
                     configurations=None,
                   ):
            customization_mod = _GetCustomizationMod(directory)
            if customization_mod is None:
                return

            if guid not in self:
                value = cls.Value(name, guid, directory)
                value.root = directory

                self[guid] = value

            value = self[guid]

            if configurations is None:
                configurations = _RepoData.Create(customization_mod).Configurations
                if not configurations:
                    return

            for config_name, config_info in six.iteritems(configurations):
                these_dependencies = []

                for dependency_info in config_info.Dependencies:
                    these_dependencies.append(( dependency_info.RepositoryId, dependency_info.Configuration ))

                    if dependency_info.RepositoryId not in self:
                        if dependency_info.RepositoryId in repo_cache:
                            enum_result = repo_cache[dependency_info.RepositoryId]
                            del repo_cache[dependency_info.RepositoryId]

                            AddRepo( enum_result.Name,
                                     enum_result.Id,
                                     enum_result.Root,
                                   )
                        else:
                            self[dependency_info.RepositoryId] = cls.Value( dependency_info.FriendlyName,
                                                                            dependency_info.RepositoryId,
                                                                            directory,
                                                                          )
                            nonlocals.remaining_repos += 1

                    that_value = self[dependency_info.RepositoryId]

                    that_value.dependents.setdefault(dependency_info.Configuration, []).append(( guid, config_name ))

                    if that_value.get_clone_uri_func is None:
                        that_value.get_clone_uri_func = dependency_info.GetCloneUri

                value.dependencies[config_name] = these_dependencies

        # ----------------------------------------------------------------------

        root_repo_name, root_repo_id = Utilities.GetRepositoryUniqueId(repository_root)

        AddRepo( root_repo_name,
                 root_repo_id,
                 repository_root,
                 configurations=repo_data.Configurations,
               )

        if on_search_begin_func and not on_search_begin_func(self):
            return None

        if nonlocals.remaining_repos:
            output_stream.write("\nSearching for repositories...")
            output_stream.flush()

            warnings = []
                
            with output_stream.DoneManager( suffix='\n\n',
                                          ) as dm:
                for enum_result in cls._Enumerate( repository_root,
                                                   CommonEnvironmentImports.StreamDecorator(dm.stream if verbose else None),
                                                   search_depth=search_depth,
                                                   max_num_searches=max_num_searches,
                                                   required_ancestor_dir=required_ancestor_dir,
                                                 ):
                    if enum_result.Id not in self:
                        if enum_result.Id not in repo_cache:
                            repo_cache[enum_result.Id] = enum_result
                
                        continue
                
                    value = self[enum_result.Id]
                
                    # Note that we may already have a root associated with this repo.
                    # This can happen when the repo has already been found in a location
                    # nearer to the repository_root and the search has continued to find
                    # other repositories.
                    if value.root is not None:
                        continue
                
                    if value.Name != enum_result.Name:
                        warnings.append(( enum_result.Name, value.Name, value.Source ))
                        
                    value.Name = enum_result.Name
                    value.root = enum_result.Root
                    
                    if recurse:
                        AddRepo( enum_result.Name,
                                 enum_result.Id,
                                 enum_result.Root,
                               )
                
                    assert nonlocals.remaining_repos
                    nonlocals.remaining_repos -= 1
                
                    if nonlocals.remaining_repos == 0:
                        break

            if warnings:
                output_stream.write(textwrap.dedent(
                    """\
                    WARNING: The following dependency names didn't match the actual name used within the repository.

                        {}

                    """).format(CommonEnvironmentImports.StringHelpers.LeftJustify( '\n'.join([ textwrap.dedent(
                                                                                                    """\
                                                                                                    Actual Name:        {}
                                                                                                    Dependency Name:    {}
                                                                                                    Dependency Source:  {}
                                                                                                    """).format( actual_name,
                                                                                                                 dependency_name,
                                                                                                                 dependency_source,
                                                                                                               )
                                                                                                for actual_name, dependency_name, dependency_source in warnings
                                                                                              ]),
                                                                                    4,
                                                                                  )))

        return self

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    _EnumerateResult                        = namedtuple( "_EnumerateResult",
                                                          [ "Name",
                                                            "Id",
                                                            "Root",
                                                          ],
                                                        )

    # ----------------------------------------------------------------------
    @classmethod
    def _Enumerate( cls,
                    repository_root,
                    verbose_stream,
                    search_depth=None,
                    max_num_searches=None,
                    required_ancestor_dir=None,
                  ):
        search_depth = search_depth or 5
        assert required_ancestor_dir is None or repository_root.startswith(required_ancestor_dir), (required_ancestor_dir, repository_root)
    
        # Augment the search depth to account for the provided root
        search_depth += repository_root.count(os.path.sep)
        if CommonEnvironmentImports.CurrentShell.CategoryName == "Windows":
            # Don't count the slash associated with the drive name
            assert search_depth
            search_depth -= 1
    
            # ----------------------------------------------------------------------
            def ItemPreprocessor(item):
                drive, suffix = os.path.splitdrive(item)
                if drive[-1] == ':':
                    drive = drive[:-1]
            
                return "{}:{}".format(drive.upper(), suffix)
            
            # ----------------------------------------------------------------------
            
        else:
            # ----------------------------------------------------------------------
            def ItemPreprocessor(item):
                return item
    
            # ----------------------------------------------------------------------
                
        if required_ancestor_dir:
            required_ancestor_dir = ItemPreprocessor(CommonEnvironmentImports.FileSystem.RemoveTrailingSep(required_ancestor_dir))
    
            # ----------------------------------------------------------------------
            def IsValidAncestor(fullpath):
                return fullpath.startswith(required_ancestor_dir)
    
            # ----------------------------------------------------------------------
        else:
            # ----------------------------------------------------------------------
            def IsValidAncestor(fullpath):
                return True
    
            # ----------------------------------------------------------------------
    
        # ----------------------------------------------------------------------
        def Enumerate():
            repository_root_dirname = os.path.dirname(repository_root)
            len_repository_root_dirname = len(repository_root_dirname)
    
            search_items = []
            searched_items = set()
    
            # ----------------------------------------------------------------------
            def FirstNonmatchingChar(s):
                for index, c in enumerate(s):
                    if ( index == len_repository_root_dirname or
                         c != repository_root_dirname[index]
                       ):
                        break
    
                return index
    
            # ----------------------------------------------------------------------
            def PushSearchItem(fullpath):
                fullpath = os.path.realpath(os.path.normpath(fullpath))
    
                parts = fullpath.split(os.path.sep)
                if len(parts) > search_depth:
                    return
    
                parts_lower = set([ part.lower() for part in parts ])
    
                priority = 1
                for bump_name in CODE_DIRECTORY_NAMES:
                    if bump_name in parts_lower:
                        priority = 0
                        break
    
                # Every item except the last is used for sorting
                search_items.append(( -FirstNonmatchingChar(fullpath),          # Favor ancestors over other locations
                                      priority,                                 # Favor names that look like source locations
                                      len(parts),                               # Favor locations near the root
                                      fullpath.lower(),                         # Case insensitive sort
                                      fullpath,
                                    ))
                search_items.sort()
    
            # ----------------------------------------------------------------------
            def PopSearchItem():
                return search_items.pop(0)[-1]
    
            # ----------------------------------------------------------------------
            def Impl(skip_root):
                ctr = 0
    
                while search_items:
                    search_item = PopSearchItem()
    
                    # Don't process the dir if it has already been procssed
                    if search_item in searched_items:
                        continue
    
                    searched_items.add(search_item)
    
                    # Don't process if the dir doesn't exist anymore (these searches 
                    # can take a while and dirs come and go)
                    if not os.path.isdir(search_item):
                        continue
    
                    # Don't process if the dir has been explicitly ignored
                    if os.path.exists(os.path.join(search_item, Constants.IGNORE_DIRECTORY_AS_BOOTSTRAP_DEPENDENCY_SENTINEL_FILENAME)):
                        continue
    
                    yield search_item
    
                    ctr += 1
                    if max_num_searches and ctr == max_num_searches:
                        break
    
                    # Add the parent to the queue
                    try:
                        potential_parent = os.path.dirname(search_item)
                        if potential_parent != search_item:
                            if ( IsValidAncestor(potential_parent) and 
                                 ( not skip_root or os.path.dirname(potential_parent) != potential_parent )
                               ):
                                PushSearchItem(ItemPreprocessor(potential_parent))
                    
                    except (PermissionError, FileNotFoundError):
                        pass
    
                    # Add the children to the queue
                    try:
                        for item in os.listdir(search_item):
                            fullpath = os.path.join(search_item, item)
                            if not os.path.isdir(fullpath):
                                continue
    
                            if item.lower() in ENUMERATE_EXCLUDE_DIRS:
                                continue
    
                            PushSearchItem(ItemPreprocessor(fullpath))
                    
                    except (PermissionError, FileNotFoundError):
                        pass
    
            # ----------------------------------------------------------------------
    
            PushSearchItem(ItemPreprocessor(repository_root))
    
            if CommonEnvironmentImports.CurrentShell.CategoryName == "Windows":
                for result in Impl(True):
                    yield result
            
                # If here, look at other drive locations
                import win32api
                import win32file
            
                # <Module 'win32api' has not 'GetLogicalDriveStrings' member, but source is unavailable. Consider adding this module to extension-pkg-whitelist if you want to perform analysis based on run-time introspection of living objects.> pylint: disable = I1101
            
                for drive in [ drive for drive in win32api.GetLogicalDriveStrings().split('\000') if drive and win32file.GetDriveType(drive) == win32file.DRIVE_FIXED ]:
                    PushSearchItem(drive)
            
                for result in Impl(False):
                    yield result
            
            else:
                for result in Impl(False):
                    yield result
    
        # ----------------------------------------------------------------------
    
        for directory in Enumerate():
            verbose_stream.write("Searching in '{}'\n".format(directory))
    
            result = Utilities.GetRepositoryUniqueId(directory, raise_on_error=False)
            if result is None:
                continue
    
            yield cls._EnumerateResult( result[0],
                                        result[1],
                                        directory,
                                      )
    
        verbose_stream.write("\n")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GetCustomizationMod(repository_root):
    potential_customization_filename = os.path.join(repository_root, Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME)
    if os.path.isfile(potential_customization_filename):
        sys.path.insert(0, repository_root)
        with CommonEnvironmentImports.CallOnExit(lambda: sys.path.pop(0)):
            module_name = os.path.splitext(Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME)[0]

            module = importlib.import_module(module_name)
            del sys.modules[module_name]

            return module

    return None

# ----------------------------------------------------------------------
def _CreateRepoMap( repository_root,
                    supported_configurations,
                    recurse,
                    output_stream,
                    verbose,
                    max_num_searches=None,
                    required_ancestor_dir=None,
                  ):
    customization_mod = _GetCustomizationMod(repository_root)
    if customization_mod is None:
        output_stream.write("ERROR: '{}' is not a valid repository root.\n".format(repository_root))
        return -1

    return _RepositoriesMap.Create( repository_root,
                                    _RepoData.Create( customization_mod,
                                                      supported_configurations=supported_configurations,
                                                    ),
                                    recurse,
                                    output_stream,
                                    verbose,
                                    search_depth=None,
                                    max_num_searches=max_num_searches,
                                    required_ancestor_dir=required_ancestor_dir,
                                  )
                                                      
# ----------------------------------------------------------------------
def _SimpleFuncImpl( callback,              # def Func(output_stream, repo_map) -> result code
                     repository_root,
                     recurse,
                     scm,
                     explicit_configurations,
                     output_stream,
                     verbose,
                     search_depth=None,
                     max_num_searches=None,
                     required_ancestor_dir=None,
                     use_ascii=False,
                   ):
    with CommonEnvironmentImports.StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                                              prefix="\nResults: ",
                                                                              suffix='\n',
                                                                            ) as dm:
        repo_map = _CreateRepoMap( repository_root,
                                   explicit_configurations,
                                   recurse,
                                   dm.stream,
                                   verbose,
                                   max_num_searches=max_num_searches,
                                   required_ancestor_dir=required_ancestor_dir,
                                 )
        if isinstance(repo_map, int):
            return repo_map

        # ----------------------------------------------------------------------
        nonlocals = CommonEnvironmentImports.CommonEnvironment.Nonlocals( display_template=None,
                                                                          display_cols=None,
                                                                        )

        # ----------------------------------------------------------------------
        DisplayInfo                         = namedtuple( "DisplayInfo",
                                                          [ "Id",
                                                            "Configuration",
                                                            "Root",
                                                            "GetCloneUri",
                                                          ],
                                                        )

        # ----------------------------------------------------------------------
        def Traverse(value, configuration):
            result_tree = OrderedDict()
            result_display_infos = []

            display_infos.append(DisplayInfo( value.Id,
                                              configuration,
                                              value.root,
                                              value.get_clone_uri_func,
                                            ))

            if configuration in value.dependencies:
                for child_guid, child_configuration in value.dependencies[configuration]:
                    assert child_guid in repo_map, child_guid
                    child_value = repo_map[child_guid]

                    child_tree, child_display_infos = Traverse(child_value, child_configuration)

                    result_tree[child_value.Name] = child_tree
                    result_display_infos += child_display_infos

            return result_tree, result_display_infos

        # ----------------------------------------------------------------------
        def Display(tree, display_infos):
            if not tree:
                return

            # asciitree requires a single element at the root
            if len(tree) > 1:
                added_line = True
                tree = OrderedDict([ ( "", tree ), ])
            else:
                added_line = False

            from asciitree import LeftAligned
            from asciitree.drawing import BoxStyle, BOX_LIGHT, BOX_ASCII

            create_tree_func = LeftAligned(draw=BoxStyle(gfx=(BOX_ASCII if use_ascii else BOX_LIGHT), horiz_len=1))

            lines = create_tree_func(tree).split('\n')

            if added_line:
                lines = lines[1:]

            if nonlocals.display_template is None:
                max_length = len(max(lines, key=len))

                nonlocals.display_cols = [ max_length, 20, 32, 50, 45, ]
                nonlocals.display_template = "{{0:<{0}}}  {{1:<{1}}}  {{2:<{2}}}  {{3:<{3}}}  {{4:<{4}}}".format(*nonlocals.display_cols)

            dm.stream.write(textwrap.dedent(
                """\
                {}
                {}
                {}
                """).format( nonlocals.display_template.format("Repository", "Configuration", "Id", "Location", "Clone Uri"),
                             nonlocals.display_template.format(*[ '-' * col_size for col_size in nonlocals.display_cols ]),
                             '\n'.join([ nonlocals.display_template.format( line,
                                                                            display_infos[index].Configuration or "<default>",
                                                                            display_infos[index].Id,
                                                                            display_infos[index].Root or "N/A",
                                                                            (display_infos[index].GetCloneUri(scm) if display_infos[index].GetCloneUri else None) or "N/A",
                                                                          )
                                         for index, line in enumerate(lines)
                                       ]),
                           ))

        # ----------------------------------------------------------------------
        def CreateTreeKey(name, index):
            # Tree keys must be unique. Therefore, append whitespace based on the index
            # to ensure that we create unique values.
            return "{}{}".format(name, ' ' * index)

        # ----------------------------------------------------------------------

        # Display all the items that are used
        roots = [ value for value in six.itervalues(repo_map) if not value.dependents ]

        display_tree = OrderedDict()
        display_infos = []

        for root in roots:
            for index, (config_name, dependnecies) in enumerate(six.iteritems(root.dependencies)):
                this_result_tree, this_display_infos = Traverse(root, config_name)

                key_name = CreateTreeKey(root.Name, index)

                display_tree[key_name] = this_result_tree
                display_infos += this_display_infos

        Display(display_tree, display_infos)

        # Display all the items that aren't used
        display_tree = OrderedDict()
        display_infos = []

        for value in six.itervalues(repo_map):
            if not value.dependents:
                continue

            for index, config_name in enumerate(six.iterkeys(value.dependencies)):
                if config_name not in value.dependents:
                    display_tree[CreateTreeKey(value.Name, index)] = {}
                    display_infos.append(DisplayInfo( value.Id,
                                                      config_name,
                                                      value.root,
                                                      value.get_clone_uri_func,
                                                    ))

        if display_tree:
            output_stream.write(textwrap.dedent(
                """\



                Unused Configurations
                =====================

                """))

            Display(display_tree, display_infos)

        # Invoke the external functionality
        dm.result = callback(dm.stream, repo_map) or 0

        return dm.result

# ----------------------------------------------------------------------
def _ScmParameterToScm(value, repository_root):
    if value is None:
        return CommonEnvironmentImports.GetSCM(repository_root)

    for scm in CommonEnvironmentImports.SourceControlManagement_ALL_TYPES:
        if scm.Name == value:
            return scm

    assert False, value

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommonEnvironmentImports.CommandLine.Main())
    except KeyboardInterrupt: pass
