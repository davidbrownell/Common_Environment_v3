# ----------------------------------------------------------------------
# |  
# |  Activate.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-04 19:59:15
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Activates an environment for development activities."""

import json
import os
import sys
import textwrap

from collections import OrderedDict

import inflect as inflect_mod
import six

from RepositoryBootstrap import Constants

from RepositoryBootstrap.Impl.ActivationData import ActivationData
from RepositoryBootstrap.Impl import CommonEnvironmentImports
from RepositoryBootstrap.Impl.EnvironmentBootstrap import EnvironmentBootstrap
from RepositoryBootstrap.Impl import Utilities

from RepositoryBootstrap.Impl.ActivationActivity import ActivationActivity
from RepositoryBootstrap.Impl.ActivationActivity.PythonActivationActivity import PythonActivationActivity
from RepositoryBootstrap.Impl.ActivationActivity.ScriptsActivationActivity import ScriptsActivationActivity
from RepositoryBootstrap.Impl.ActivationActivity.ToolsActivationActivity import ToolsActivationActivity

from RepositoryBootstrap.SetupAndActivate import Configuration

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironmentImports.CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Created file containing the generated content or stdout of the value is 'stdout'"),
                                                  repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Root of the repository"),
                                                  configuration=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Configuration value to setup; all configurations will be setup if no configurations are provided"),
                                                  debug=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Write additional debug information to the console"),
                                                  verbose=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Write additional verbose information to the console"),
                                                  version_spec=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Overrides version specifications for tools and/or libraries. Example: '/version_spec=Tools/Python:v3.6.0'."),
                                                  no_python_libraries=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Disables the import of python libraries, which can be useful when pip installing python libraries for Library inclusion."),
                                                  fast=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Activate the environment as quickly as possible; in some cases, the environment activated may not have all functionality enabled as a result."),
                                                  mixin=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Activate a mixin repository at the specified folder location along with this repository"),
                                                )
@CommonEnvironmentImports.CommandLine.Constraints( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
                                                   repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                   configuration=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
                                                   version_spec=CommonEnvironmentImports.CommandLine.DictTypeInfo(require_exact_match=False, arity='?'),
                                                   mixin=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(arity='*'),
                                                   output_stream=None,
                                                 )
def Activate( output_filename_or_stdout,
              repository_root,
              configuration,
              debug=False,
              verbose=False,
              version_spec=None,
              no_python_libraries=False,
              force=False,
              fast=False,
              mixin=None,
              output_stream=sys.stdout,
            ):
    """Activates a repository for development activities."""

    nonlocals = CommonEnvironmentImports.CommonEnvironment.Nonlocals(
        configuration=configuration if configuration.lower() != "none" else None,
    )

    version_specs = version_spec or {}; del version_spec
    mixins = mixin or []; del mixin

    if debug:
        verbose = True

    output_stream = CommonEnvironmentImports.StreamDecorator(output_stream)

    # ----------------------------------------------------------------------
    def Execute():
        commands = []

        # Load the activation data
        output_stream.write("\nLoading data...")
        with output_stream.DoneManager( suffix='\n',
                                      ):
            is_activated = bool(os.getenv(Constants.DE_REPO_ACTIVATED_FLAG))

            activation_data = ActivationData.Load( repository_root,
                                                   nonlocals.configuration,
                                                   fast,
                                                   force=force or not is_activated,
                                                 )

        # Augment the version specs with those provided on the command line
        for k, v in six.iteritems(version_specs):
            keys = k.split('/')

            if keys[0] == Constants.TOOLS_SUBDIR:
                if len(keys) != 2:
                    raise Exception("'{}' is not a valid version spec; expected '{}/<Tool Name>'.".format(k, Constants.TOOLS_SUBDIR))

                name = keys[1]
                version_infos = activation_data.VersionSpecs.Tools

            elif keys[0] == Constants.LIBRARIES_SUBDIR:
                if len(keys) != 3:
                    raise Exception("'{}' is not a valid version spec; expected '{}/<Language>/<Library Name>'.".format(k, Constants.LIBRARIES_SUBDIR))

                name = keys[2]
                version_infos = activation_data.VersionSpecs.Libraries.setdefault(keys[1], [])

            else:
                raise Exception("'{}' is not a valid version spec prefix".format(keys[0]))

            found = False
            for version_info in version_infos:
                if version_info.Name == name:
                    version_info.Version = v
                    found = True
                    break

            if not found:
                version_infos.append(Configuration.VersionInfo(name, v))

        # ----------------------------------------------------------------------
        def LoadMixinLibrary(mixin_path):
            mixin_activation_data = ActivationData.Load( mixin_path,
                                                         configuration=None,
                                                         is_fast_environment=False,
                                                         force=True,
                                                       )
            if not mixin_activation_data.IsMixinRepo:
                raise Exception("The repository at '{}' is not a mixin repository".format(mixin_path))

            mixin_repo = mixin_activation_data.PrioritizedRepositories[-1]
            mixin_repo.IsMixinRepo = True

            # Add this repo as a repo to be activated if it isn't already in the list
            if not any(r.Id == mixin_repo.Id for r in activation_data.PrioritizedRepositories):
                activation_data.PrioritizedRepositories.append(mixin_repo)

        # ----------------------------------------------------------------------

        # Are we activating a mixin repository?
        is_mixin_repo = EnvironmentBootstrap.Load(repository_root).IsMixinRepo

        if is_mixin_repo:
            if force:
                raise Exception("'force' cannot be used with mixin repositories")

            LoadMixinLibrary(repository_root)
            nonlocals.configuration = activation_data.Configuration

        for mixin in mixins:
            LoadMixinLibrary(mixin)

        # Ensure that the generated dir exists
        generated_dir = activation_data.GetActivationDir()
        CommonEnvironmentImports.FileSystem.MakeDirs(generated_dir)

        methods = [ _ActivateActivationData,
                    _ActivateNames,
                    _ActivateTools,
                    _ActivatePython,
                    _ActivateScripts,
                    _ActivateCustom,
                    _ActivatePrompt,
                  ]

        if not is_mixin_repo:
            methods = [ _ActivateOriginalEnvironment,
                        _ActivateRepoEnvironmentVars,
                      ] + methods

        args = OrderedDict([ ( "output_stream", output_stream ),
                             ( "configuration", nonlocals.configuration ),
                             ( "activation_data", activation_data ),
                             ( "version_specs", activation_data.VersionSpecs ),
                             ( "generated_dir", generated_dir ),
                             ( "debug", debug ),
                             ( "verbose", verbose ),
                             ( "no_python_libraries", no_python_libraries ),
                             ( "fast", fast ),
                             ( "repositories", activation_data.PrioritizedRepositories ),
                             ( "is_mixin_repo", is_mixin_repo ),
                             ( "ignore_conflicted_library_names", activation_data.IgnoreConflictedLibraryNames ),
                           ])

        # Invoke the methods
        for original_method in methods:
            method = CommonEnvironmentImports.Interface.CreateCulledCallable(original_method)

            result = method(args)
            
            if isinstance(result, list):
                commands += result
            elif result is not None:
                commands.append(result)

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
_ListConfigurations_DisplayFormats          = [ "standard", "json", "command_line", ]

@CommonEnvironmentImports.CommandLine.EntryPoint( repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Root of the repository"),
                                                  display_format=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Controls how the output is displayed"),
                                                )
@CommonEnvironmentImports.CommandLine.Constraints( repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                   display_format=CommonEnvironmentImports.CommandLine.EnumTypeInfo(_ListConfigurations_DisplayFormats, arity='?'),
                                                 )
def ListConfigurations( repository_root,
                        display_format=_ListConfigurations_DisplayFormats[0],
                      ):
    """List all configurations available for activation by this repository."""

    repo_info = EnvironmentBootstrap.Load(repository_root)

    if display_format == "json":
        items = OrderedDict()

        for config_name, config_info in six.iteritems(repo_info.Configurations):
            if config_name is None:
                continue

            # This is a bare-bones representation of the data for a controlled set of scenarios.
            # Additional scenarios should populate additional data as needed.
            items[config_name] = { "description" : config_info.Description,
                                 }

        sys.stdout.write(json.dumps(items))
        return 0

    config_names = [ config_name for config_name in six.iterkeys(repo_info.Configurations) if config_name ]

    max_length = 30
    if config_names:
        max_length = max([ max_length, ] + [ len(config_name) for config_name in config_names ])

    lines = [ "{0:<{1}}{2}".format( config_name,
                                    max_length,
                                    " : {}".format(repo_info.Configurations[config_name].Description),
                                  )
              for config_name in config_names 
            ]

    if display_format == "standard":
        sys.stdout.write(textwrap.dedent(
            """\

            Available configurations:

            {}

            """).format('\n'.join([ "    - {}".format(line) for line in lines ]) if lines else "None"))
    elif display_format == "command_line":
        sys.stdout.write('\n'.join([ "         - {}".format(line) for line in lines ]) if lines else "None")
    else:
        assert False, display_format

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _ActivateOriginalEnvironment(generated_dir):
    original_environment = dict(os.environ)

    elimination_funcs = [ lambda value: value.startswith("PYTHON"),
                          lambda value: value.startswith("_ACTIVATE_ENVIRONMENT"),
                          lambda value: value.startswith("DEVELOPMENT_ENVIRONMENT"),
                        ]

    for k in list(six.iterkeys(original_environment)):
        for elimination_func in elimination_funcs:
            if elimination_func(k):
                del original_environment[k]
                break
    
    with open(os.path.join(generated_dir, Constants.GENERATED_ACTIVATION_ORIGINAL_ENVIRONMENT_FILENAME), 'w') as f:
        json.dump(original_environment, f)

# ----------------------------------------------------------------------
def _ActivateRepoEnvironmentVars(generated_dir, configuration):
    Commands = CommonEnvironmentImports.CurrentShell.Commands

    commands = [ Commands.Set(Constants.DE_REPO_ACTIVATED_FLAG, "1"),
                 Commands.Set(Constants.DE_REPO_ROOT_NAME, os.path.realpath(os.path.join(generated_dir, "..", "..", ".."))),
                 Commands.Set(Constants.DE_REPO_GENERATED_NAME, generated_dir),
               ]

    if configuration:
        commands.append(Commands.Set(Constants.DE_REPO_CONFIGURATION_NAME, configuration))
    return commands

# ----------------------------------------------------------------------
def _ActivateActivationData(activation_data):
    activation_data.Save()

# ----------------------------------------------------------------------
def _ActivateNames(output_stream, repositories):
    col_sizes = [ 54, 32, 100, ]

    names = []
    max_length = col_sizes[0] / 2

    for repo in repositories:
        names.append("{}{}{}".format( repo.Name,
                                      " ({})".format(repo.Configuration) if repo.Configuration else '',
                                      " [Mixin]" if repo.IsMixinRepo else '',
                                    ))
        max_length = max(max_length, len(names[-1]))

    template = "{{name:<{0}}}  {{guid:<{1}}}  {{data:<{2}}}".format(*col_sizes)

    output_stream.write(textwrap.dedent(
                            """\
                            Activating {this} {repository}...

                                {header}
                                {sep}
                                {values}

                            
                            """).format( this=inflect.plural_adj("this", len(names)),
                                         repository=inflect.no("repository", len(names)),
                                         header=template.format( name="Repository Name",
                                                                 guid="Id",
                                                                 data="Location",
                                                               ),
                                         sep=template.format(**{ k : v for k, v in six.moves.zip( [ "name", "guid", "data", ],
                                                                                                  [ '-' * col_size for col_size in col_sizes ],
                                                                                                ) }),
                                         values=CommonEnvironmentImports.StringHelpers.LeftJustify( '\n'.join([ template.format( name=name,
                                                                                                                                 guid=repo.Id,
                                                                                                                                 data=repo.Root,
                                                                                                                               )
                                                                                                                for repo, name in six.moves.zip(repositories, names)
                                                                                                              ]),
                                                                                                    4,
                                                                                                  ),
                                       ))

# ----------------------------------------------------------------------
def _ActivatePython(output_stream, configuration, repositories, version_specs, generated_dir, no_python_libraries, fast, verbose, ignore_conflicted_library_names):
    if fast:
        output_stream.write("** FAST: Activating python without libraries ({}) **\n\n".format(_script_fullpath))

        no_python_libraries = True

    return PythonActivationActivity.CreateCommands( output_stream,
                                                    verbose,
                                                    configuration,
                                                    repositories,
                                                    version_specs,
                                                    generated_dir,
                                                    no_python_libraries=no_python_libraries,
                                                    ignore_conflicted_library_names=ignore_conflicted_library_names,
                                                  )

# ----------------------------------------------------------------------
def _ActivateScripts(output_stream, configuration, repositories, version_specs, generated_dir, fast, verbose):
    if fast:
        output_stream.write("** FAST: Activating scripts without displaying conflicts ({}) **\n\n".format(_script_fullpath))

    return ScriptsActivationActivity.CreateCommands( output_stream,
                                                     verbose,
                                                     configuration,
                                                     repositories,
                                                     version_specs,
                                                     generated_dir,
                                                     no_display_conflicts=fast,
                                                   )

# ----------------------------------------------------------------------
def _ActivateTools(output_stream, configuration, repositories, version_specs, generated_dir, verbose):
    return ToolsActivationActivity.CreateCommands( output_stream,
                                                   verbose,
                                                   configuration,
                                                   repositories,
                                                   version_specs,
                                                   generated_dir,
                                                 )

# ----------------------------------------------------------------------
def _ActivateCustom(**kwargs):
    original_configuration = kwargs["configuration"]

    # ----------------------------------------------------------------------
    def RestoreConfiguration():
        kwargs["configuration"] = original_configuration

    # ----------------------------------------------------------------------

    with CommonEnvironmentImports.CallOnExit(RestoreConfiguration):
        repositories = kwargs["repositories"]

        actions = []

        for repository in repositories:
            kwargs["configuration"] = repository.Configuration

            result = ActivationActivity.CallCustomMethod( os.path.join(repository.Root, Constants.ACTIVATE_ENVIRONMENT_CUSTOMIZATION_FILENAME),
                                                          Constants.ACTIVATE_ENVIRONMENT_ACTIONS_METHOD_NAME,
                                                          kwargs,
                                                        )
            if result is not None:
                actions += result

    return actions

# ----------------------------------------------------------------------
def _ActivatePrompt(repositories, configuration, is_mixin_repo, fast):
    mixin_names = []

    index = -1
    while repositories[index].IsMixinRepo:
        mixin_names.insert(0, repositories[index].Name)
        index -= 1

    prompt = repositories[index].Name
    if configuration:
        prompt += " - {}".format(configuration)

    if mixin_names:
        prompt += " [{}]".format(', '.join(mixin_names))

    if fast:
        prompt += " ** FAST **"

    return CommonEnvironmentImports.CurrentShell.Commands.CommandPrompt(prompt)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommonEnvironmentImports.CommandLine.Main())
    except KeyboardInterrupt: pass
