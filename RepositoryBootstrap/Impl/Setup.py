# ----------------------------------------------------------------------
# |  
# |  Setup.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-20 18:56:34
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""
One-time environment preparation for a repository.

"""

import os
import shutil
import sys
import textwrap

from collections import OrderedDict

import inflect as inflect_mod
import six

import RepositoryBootstrap

from RepositoryBootstrap import Constants

from RepositoryBootstrap.Impl import CommonEnvironmentImports
from RepositoryBootstrap.Impl.EnvironmentBootstrap import EnvironmentBootstrap
from RepositoryBootstrap.Impl import Utilities

from RepositoryBootstrap.Impl.ActivationActivity.PythonActivationActivity import PythonActivationActivity

from RepositoryBootstrap.SetupAndActivate.Configuration import Configuration

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
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

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Filename for generated content or standard output if the value is 'stdout'"),
                                                  repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Root of the repository"),
                                                  debug=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Write additional debug information to the console"),
                                                  verbose=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Write additional verbose information to the console"),
                                                  configuration=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Configurations to setup; all configurations defined will be setup if explicit values are not provided"),
                                                )
@CommonEnvironmentImports.CommandLine.Constraints( output_filename_or_stdout=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
                                                   repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
                                                   configuration=CommonEnvironmentImports.CommandLine.StringTypeInfo(arity='*'),
                                                   output_stream=None,
                                                 )
def EntryPoint( output_filename_or_stdout,
                repository_root,
                debug=False,
                verbose=False,
                configuration=None,
                output_stream=sys.stdout,
              ):
    configurations = configuration or []; del configuration
    
    if debug:
        verbose = True

    shell = CommonEnvironmentImports.CurrentShell
    
    # Get the setup customization module
    potential_customization_filename = os.path.join(repository_root, Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME)
    if os.path.isfile(potential_customization_filename):
        sys.path.insert(0, repository_root)
        with CommonEnvironmentImports.CallOnExit(lambda: sys.path.pop(0)):
            customization_mod = __import__(os.path.splitext(Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME)[0])

    else:
        customization_mod = None

    # ----------------------------------------------------------------------
    def Execute():
        commands = []

        for func in [ _SetupBootstrap,
                      _SetupCustom,
                      _SetupShortcuts,
                      _SetupGeneratedPermissions,
                      _SetupScmHooks,
                    ]:
            these_commands = func( shell,
                                   repository_root,
                                   customization_mod,
                                   debug,
                                   verbose,
                                   configurations,
                                 )
            if these_commands:
                commands += these_commands

        return commands

    # ----------------------------------------------------------------------

    result, commands = Utilities.GenerateCommands(Execute, debug, shell)
    
    if output_filename_or_stdout == "stdout":
        output_stream = sys.stdout
        close_stream_func = lambda: None
    else:
        output_stream = open(output_filename_or_stdout, 'w')
        close_stream_func = output_stream.close
    
    with CommonEnvironmentImports.CallOnExit(close_stream_func):
        output_stream.write(shell.GenerateCommands(commands))
    
    return result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _SetupBootstrap( shell,
                     repository_root,
                     customization_mod,
                     debug,
                     verbose,
                     explict_configurations,
                     search_depth=5,
                   ):
    # Look for all dependencies by intelligently enumerating through the file system

    search_depth += repository_root.count(os.path.sep)
    if shell.CategoryName == "Windows":
        # Remove the slash assocaited with the drive name
        assert search_depth
        search_depth -= 1

    fundamental_repo = RepositoryBootstrap.GetFundamentalRepository()

    repository_root_dirname = os.path.dirname(fundamental_repo)
    len_repository_root_dirname = len(repository_root_dirname)

    # ----------------------------------------------------------------------
    class LookupObject(object):
        def __init__(self, name):
            self.Name                       = name
            self.repository_root            = None
            self.dependent_configurations   = []

        def __str__(self):
            return CommonEnvironmentImports.CommonEnvironment.ObjectStrImpl(self)

    # ----------------------------------------------------------------------
    def EnumerateDirectories():
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
        def PushSearchItem(item):
            item = os.path.realpath(os.path.normpath(item))

            parts = item.split(os.path.sep)
            if len(parts) > search_depth:
                return

            parts_lower = set([ part.lower() for part in parts ])

            priority = 1
            for bump_name in CODE_DIRECTORY_NAMES:
                if bump_name in parts_lower:
                    priority = 0
                    break

            # Every item except the last is used for sorting
            search_items.append(( -FirstNonmatchingChar(item),              # Favor parents over other locations
                                  priority,                                 # Favor names that look like they could contain source doe
                                  len(parts),                               # Favor dirs closer to the root
                                  item.lower(),                             # Case insensitive sort
                                  item,
                                ))

            search_items.sort()

        # ----------------------------------------------------------------------
        def PopSearchItem():
            return search_items.pop(0)[-1]

        # ----------------------------------------------------------------------
        def Impl( skip_root,
                  preprocess_item_func=None,            # def Func(item) -> item
                ):
            preprocess_item_func = preprocess_item_func or (lambda item: item)

            while search_items:
                search_item = PopSearchItem()

                # Don't process if the dir has already been processed
                if search_item in searched_items:
                    continue

                searched_items.add(search_item)

                # Don't process if the dir doesn't exist anymore (these searched can
                # take a while and dirs come and go)
                if not os.path.isdir(search_item):
                    continue

                # Don't process if the dir has been explicitly ignored
                if os.path.exists(os.path.join(search_item, Constants.IGNORE_DIRECTORY_AS_BOOTSTRAP_DEPENDENCY_SENTINEL_FILENAME)):
                    continue

                yield search_item

                try:
                    # Add the parent to the queue
                    potential_parent = os.path.dirname(search_item)
                    if potential_parent != search_item:
                        if not skip_root or os.path.dirname(potential_parent) != potential_parent:
                            PushSearchItem(preprocess_item_func(potential_parent))

                    # Add the children to the queue
                    for item in os.listdir(search_item):
                        fullpath = os.path.join(search_item, item)
                        if not os.path.isdir(fullpath):
                            continue

                        if item.lower() in ENUMERATE_EXCLUDE_DIRS:
                            continue

                        PushSearchItem(preprocess_item_func(fullpath))

                except PermissionError:
                    pass

        # ----------------------------------------------------------------------

        PushSearchItem(repository_root)

        if shell.CategoryName == "Windows":
            # ----------------------------------------------------------------------
            def ItemPreprocessor(item):
                drive, suffix = os.path.splitdrive(item)
                if drive[-1] == ':':
                    drive = drive[:-1]

                return "{}:{}".format(drive.upper(), suffix)

            # ----------------------------------------------------------------------

            for item in Impl(True, ItemPreprocessor):
                yield item

            # If here, look at other drive locations
            import win32api
            import win32file

            # <Module 'win32api' has not 'GetLogicalDriveStrings' member, but source is unavailable. Consider adding this module to extension-pkg-whitelist if you want to perform analysis based on run-time introspection of living objects.> pylint: disable = I1101

            for drive in [ drive for drive in win32api.GetLogicalDriveStrings().split('\000') if drive and win32file.GetDriveType(drive) == win32file.DRIVE_FIXED ]:
                PushSearchItem(drive)

            for item in Impl(False, ItemPreprocessor):
                yield item

        else:
            for item in Impl(False):
                yield item

    # ----------------------------------------------------------------------

    # Get the configurations from the setup script
    configurations = None
    is_tool_repository = False

    if customization_mod:
        dependencies_func = getattr(customization_mod, Constants.SETUP_ENVIRONMENT_DEPENDENCIES_METHOD_NAME, None)
        if dependencies_func is not None:
            configurations = dependencies_func()

            if configurations and not isinstance(configurations, dict):
                configurations = { None : configurations, }

            # Is this a tool repo? Tool repos are specified via the ToolRepository 
            # decorator.
            is_tool_repository = ( hasattr(dependencies_func, "_self_wrapper") and
                                   dependencies_func._self_wrapper.__name__ == "ToolRepository"
                                 )

    if not configurations:
        configurations = { None : Configuration("Default Configuration"),
                         }

    has_configurations = len(configurations) > 1 or next(six.iterkeys(configurations)) is not None

    # A tool repository cannot have configurations, dependencies, or version specs
    if ( is_tool_repository and 
         ( has_configurations or
           next(six.itervalues(configurations)).Dependencies or
           next(six.itervalues(configurations)).VersionSpecs.Tools or
           next(six.itervalues(configurations)).VersionSpecs.Libraries
         )
       ):
        raise Exception("A tool repository cannot have any configurations, dependencies, or version specs.")

    # Remove any configurations that shouldn't be setup
    if explict_configurations:
        for config_name in list(six.iterkeys(configurations)):
            if config_name not in explict_configurations:
                del configurations[config_name]

    # Create a repo lookup list
    fundamental_name, fundamental_guid = Utilities.GetRepositoryUniqueId(fundamental_repo)

    id_lookup = OrderedDict([ ( fundamental_guid, LookupObject(fundamental_name), ),
                            ])

    for config_name, config_info in six.iteritems(configurations):
        for dependency_info in config_info.Dependencies:
            if dependency_info.RepositoryId not in id_lookup:
                id_lookup[dependency_info.RepositoryId] = LookupObject(dependency_info.FriendlyName)

            id_lookup[dependency_info.RepositoryId].dependent_configurations.append(config_name)

    # Display status
    col_sizes = [ 54, 32, 100, ]
    display_template = "{{name:<{0}}}  {{guid:<{1}}}  {{data:<{2}}}".format(*col_sizes)

    max_config_name_length = int(col_sizes[0] * 0.75)
    config_display_info = []

    for config_name, config_info in six.iteritems(configurations):
        if config_name is None:
            continue

        max_config_name_length = max(max_config_name_length, len(config_name))
        config_display_info.append(( config_name, config_info.Description ))

    sys.stdout.write(textwrap.dedent(
        """\

        Your system will be scanned for these repositories:

            {header}
            {sep}
            {values}

            {configurations}

        """).format( header=display_template.format( name="Repository Name",
                                                     guid="Id",
                                                     data="Dependent Configurations",
                                                   ),
                     sep=display_template.format(**{ k : v for k, v in six.moves.zip( [ "name", "guid", "data", ],
                                                                                      [ '-' * col_size for col_size in col_sizes ],
                                                                                    ) }),
                     values='\n    '.join([ display_template.format( name=v.Name,
                                                                     guid=k,
                                                                     data=', '.join(sorted([ dc for dc in v.dependent_configurations if dc ], key=str.lower)),
                                                                   )
                                            for k, v in six.iteritems(id_lookup)
                                          ]),
                     configurations='' if not has_configurations else CommonEnvironmentImports.StringHelpers.LeftJustify( textwrap.dedent(
                                                                                                                            # <Wrong hanging indentation> pylint: disable = C0330
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
                                                                                                                                         '' if explict_configurations else textwrap.dedent(
                                                                                                                                                                            # <Wrong hanging indentation> pylint: disable = C0330
                                                                                                                                                                            """\

                                                                                                                                                                            To setup specific configurations, specify this argument one or more times on the command line:

                                                                                                                                                                                /configuration=<configuration name>
                                                                                                                                                                            """).rstrip(),
                                                                                                                                       ),
                                                                                                                          4,
                                                                                                                        ),
                   ))

    # Find them all
    remaining_repos = len(id_lookup)

    verbose_stream = CommonEnvironmentImports.StreamDecorator(sys.stdout if debug or verbose else None)

    for directory in EnumerateDirectories():
        verbose_stream.write("Searching in '{}'...\n".format(directory))

        result = Utilities.GetRepositoryUniqueId( directory,
                                                  raise_on_error=False,
                                                )
        if result is None:
            continue

        repo_guid = result[1]

        if repo_guid in id_lookup:
            # Note that we may already have a repository associated with this guid.
            # This can happen when the repo has already been found near the 
            # originating repo and the search has continued into directories further
            # away.
            if id_lookup[repo_guid].repository_root is None:
                id_lookup[repo_guid].repository_root = directory

                remaining_repos -= 1
                if not remaining_repos:
                    break
    
    verbose_stream.write('\n')

    if remaining_repos:
        unknown_repos = []

        for repo_guid, lookup_info in six.iteritems(id_lookup):
            if lookup_info.repository_root is None:
                unknown_repos.append(( lookup_info.Name, repo_guid ))

        assert unknown_repos
        raise Exception(textwrap.dedent(
            """\
            Unable to find {repository}
            {repos}
            """).format( repository=inflect.no("repository", len(unknown_repos)),
                         repos='\n'.join([ "    - {} ({})".format(repo_name, repo_guid) for repo_name, repo_guid in unknown_repos ]),
                       ))

    sys.stdout.write(textwrap.dedent(
        """\
        {repository} {was} found at {this} {location}:

            {header}
            {sep}
            {values}


        """).format( repository=inflect.no("repository", len(id_lookup)),
                     was=inflect.plural_verb("was", len(id_lookup)),
                     this=inflect.plural_adj("this", len(id_lookup)),
                     location=inflect.plural("location", len(id_lookup)),
                     header=display_template.format( name="Repository Name",
                                                     guid="Id",
                                                     data="Location",
                                                   ),
                     sep=display_template.format(**{ k : v for k, v in six.moves.zip( [ "name", "guid", "data", ],
                                                                                      [ '-' * col_size for col_size in col_sizes ],
                                                                                    ) }),
                     values=CommonEnvironmentImports.StringHelpers.LeftJustify( '\n'.join([ display_template.format( name=lookup_info.Name,
                                                                                                                     guid=repo_guid,
                                                                                                                     data=lookup_info.repository_root,
                                                                                                                   )
                                                                                            for repo_guid, lookup_info in six.iteritems(id_lookup)
                                                                                          ]),
                                                                                4,
                                                                              ),
                   ))

    # Populate the configuration locations and Calcualte fingerprints
    for config_name, config_info in six.iteritems(configurations):
        repository_roots = []

        for dependency in config_info.Dependencies:
            assert dependency.RepositoryRoot is None, dependency.RepositoryRoot
            assert dependency.RepositoryId in id_lookup, dependency

            dependency.RepositoryRoot = id_lookup[dependency.RepositoryId].repository_root

            repository_roots.append(dependency.RepositoryRoot)

        config_info.Fingerprint = Utilities.CalculateFingerprint( [ repository_root, ] + repository_roots,
                                                                  repository_root,
                                                                )

    EnvironmentBootstrap( fundamental_repo,
                          is_tool_repository,
                          has_configurations,
                          configurations,
                        ).Save( repository_root,
                                shell=shell,
                              )

# ----------------------------------------------------------------------
# <Unused argument> pylint: disable = W0613
def _SetupCustom( shell,
                  repository_root,
                  customization_mod,
                  debug,
                  verbose,
                  explict_configurations,
                ):
    if customization_mod is None or not hasattr(customization_mod, Constants.SETUP_ENVIRONMENT_ACTIONS_METHOD_NAME):
        return None

    func = CommonEnvironmentImports.Interface.CreateCulledCallable(getattr(customization_mod, Constants.SETUP_ENVIRONMENT_ACTIONS_METHOD_NAME))

    return func({ "debug" : debug,
                  "verbose" : verbose,
                  "explict_configurations" : explict_configurations,
                })

# ----------------------------------------------------------------------
# <Unused argument> pylint: disable = W0613
def _SetupShortcuts( shell,
                     repository_root,
                     customization_mod,
                     debug,
                     verbose,
                     explict_configurations,
                   ):
    activate_script = shell.CreateScriptName(Constants.ACTIVATE_ENVIRONMENT_NAME)

    shortcut_target = os.path.join(_script_dir, activate_script)
    assert os.path.isfile(shortcut_target), shortcut_target

    return [ shell.Commands.SymbolicLink( os.path.join(repository_root, activate_script),
                                          shortcut_target,
                                        ),
           ]

# ----------------------------------------------------------------------
# <Unused argument> pylint: disable = W0613
def _SetupGeneratedPermissions( shell,
                                repository_root,
                                customization_mod,
                                debug,
                                verbose,
                                explict_configurations,
                              ):
    generated_dir = os.path.join(repository_root, Constants.GENERATED_DIRECTORY_NAME, shell.CategoryName)
    assert os.path.isdir(generated_dir), generated_dir

    os.chmod(generated_dir, 0x777)

# ----------------------------------------------------------------------
# <Unused argument> pylint: disable = W0613
def _SetupScmHooks( shell,
                    repository_root,
                    customization_mod,
                    debug,
                    verbose,
                    explict_configurations,
                  ):
    # Mercurial
    if os.path.isdir(os.path.join(repository_root, ".hg")):
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

        config.set("hooks", "pretxncommit.CommonEnvironment", "python:{}:PreTxnCommit".format(hooks_filename))
        config.set("hooks", "preoutgoing.CommonEnvironment", "python:{}:PreOutgoing".format(hooks_filename))
        config.set("hooks", "pretxnchangegroup.CommonEnvironment", "python:{}:PreTxnChangeGroup".format(hooks_filename))

        backup_hg_filename = "{}.bak".format(potential_hg_filename)
        if os.path.isfile(potential_hg_filename) and not os.path.isfile(backup_hg_filename):
            shutil.copyfile(potential_hg_filename, backup_hg_filename)

        with open(potential_hg_filename, 'w') as f:
            config.write(f)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommonEnvironmentImports.CommandLine.Main())
    except KeyboardInterrupt: pass
