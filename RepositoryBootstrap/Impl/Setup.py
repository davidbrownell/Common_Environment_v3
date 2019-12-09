# ----------------------------------------------------------------------
# |
# |  Setup.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-06-20 10:54:55
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
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

from RepositoryBootstrap.SetupAndActivate.Configuration import Configuration, Dependency

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironmentImports.CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
# These values influence the behavior of enumeration when searching for repositories.

# The following terms are given higher priority during search, as they contain names
# that are more likely to contain repositories.
CODE_DIRECTORY_NAMES                        = [
    "code",
    "coding",
    "source",
    "src",
    "development",
    "develop",
    "dev",
]

ENUMERATE_EXCLUDE_DIRS                      = ["generated", ".hg", ".git"]

_ScmConstraint                              = CommonEnvironmentImports.CommandLine.EnumTypeInfo(
    [scm.Name for scm in CommonEnvironmentImports.SourceControlManagement_ALL_TYPES],
    arity="?",
)

_DEFAULT_SEARCH_DEPTH                       = 6

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint(
    output_filename_or_stdout=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Filename for generated content or standard output if the value is 'stdout'",
    ),
    repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Root of the repository",
    ),
    recurse=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Invoke Setup on this repository and its dependencies",
    ),
    debug=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Write additional debug information to the console",
    ),
    verbose=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Write additional verbose information to the console",
    ),
    configuration=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Configurations to setup; all configurations defined will be setup if explicit values are not provided",
    ),
    max_num_searches=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Limit the number of directories searched when looking for dependencies; this value can be used to reduce the overall time it takes to search for dependencies that ultimately can't be found",
    ),
    required_ancestor_dir=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "When searching for dependencies, limit the search to directories that are descendants of this ancestor",
    ),
    all_configurations=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Setup all configurations, not just the ones used by this repository and those that it depends upon  (used with '/recurse')",
    ),
    no_hooks=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Do not setup SCM hooks",
    ),
)
@CommonEnvironmentImports.CommandLine.Constraints(
    output_filename_or_stdout=CommonEnvironmentImports.CommandLine.StringTypeInfo(),
    repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
    configuration=CommonEnvironmentImports.CommandLine.StringTypeInfo(
        arity="*",
    ),
    search_depth=CommonEnvironmentImports.CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    max_num_searches=CommonEnvironmentImports.CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    required_ancestor_dir=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(
        arity="*",
    ),
    output_stream=None,
)
def Setup(
    output_filename_or_stdout,
    repository_root,
    recurse=False,
    debug=False,
    verbose=False,
    configuration=None,
    search_depth=None,
    max_num_searches=None,
    required_ancestor_dir=None,
    use_ascii=False,
    all_configurations=False,
    no_hooks=False,
    output_stream=sys.stdout,
):
    """Perform setup activities for this repository"""

    configurations = configuration or []
    del configuration

    required_ancestor_dirs = required_ancestor_dir
    del required_ancestor_dir

    if debug:
        verbose = True

    output_stream = CommonEnvironmentImports.StreamDecorator(output_stream)

    customization_mod = _GetCustomizationMod(repository_root)

    # ----------------------------------------------------------------------
    def Execute():
        args = [
            output_stream,
            repository_root,
            customization_mod,
            debug,
            verbose,
            configurations,
        ]

        activities = [_SetupOperatingSystem]

        if recurse:
            # If here, invoke setup on this repo and all of its dependencies
            activities += [_SetupRecursive]

            args += [use_ascii, all_configurations]
        else:
            # If here, setup this specific repo
            activities += [
                lambda *args, **kwargs: _SetupBootstrap(
                    *args,
                    search_depth=search_depth,
                    max_num_searches=max_num_searches,
                    required_ancestor_dirs=required_ancestor_dirs,
                    **kwargs
                ),
                _SetupCustom,
                _SetupActivateScript,
            ]

            if not no_hooks:
                activities += [_SetupScmHooks]

        commands = []

        for func in activities:
            these_commands = func(*args)
            if these_commands:
                if isinstance(these_commands, int):
                    return these_commands

                commands += these_commands

        return commands

    # ----------------------------------------------------------------------

    result, commands = Utilities.GenerateCommands(Execute, debug)

    if output_filename_or_stdout == "stdout":
        output_stream = sys.stdout
        close_stream_func = lambda: None
    else:
        output_stream = open(output_filename_or_stdout, "w")
        close_stream_func = output_stream.close

    with CommonEnvironmentImports.CallOnExit(close_stream_func):
        output_stream.write(
            CommonEnvironmentImports.CurrentShell.GenerateCommands(commands),
        )

    return result

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint(
    repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Root of the repository",
    ),
    recurse=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Recurse into the dependencies of dependencies",
    ),
    scm=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Specify the Source Control Management system to use when displaying clone uris",
    ),
    configuration=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Specific configurations to list for this repository; configurations not provided with be omitted",
    ),
    max_num_searches=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Limit the number of directories searched when looking for dependencies; this value can be used to reduce the overall time it takes to search for dependencies that ultimately can't be found",
    ),
    required_ancestor_dir=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "When searching for dependencies, limit the search to directories that are descendants of this ancestor",
    ),
    json=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter("Output data as JSON"),
    decorate=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Decorate output so that it can be easily extracted from output",
    ),
)
@CommonEnvironmentImports.CommandLine.Constraints(
    repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
    scm=_ScmConstraint,
    configuration=CommonEnvironmentImports.CommandLine.StringTypeInfo(
        arity="*",
    ),
    search_depth=CommonEnvironmentImports.CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    max_num_searches=CommonEnvironmentImports.CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    required_ancestor_dir=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(
        arity="*",
    ),
    output_stream=None,
)
def List(
    repository_root,
    recurse=False,
    scm=None,
    configuration=None,
    search_depth=None,
    max_num_searches=None,
    required_ancestor_dir=None,
    use_ascii=False,
    json=False,
    decorate=False,
    output_stream=sys.stdout,
    verbose=False,
):
    """Lists repository information"""

    required_ancestor_dirs = required_ancestor_dir
    del required_ancestor_dir

    scm = _ScmParameterToScm(scm, repository_root)

    if decorate:
        output_stream.write(
            "//--//--//--//--//--//--//--//--//--//--//--//--//--//--//--//\n",
        )

        # ----------------------------------------------------------------------
        def OnExit():
            output_stream.write(
                "\n//--//--//--//--//--//--//--//--//--//--//--//--//--//--//--//\n",
            )

        # ----------------------------------------------------------------------

    else:
        # ----------------------------------------------------------------------
        def OnExit():
            pass

        # ----------------------------------------------------------------------

    with CommonEnvironmentImports.CallOnExit(OnExit):
        if json:
            sink = six.moves.StringIO()

            repo_map = _CreateRepoMap(
                repository_root,
                configuration,
                recurse,
                CommonEnvironmentImports.StreamDecorator(sink),
                verbose,
                search_depth=search_depth,
                max_num_searches=max_num_searches,
                required_ancestor_dirs=required_ancestor_dirs,
            )
            if isinstance(repo_map, int):
                output_stream.write(sink.getvalue())
                return repo_map

            # Calculate the priorities of the items
            for value in six.itervalues(repo_map):
                value.priority = 0

            # ----------------------------------------------------------------------
            def Walk(repo_value, priority_modifier):
                repo_value.priority += priority_modifier

                for config_name in repo_value.dependencies:
                    for dependency_id, _ in repo_value.dependencies[config_name]:
                        Walk(repo_map[dependency_id], priority_modifier + 1)

            # ----------------------------------------------------------------------

            for value in six.itervalues(repo_map):
                if value.dependents:
                    continue

                Walk(value, 1)

            # Sort by priority
            repo_ids = list(six.iterkeys(repo_map))
            repo_ids.sort(
                key=lambda id: (repo_map[id].priority, repo_map[id].Name),
                reverse=True,
            )

            # Create the output

            # ----------------------------------------------------------------------
            def SortRepoConfigList(l):
                l = list(l)

                l.sort(
                    key=(
                        lambda item: (
                            repo_map[item[0]].priority,
                            repo_map[item[0]].Name,
                            item[1],
                        )
                    ),
                    reverse=True,
                )

                return l

            # ----------------------------------------------------------------------

            output = []

            for repo_id in repo_ids:
                repo = repo_map[repo_id]

                dependents = OrderedDict(
                    [
                        (k or "<None>", SortRepoConfigList(v))
                        for k,
                        v in six.iteritems(repo.dependents)
                    ],
                )

                dependencies = OrderedDict(
                    [
                        (k or "<None>", SortRepoConfigList(v))
                        for k,
                        v in six.iteritems(repo.dependencies)
                    ],
                )

                output.append(
                    {
                        "name": repo.Name,
                        "id": repo.Id,
                        "root": repo.root,
                        "clone_uri": repo.get_clone_uri_func(
                            scm,
                        ) if repo.get_clone_uri_func else None,
                        "priority": repo.priority,
                        "configurations": repo.configurations,
                        "dependents": dependents,
                        "dependencies": dependencies,
                    },
                )

            # Write the output
            output_stream.write(json_mod.dumps(output))

            return 0

        # ----------------------------------------------------------------------
        def Callback(output_stream, repo_map):
            for value in six.itervalues(repo_map):
                if value.root is None:
                    return -1

            return 0

        # ----------------------------------------------------------------------

        return _SimpleFuncImpl(
            Callback,
            repository_root,
            recurse,
            scm,
            configuration,
            output_stream,
            verbose,
            search_depth=search_depth,
            max_num_searches=max_num_searches,
            required_ancestor_dirs=required_ancestor_dirs,
            use_ascii=use_ascii,
        )

# ----------------------------------------------------------------------
@CommonEnvironmentImports.CommandLine.EntryPoint(
    repository_root=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Root of the repository",
    ),
    repositories_root=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Root of all repositories; repositories not found under this directory will be cloned relative to it",
    ),
    recurse=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Recurse into the dependencies of dependencies",
    ),
    scm=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Specify the Source Control Management system to use when displaying clone uris",
    ),
    uri_dict=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Values used to populate clone uri templates",
    ),
    configuration=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Specific configurations to list for this repository; configurations not provided with be omitted",
    ),
    max_num_searches=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "Limit the number of directories searched when looking for dependencies; this value can be used to reduce the overall time it takes to search for dependencies that ultimately can't be found",
    ),
    required_ancestor_dir=CommonEnvironmentImports.CommandLine.EntryPoint.Parameter(
        "When searching for dependencies, limit the search to directories that are descendants of this ancestor",
    ),
)
@CommonEnvironmentImports.CommandLine.Constraints(
    repository_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(),
    repositories_root=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
    ),
    scm=_ScmConstraint,
    uri_dict=CommonEnvironmentImports.CommandLine.DictTypeInfo(
        require_exact_match=False,
        arity="?",
    ),
    configuration=CommonEnvironmentImports.CommandLine.StringTypeInfo(
        arity="*",
    ),
    search_depth=CommonEnvironmentImports.CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    max_num_searches=CommonEnvironmentImports.CommandLine.IntTypeInfo(
        min=1,
        arity="?",
    ),
    required_ancestor_dir=CommonEnvironmentImports.CommandLine.DirectoryTypeInfo(
        arity="*",
    ),
    output_stream=None,
)
def Enlist(
    repository_root,
    repositories_root,
    recurse=False,
    scm=None,
    uri_dict=None,
    configuration=None,
    search_depth=None,
    max_num_searches=None,
    required_ancestor_dir=None,
    use_ascii=False,
    output_stream=sys.stdout,
    verbose=False,
):
    """Enlists in provided repositories"""

    required_ancestor_dirs = required_ancestor_dir
    del required_ancestor_dir

    if repository_root not in required_ancestor_dirs:
        required_ancestor_dirs.append(repository_root)
    if repositories_root not in required_ancestor_dirs:
        required_ancestor_dirs.append(repositories_root)

    scm = _ScmParameterToScm(scm, repository_root)

    nonlocals = CommonEnvironmentImports.CommonEnvironment.Nonlocals(
        should_continue=None,
        previously_updated=set(),
    )

    # ----------------------------------------------------------------------
    def Callback(output_stream, repo_map):
        to_clone = []
        to_update = []
        missing = []

        for value in six.itervalues(repo_map):
            if value.root is not None:
                if (
                    value.root != repository_root
                    and value.root not in nonlocals.previously_updated
                ):
                    to_update.append(value)

                continue

            if value.get_clone_uri_func is not None:
                clone_uri = value.get_clone_uri_func(scm)
                if clone_uri is not None:
                    try:
                        clone_uri = clone_uri.format(**uri_dict)
                    except KeyError as ex:
                        output_stream.write(
                            "\nERROR: The key {} is used in the clone uri '{}' (defined in '{}') and must be provided on the command line using the 'uri_dict' argument.\n".format(
                                str(ex),
                                clone_uri,
                                value.root,
                            ),
                        )
                        return -1

                    to_clone.append((value, clone_uri))
                    continue

            missing.append(value)

        if to_update:
            output_stream.write(
                "\n\nUpdating {}...".format(inflect.no("repository", len(to_update))),
            )
            with output_stream.DoneManager() as dm:
                for index, value in enumerate(to_update):
                    dm.stream.write(
                        "Processing '{}' ({} of {})...".format(
                            value.Name,
                            index + 1,
                            len(to_update),
                        ),
                    )
                    with dm.stream.DoneManager(
                        suffix="\n",
                    ) as update_dm:
                        for func in [scm.Pull, scm.Update]:
                            update_dm.result, output = func(value.root)
                            update_dm.stream.write(output)

                            if update_dm.result != 0:
                                return update_dm.result

                        nonlocals.previously_updated.add(value.root)

                if dm.result != 0:
                    return dm.result

        if to_clone:
            output_stream.write(
                "\n\nCloning {}...".format(inflect.no("repository", len(to_clone))),
            )
            with output_stream.DoneManager() as dm:
                for index, (value, clone_uri) in enumerate(to_clone):
                    dm.stream.write(
                        "Processing '{}' ({} of {})...".format(
                            value.Name,
                            index + 1,
                            len(to_clone),
                        ),
                    )
                    with dm.stream.DoneManager() as clone_dm:
                        dest_dir = os.path.join(
                            repositories_root,
                            value.Name.replace("_", os.path.sep),
                        )
                        if os.path.isdir(dest_dir):
                            clone_dm.stream.write(
                                "WARNING: The output dir '{}' already exists and will not be replaced by the repo '{}'.\n".format(
                                    dest_dir,
                                    value.Name,
                                ),
                            )
                            clone_dm.result = 1

                            continue

                        clone_dm.result, output = scm.Clone(clone_uri, dest_dir)
                        clone_dm.stream.write(output)

                        if clone_dm.result != 0:
                            return clone_dm.result

        if missing:
            output_stream.write(
                textwrap.dedent(
                    """\


                    WARNING: Unable to clone these repositories:
                    {}
                    """,
                ).format(
                    "\n".join(
                        [
                            "    - {} <{}>".format(value.Name, value.Id)
                            for value in missing
                        ],
                    ),
                ),
            )

            return 1

        nonlocals.should_continue = bool(to_clone)
        return 0

    # ----------------------------------------------------------------------

    while True:
        nonlocals.should_continue = False

        result = _SimpleFuncImpl(
            Callback,
            repository_root,
            recurse,
            scm,
            configuration,
            output_stream,
            verbose,
            search_depth=search_depth,
            max_num_searches=max_num_searches,
            required_ancestor_dirs=required_ancestor_dirs,
            additional_repo_search_dirs=[repositories_root],
            use_ascii=use_ascii,
        )

        if result != 0 or not nonlocals.should_continue:
            break

    return result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _SetupOperatingSystem(output_stream, *args, **kwargs):
    if CommonEnvironmentImports.CurrentShell.CategoryName == "Windows":
        import winreg

        # Check to see if developer mode is enabled on Windows
        output_stream.write("Verifying developer mode on Windows...")
        with output_stream.DoneManager() as this_dm:
            try:
                hkey = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock",
                )
                with CommonEnvironmentImports.CallOnExit(lambda: winreg.CloseKey(hkey)):
                    value = winreg.QueryValueEx(
                        hkey,
                        "AllowDevelopmentWithoutDevLicense",
                    )[0]

                    if value != 1:
                        raise Exception(
                            textwrap.dedent(
                                """\

                                Windows Developer Mode is not enabled; this is a requirement for the setup process
                                as Developer Mode allows for the creation of symbolic links without admin privileges.

                                To enable Developer Mode in Windows:

                                    1) Launch 'Developer settings'
                                    2) Select 'Developer mode'

                                """,
                            ),
                        )
            except FileNotFoundError:
                # This key isn't available on all versions of Windows
                pass

        # Check to see if long paths are enabled on Windows
        output_stream.write("Verifying long path support on Windows...")
        with output_stream.DoneManager() as this_dm:
            try:
                # Python imports can begin to break down if long paths aren't enabled
                hkey = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\ControlSet001\Control\FileSystem",
                )
                with CommonEnvironmentImports.CallOnExit(lambda: winreg.CloseKey(hkey)):
                    value = winreg.QueryValueEx(hkey, "LongPathsEnabled")[0]

                    if value != 1:
                        this_dm.stream.write(
                            textwrap.dedent(
                                """\


                                WARNING: Long path support is not enabled. While this isn't a requirement
                                         for running on Windows, it could present problems with
                                         python imports in deeply nested directory hierarchies.

                                         To enable long path support in Windows:

                                            1) Launch 'regedit'
                                            2) Navigate to 'HKEY_LOCAL_MACHINE\\SYSTEM\\ControlSet001\\Control\\FileSystem'
                                            3) Edit the value 'LongPathsEnabled'
                                            4) Set the value to 1


                                """,
                            ),
                        )

            except FileNotFoundError:
                # This key isn't available on all versions of Windows
                pass

        # Check to see if git is installed and if its settings are set to the best defaults
        if "usage: git" in CommonEnvironmentImports.Process.Execute("git")[1] != -1:
            output_stream.write("Verifying git settings on Windows...")
            with output_stream.DoneManager() as this_dm:
                this_dm.result, git_output = CommonEnvironmentImports.Process.Execute(
                    "git config --get core.autocrlf",
                )

                if this_dm.result != 0:
                    this_dm.stream.write(git_output)
                    assert False, this_dm.result

                git_output = git_output.strip()

                if git_output != "false":
                    this_dm.stream.write(
                        textwrap.dedent(
                            """\


                            WARNING: Git is configured to modify line endings on checkin and/or checkout.
                                     While this was the recommended setting in the past, it presents problems
                                     when running on Windows and the Windows Subsystem for Linux.

                                     It is recommended that you change this setting to not modify line endings:

                                        1) 'git config --global core.autocrlf false`

                            """,
                        ),
                    )

        output_stream.write("\n")


# ----------------------------------------------------------------------
def _SetupRecursive(
    output_stream,
    repository_root,
    customization_mod,
    debug,
    verbose,
    explicit_configurations,
    use_ascii,
    all_configurations,
):
    # ----------------------------------------------------------------------
    def Callback(output_stream, repo_map):
        Commands = CommonEnvironmentImports.CurrentShell.Commands

        with output_stream.DoneManager(
            display=False,
        ) as dm:
            dm.stream.write("\n\n")

            command_line_template = "{source}{cmd}{debug}{verbose} {{}}".format(
                source="./" if CommonEnvironmentImports.CurrentShell.CategoryName == "Linux" else "",
                cmd=CommonEnvironmentImports.CurrentShell.CreateScriptName(
                    Constants.SETUP_ENVIRONMENT_NAME,
                ),
                debug="" if not debug else " /debug",
                verbose="" if not verbose else " /verbose",
            )

            fundamental_root_dir = CommonEnvironmentImports.FileSystem.RemoveTrailingSep(
                os.getenv(Constants.DE_FUNDAMENTAL_ROOT_NAME),
            )

            # Get all repos other than the fundamental repo (as this will already be
            # setup and activated when this functionality is invoked).
            values = [
                value
                for value in six.itervalues(repo_map)
                if (value.root and value.root != fundamental_root_dir)
            ]

            setup_error_variable_name = "_setup_error"

            for index, value in enumerate(values):
                dm.stream.write(
                    "Setting up '{} <{}>' ({} of {})...".format(
                        value.Name,
                        value.Id,
                        index + 1,
                        len(values),
                    ),
                )
                with dm.stream.DoneManager(
                    suffix="\n",
                ) as this_dm:
                    if value.root is None:
                        this_dm.stream.write(
                            "This repository does not exist in the current filesystem.\n",
                        )
                        this_dm.result = 1

                        continue

                    if all_configurations:
                        configurations = []
                    elif value.root == repository_root:
                        configurations = explicit_configurations
                    else:
                        configurations = [
                            configuration
                            for configuration in value.configurations
                            if configuration is not None
                        ]

                    commands = [
                        Commands.EchoOff(),
                        Commands.PushDirectory(value.root),
                        Commands.Call(
                            command_line_template.format(
                                ""
                                if not configurations
                                else " ".join(
                                    [
                                        '"/configuration={}"'.format(configuration)
                                        for configuration in configurations
                                    ],
                                ),
                            ),
                        ),
                        Commands.PersistError(setup_error_variable_name),
                        Commands.PopDirectory(),
                        Commands.ExitOnError(
                            variable_name=setup_error_variable_name,
                        ),
                    ]

                    this_dm.result = CommonEnvironmentImports.CurrentShell.ExecuteCommands(
                        commands,
                        this_dm.stream,
                    )

            return dm.result

    # ----------------------------------------------------------------------

    return _SimpleFuncImpl(
        Callback,
        repository_root,
        True,                                                               # recursive
        _ScmParameterToScm(None, repository_root),
        explicit_configurations=explicit_configurations,
        output_stream=output_stream,
        verbose=verbose,
        use_ascii=use_ascii,
    )


# ----------------------------------------------------------------------
def _SetupBootstrap(
    output_stream,
    repository_root,
    customization_mod,
    debug,
    verbose,
    explicit_configurations,
    search_depth=None,
    max_num_searches=None,
    required_ancestor_dirs=None,
):
    repo_data = _RepoData.Create(
        customization_mod,
        supported_configurations=explicit_configurations,
    )

    # A mixin repository cannot have configurations, dependencies or version specs
    if repo_data.IsMixinRepository and repo_data.HasConfigurations:
        raise Exception(
            "A mixin repository cannot have configurations, dependencies, or version specs.",
        )

    display_cols = [54, 32, 100]
    display_template = "{{0:<{0}}}  {{1:<{1}}}  {{2:<{2}}}".format(*display_cols)

    # ----------------------------------------------------------------------
    def InitialDisplay(repo_map):
        max_config_name_length = int(display_cols[0] * 0.75)
        config_display_info = []

        for config_name, config_info in six.iteritems(repo_data.Configurations):
            if config_name is None:
                continue

            max_config_name_length = max(max_config_name_length, len(config_name))
            config_display_info.append((config_name, config_info.Description))

        # ----------------------------------------------------------------------
        def GetUniqueConfigurations(map_value):
            configurations = set()

            for v in six.itervalues(map_value.dependents):
                for id, config_name in v:
                    if config_name is not None:
                        configurations.add(config_name)

            configurations = sorted(
                list(configurations),
                key=str.lower,
            )
            return configurations

        # ----------------------------------------------------------------------

        if repo_data.HasConfigurations:
            configuration_info = textwrap.dedent(
                # <Wrong hanging indentation> pylint: disable = C0330
                """\
                Based on these configurations:

                    {}
                {}
                """,
            ).format(
                CommonEnvironmentImports.StringHelpers.LeftJustify(
                    "\n".join(
                        [
                            "- {0:<{1}}{2}".format(
                                config_name,
                                max_config_name_length,
                                " : {}".format(description),
                            )
                            for config_name,
                            description in config_display_info
                        ],
                    ),
                    4,
                ),
                "" if repo_data.AreConfigurationsFiltered else textwrap.dedent(
                    # <Wrong hanging indentation> pylint: disable = C0330
                    """\

                    To operate on specific configurations, specify this argument one or more times on the command line:

                        /configuration=<configuration name>
                    """,
                ).rstrip(),
            )
        else:
            configuration_info = ""

        output_stream.write(
            textwrap.dedent(
                """\

                Your system will be scanned for these repositories:

                    {header}
                    {sep}
                    {values}

                    {configurations}

                """,
            ).format(
                header=display_template.format(
                    "Repository Name",
                    "Id",
                    "Dependent Configurations",
                ),
                sep=display_template.format(
                    *["-" * col_size for col_size in display_cols]
                ),
                values="\n    ".join(
                    [
                        display_template.format(
                            v.Name,
                            k,
                            ", ".join(GetUniqueConfigurations(v)),
                        )
                        for k,
                        v in six.iteritems(repo_map)
                    ],
                ),
                configurations=CommonEnvironmentImports.StringHelpers.LeftJustify(
                    configuration_info,
                    4,
                ),
            )
        )

    # ----------------------------------------------------------------------

    repo_map = _RepositoriesMap.Create(
        repository_root,
        repo_data,
        recurse=False,
        output_stream=output_stream,
        verbose=verbose,
        search_depth=search_depth,
        max_num_searches=max_num_searches,
        required_ancestor_dirs=required_ancestor_dirs,
        on_search_begin_func=InitialDisplay,
    )

    remaining_repos = [value for value in six.itervalues(repo_map) if value.root is None]
    if remaining_repos:
        raise Exception(
            textwrap.dedent(
                """\
                Unable to find {repository}

                {repos}

                If you believe that these repositories are already on your system, consider
                increasing the directory search depth by providing the '/search_depth=<value>'
                command line argument with a value greater than '{search_depth}'.

                Any or all of these command line arguments can be used to limit the number
                of directories queried when searching for dependencies:

                    /max_num_searches=<value>
                    /required_ancestor_dir=<value>
                    /search_depth=<value>

                """,
            ).format(
                repository=inflect.no("repository", len(remaining_repos)),
                repos="\n".join(
                    ["    - {} <{}>".format(ri.Name, ri.Id) for ri in remaining_repos],
                ),
                search_depth=search_depth or _DEFAULT_SEARCH_DEPTH,
            ),
        )

    output_stream.write(
        textwrap.dedent(
            """\
            {repository} {was} found at {this} {location}

                {header}
                {sep}
                {values}


            """,
        ).format(
            repository=inflect.no("repository", len(repo_map)),
            was=inflect.plural("was", len(repo_map)),
            this=inflect.plural("this", len(repo_map)),
            location=inflect.plural("location", len(repo_map)),
            header=display_template.format("Repository Name", "Id", "Location"),
            sep=display_template.format(*["-" * col_size for col_size in display_cols]),
            values=CommonEnvironmentImports.StringHelpers.LeftJustify(
                "\n".join(
                    [
                        display_template.format(value.Name, value.Id, value.root)
                        for value in six.itervalues(repo_map)
                    ],
                ),
                4,
            ),
        )
    )

    # Populate the configurations and calculate the fingerprints
    for config_name, config_info in six.iteritems(repo_data.Configurations):
        repository_roots = []

        for dependency in config_info.Dependencies:
            assert dependency.RepositoryRoot is None or (
                dependency.RepositoryId in repo_map
                and repo_map[dependency.RepositoryId].root == dependency.RepositoryId
            ), dependency.RepositoryRoot
            assert dependency.RepositoryId in repo_map, dependency.RepositoryId

            dependency.RepositoryRoot = repo_map[dependency.RepositoryId].root

            repository_roots.append(dependency.RepositoryRoot)

        config_info.Fingerprint = Utilities.CalculateFingerprint(
            [repository_root] + repository_roots,
            repository_root,
        )

    return EnvironmentBootstrap(
        RepositoryBootstrap.GetFundamentalRepository(),
        repo_data.IsMixinRepository,
        repo_data.HasConfigurations,
        repo_data.Configurations,
    ).Save(repository_root)

# ----------------------------------------------------------------------
# <Unused argument> pylint: disable = W0613
def _SetupCustom(
    output_stream,
    repository_root,
    customization_mod,
    debug,
    verbose,
    explicit_configurations,
):
    if customization_mod is None or not hasattr(
        customization_mod,
        Constants.SETUP_ENVIRONMENT_ACTIONS_METHOD_NAME,
    ):
        return None

    func = CommonEnvironmentImports.Interface.CreateCulledCallable(
        getattr(customization_mod, Constants.SETUP_ENVIRONMENT_ACTIONS_METHOD_NAME),
    )

    return func(
        {
            "debug": debug,
            "verbose": verbose,
            "explicit_configurations": explicit_configurations,
        },
    )


# ----------------------------------------------------------------------
# <Unused argument> pylint: disable = W0613
def _SetupActivateScript(
    output_stream,
    repository_root,
    customization_mod,
    debug,
    verbose,
    explicit_configurations,
):
    environment_name = os.getenv(Constants.DE_ENVIRONMENT_NAME)
    assert environment_name

    # Create the commands
    activate_script_name = CommonEnvironmentImports.CurrentShell.CreateScriptName(
        Constants.ACTIVATE_ENVIRONMENT_NAME,
        filename_only=True,
    )

    implementation_script = os.path.join(_script_dir, activate_script_name)
    assert os.path.isfile(implementation_script), implementation_script

    commands = [
        CommonEnvironmentImports.CurrentShell.Commands.EchoOff(),
        CommonEnvironmentImports.CurrentShell.Commands.Set(
            Constants.DE_ENVIRONMENT_NAME,
            environment_name,
        ),
        CommonEnvironmentImports.CurrentShell.Commands.PushDirectory(None),
        CommonEnvironmentImports.CurrentShell.Commands.Call(
            "{} {}".format(
                implementation_script,
                CommonEnvironmentImports.CurrentShell.AllArgumentsScriptVariable,
            ),
            exit_on_error=False,
        ),
        CommonEnvironmentImports.CurrentShell.Commands.PersistError("_activate_error"),
        CommonEnvironmentImports.CurrentShell.Commands.PopDirectory(),
        CommonEnvironmentImports.CurrentShell.Commands.ExitOnError(
            variable_name="_activate_error",
            return_code=CommonEnvironmentImports.CurrentShell.DecorateEnvironmentVariable(
                "_activate_error",
            ),
        ),
    ]

    # Write the local file
    activate_name, activate_ext = os.path.splitext(activate_script_name)

    activation_filename = os.path.join(
        repository_root,
        "{}{}{}".format(
            activate_name,
            ".{}".format(environment_name)
            if environment_name != Constants.DEFAULT_ENVIRONMENT_NAME
            else "",
            activate_ext,
        ),
    )

    with open(activation_filename, "w") as f:
        f.write(CommonEnvironmentImports.CurrentShell.GenerateCommands(commands))

    CommonEnvironmentImports.CurrentShell.MakeFileExecutable(activation_filename)
    CommonEnvironmentImports.CurrentShell.UpdateOwnership(activation_filename)

    return None


# ----------------------------------------------------------------------
# <Unused argument> pylint: disable = W0613
def _SetupScmHooks(
    output_stream,
    repository_root,
    customization_mod,
    debug,
    verbose,
    explicit_configurations,
):
    # ----------------------------------------------------------------------
    def Mercurial():
        hooks_filename = os.path.normpath(
            os.path.join(_script_dir, "Hooks", "Mercurial.py"),
        )
        assert os.path.isfile(hooks_filename), hooks_filename

        import configparser

        config = configparser.ConfigParser(
            allow_no_value=True,
        )

        potential_hg_filename = os.path.join(repository_root, ".hg", "hgrc")
        if os.path.isfile(potential_hg_filename):
            with open(potential_hg_filename) as f:
                config.read_file(f)

        if not config.has_section("hooks"):
            config.add_section("hooks")

        relative_hooks_filename = CommonEnvironmentImports.FileSystem.GetRelativePath(
            repository_root,
            hooks_filename,
        ).replace(os.path.sep, "/")

        config.set(
            "hooks",
            "pretxncommit.CommonEnvironment",
            "python:{}:PreTxnCommit".format(relative_hooks_filename),
        )
        config.set(
            "hooks",
            "preoutgoing.CommonEnvironment",
            "python:{}:PreOutgoing".format(relative_hooks_filename),
        )
        config.set(
            "hooks",
            "pretxnchangegroup.CommonEnvironment",
            "python:{}:PreTxnChangeGroup".format(relative_hooks_filename),
        )

        backup_hg_filename = "{}.bak".format(potential_hg_filename)
        if os.path.isfile(potential_hg_filename) and not os.path.isfile(
            backup_hg_filename,
        ):
            shutil.copyfile(potential_hg_filename, backup_hg_filename)

        with open(potential_hg_filename, "w") as f:
            config.write(f)

    # ----------------------------------------------------------------------
    def Git():
        # Detect if we are running directly on Windows or within WSL
        is_windows = (
            CommonEnvironmentImports.CurrentShell.CategoryName == "Windows"
            or "Windows" in CommonEnvironmentImports.Process.Execute("uname -r")[1]
        )

        hooks_dir = os.path.join(repository_root, ".git", "hooks")
        CommonEnvironmentImports.FileSystem.MakeDirs(hooks_dir)

        hooks_impl_filename = os.path.normpath(
            os.path.join(_script_dir, "Hooks", "Git.py"),
        )
        assert os.path.isfile(hooks_impl_filename), hooks_impl_filename

        relative_hooks_impl_filename = CommonEnvironmentImports.FileSystem.GetRelativePath(
            repository_root,
            hooks_impl_filename,
        ).replace(
            os.path.sep,
            "/",
        )

        import io

        for name in ["commit-msg", "pre-push", "pre-receive"]:
            # Git hooks don't work well on Windows; create them in an initially disabled state so that
            # someone can opt-in to their usage.
            if is_windows:
                name = "_{}".format(name)

            with io.open(
                os.path.join(hooks_dir, name),
                "w",
                newline="\n",
            ) as f:
                if name == "pre-receive":
                    # This hook is run from the .git dir on the server. The relative path is
                    # based on the root dir, so we need to move up an additional level to compensate
                    # for the .git dir.
                    this_relative_hooks_impl_filename = "../{}".format(
                        relative_hooks_impl_filename,
                    )
                else:
                    this_relative_hooks_impl_filename = relative_hooks_impl_filename

                f.write(
                    textwrap.dedent(
                        """\
                        #!/bin/bash
                        python {} {} "$*"
                        exit $?
                        """,
                    ).format(this_relative_hooks_impl_filename, name.replace("-", "_")),
                )

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
    def Create(
        cls,
        customization_mod,
        supported_configurations=None,
    ):
        if customization_mod:
            # Get the dependency info
            dependencies_func = getattr(
                customization_mod,
                Constants.SETUP_ENVIRONMENT_DEPENDENCIES_METHOD_NAME,
                None,
            )
            if dependencies_func:
                configurations = dependencies_func()

                if configurations and not isinstance(configurations, dict):
                    configurations = {None: configurations}

                # Mixin repos are specified via the MixinRepository decorator
                is_mixin_repository = (
                    hasattr(dependencies_func, "_self_wrapper")
                    and dependencies_func._self_wrapper.__name__ == "MixinRepository"
                )

                if supported_configurations:
                    for config_name in list(six.iterkeys(configurations)):
                        if config_name not in supported_configurations:
                            del configurations[config_name]

                    if not configurations:
                        raise Exception(
                            "No configurations were found matching {}".format(
                                ", ".join(
                                    [
                                        '"{}"'.format(supported_configuration)
                                        for supported_configuration in supported_configurations
                                    ],
                                ),
                            ),
                        )

                return cls(
                    configurations,
                    bool(supported_configurations),
                    is_mixin_repository,
                )

        # Create a default configuration
        return cls(
            {None: Configuration("Default Configuration")},
            are_configurations_filtered=False,
            is_mixin_repository=False,
        )

    # ----------------------------------------------------------------------
    def __init__(self, configurations, are_configurations_filtered, is_mixin_repository):
        self.Configurations                 = configurations
        self.AreConfigurationsFiltered      = are_configurations_filtered
        self.IsMixinRepository              = is_mixin_repository

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    @property
    def HasConfigurations(self):
        return (
            len(self.Configurations) > 1
            or next(six.iterkeys(self.Configurations)) is not None
        )


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
            self.configurations             = []

            self.get_clone_uri_func         = None

            # The following will only be populated when recurse is True
            self.dependents                 = OrderedDict()                 # { <config_name> : [ ( <dependent_repo_id>, <dependent_config_name> ), ... ], ... }
            self.dependencies               = OrderedDict()                 # { <config_name> : [ ( <dependency_repo_id>, <dependency_config_name> ), ... ], ... }

        # ----------------------------------------------------------------------
        def __repr__(self):
            return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    # |  Public Methods

    @classmethod
    def Create(
        cls,
        repository_root,
        repo_data,
        recurse,
        output_stream,
        verbose,
        supported_configurations=None,
        search_depth=None,
        max_num_searches=None,
        required_ancestor_dirs=None,
        on_search_begin_func=None,          # def Func(self)
        additional_search_dirs=None,
    ):
        self = cls()
        repo_cache = {}

        fundamental_repo_name, fundamental_repo_id = RepositoryBootstrap.GetRepositoryInfo(
            RepositoryBootstrap.GetFundamentalRepository(),
        )

        nonlocals = CommonEnvironmentImports.CommonEnvironment.Nonlocals(
            remaining_repos=0,
        )

        # ----------------------------------------------------------------------
        def CreateRepoData(directory):
            customization_mod = _GetCustomizationMod(directory)
            if customization_mod is None:
                return None

            return _RepoData.Create(customization_mod)

        # ----------------------------------------------------------------------
        def AddRepo(name, id, directory, repo_data):
            if id not in self:
                value = cls.Value(name, id, directory)

                value.root = directory
                value.configurations = list(six.iterkeys(repo_data.Configurations))

                self[id] = value

            value = self[id]

            for config_name, config_info in six.iteritems(repo_data.Configurations):
                config_dependencies = config_info.Dependencies

                if not config_dependencies and id != fundamental_repo_id:
                    config_dependencies.append(
                        Dependency(
                            fundamental_repo_id,
                            fundamental_repo_name,
                            Constants.DEFAULT_FUNDAMENTAL_CONFIGURATION,
                        ),
                    )

                these_dependencies = []

                for dependency_info in config_dependencies:
                    these_dependencies.append(
                        (dependency_info.RepositoryId, dependency_info.Configuration),
                    )

                    if dependency_info.RepositoryId not in self:
                        if dependency_info.RepositoryId in repo_cache:
                            enum_result = repo_cache[dependency_info.RepositoryId]
                            del repo_cache[dependency_info.RepositoryId]

                            AddRepo(
                                enum_result.Name,
                                enum_result.Id,
                                enum_result.Root,
                                CreateRepoData(enum_result.Root),
                            )
                        else:
                            self[dependency_info.RepositoryId] = cls.Value(
                                dependency_info.FriendlyName,
                                dependency_info.RepositoryId,
                                directory,
                            )
                            nonlocals.remaining_repos += 1

                    that_value = self[dependency_info.RepositoryId]

                    that_value.dependents.setdefault(
                        dependency_info.Configuration,
                        [],
                    ).append((id, config_name))

                    if that_value.get_clone_uri_func is None:
                        func = dependency_info.GetCloneUri
                        if isinstance(func, six.string_types):
                            original_value = func
                            func = (
                                lambda *args, original_value=original_value, **kwargs: original_value
                            )

                        that_value.get_clone_uri_func = func

                value.dependencies[config_name] = these_dependencies

        # ----------------------------------------------------------------------

        root_repo_name, root_repo_id = RepositoryBootstrap.GetRepositoryInfo(
            repository_root,
        )

        AddRepo(root_repo_name, root_repo_id, repository_root, repo_data)

        if nonlocals.remaining_repos:
            if on_search_begin_func:
                on_search_begin_func(self)
            else:
                output_stream.write("\nSearching for repositories...")

            output_stream.flush()

            warnings = []

            with output_stream.DoneManager(
                suffix="\n\n",
            ) as dm:
                search_dirs = [repository_root]

                if additional_search_dirs:
                    search_dirs += additional_search_dirs

                for search_dir in search_dirs:
                    for enum_result in cls._Enumerate(
                        search_dir,
                        CommonEnvironmentImports.StreamDecorator(
                            dm.stream if verbose else None,
                        ),
                        search_depth=search_depth,
                        max_num_searches=max_num_searches,
                        required_ancestor_dirs=required_ancestor_dirs,
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

                        enum_repo_data = CreateRepoData(enum_result.Root)

                        if value.Name != enum_result.Name:
                            warnings.append((enum_result.Name, value.Name, value.Source))

                        value.Name = enum_result.Name

                        value.root = enum_result.Root
                        value.configurations = list(
                            six.iterkeys(enum_repo_data.Configurations),
                        )

                        if recurse:
                            AddRepo(
                                enum_result.Name,
                                enum_result.Id,
                                enum_result.Root,
                                enum_repo_data,
                            )

                        assert nonlocals.remaining_repos
                        nonlocals.remaining_repos -= 1

                        if nonlocals.remaining_repos == 0:
                            break

            if warnings:
                output_stream.write(
                    textwrap.dedent(
                        """\
                        WARNING: The following dependency names didn't match the actual name used within the repository.

                            {}

                        """,
                    ).format(
                        CommonEnvironmentImports.StringHelpers.LeftJustify(
                            "\n".join(
                                [
                                    textwrap.dedent(
                                        # <Wrong hanging indentation> pylint: disable = C0330
                                        """\
                                        Actual Name:        {}
                                        Dependency Name:    {}
                                        Dependency Source:  {}
                                        """,
                                    ).format(
                                        actual_name,
                                        dependency_name,
                                        dependency_source,
                                    ) for actual_name,
                                    dependency_name,
                                    dependency_source in warnings
                                ],
                            ),
                            4,
                        ),
                    ),
                )

        # The map now has every possible dependency, regardless of what configurations were specified.
        # Walk the actual roots and configurations and mark every repo that is used.
        visited = {}

        # ----------------------------------------------------------------------
        def Traverse(value, config_name):
            visited.setdefault(value.Id, set()).add(config_name)

            if value.root and config_name not in value.configurations:
                raise Exception(
                    "The configuration '{}' specified by '{}' is not valid for '{} <{}>' in '{}'".format(
                        config_name,
                        value.Source,
                        value.Name,
                        value.Id,
                        value.root,
                    ),
                )

            if config_name in value.dependencies:
                for child_id, child_configuration in value.dependencies[config_name]:
                    assert child_id in self, child_id
                    child_value = self[child_id]

                    Traverse(child_value, child_configuration)

        # ----------------------------------------------------------------------

        roots = [value for value in six.itervalues(self) if not value.dependents]

        for value in roots:
            if value.root != repository_root:
                continue

            for config_name in value.configurations:
                if (
                    supported_configurations
                    and config_name not in supported_configurations
                ):
                    continue

                Traverse(value, config_name)

        # Now that each repo and configuration has been marked, remove those
        # that are never used.

        # ----------------------------------------------------------------------
        def RemoveConfiguration(value, config_name):
            assert config_name in value.dependencies
            for dependency_id, dependency_config in value.dependencies[config_name]:
                assert dependency_id in self, dependency_id
                dependency_value = self[dependency_id]

                assert dependency_config in dependency_value.dependents, dependency_config
                for dependent_index, (dependent_id, dependent_config) in enumerate(
                    dependency_value.dependents[dependency_config],
                ):
                    if dependent_id == value.Id and dependent_config == config_name:
                        del dependency_value.dependents[dependency_config][
                            dependent_index
                        ]
                        break

                if not dependency_value.dependents[dependency_config]:
                    RemoveConfiguration(dependency_value, dependency_config)

            del value.dependencies[config_name]
            value.configurations.remove(config_name)

            if not value.configurations:
                del self[value.Id]

        # ----------------------------------------------------------------------

        # Remove values that were not visited
        for id in list(six.iterkeys(self)):
            if id not in visited:
                # Don't remove values for repos that weren't found
                if self[id].root is not None:
                    del self[id]

                continue

            if not supported_configurations:
                continue

            value = self[id]

            if value.root is None:
                continue

            if value.root == repository_root:
                continue

            config_index = 0
            while config_index < len(value.configurations):
                config_name = value.configurations[config_index]

                delete_config = False

                if config_name in value.dependents:
                    dependent_index = 0
                    while dependent_index < len(value.dependents[config_name]):
                        dependent_id, dependent_configuration = value.dependents[
                            config_name
                        ][dependent_index]

                        if (
                            dependent_id not in visited
                            or dependent_configuration not in visited[dependent_id]
                        ):
                            del value.dependents[config_name][dependent_index]
                        else:
                            dependent_index += 1

                    if not value.dependents[config_name]:
                        delete_config = True

                if config_name not in visited[id]:
                    delete_config = True

                if delete_config:
                    del value.configurations[config_index]

                    value.dependencies.pop(config_name, None)
                    value.dependents.pop(config_name, None)
                else:
                    config_index += 1

            if not value.configurations:
                del self[id]

        return self

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    _EnumerateResult                        = namedtuple("_EnumerateResult", ["Name", "Id", "Root"])

    # ----------------------------------------------------------------------
    @classmethod
    def _Enumerate(
        cls,
        repository_root,
        verbose_stream,
        search_depth=None,
        max_num_searches=None,
        required_ancestor_dirs=None,
    ):
        search_depth = search_depth or _DEFAULT_SEARCH_DEPTH

        assert not required_ancestor_dirs or any(
            repository_root.startswith(required_ancestor_dir)
            for required_ancestor_dir in required_ancestor_dirs
        ), (required_ancestor_dirs, repository_root)

        # Augment the search depth to account for the provided root
        search_depth += repository_root.count(os.path.sep)
        if CommonEnvironmentImports.CurrentShell.CategoryName == "Windows":
            # Don't count the slash associated with the drive name
            assert search_depth

            # ----------------------------------------------------------------------
            def ItemPreprocessor(item):
                drive, suffix = os.path.splitdrive(item)
                if drive[-1] == ":":
                    drive = drive[:-1]

                return "{}:{}".format(drive.upper(), suffix)

            # ----------------------------------------------------------------------

        else:
            # ----------------------------------------------------------------------
            def ItemPreprocessor(item):
                return item

            # ----------------------------------------------------------------------

        if required_ancestor_dirs:
            required_ancestor_dirs = [
                ItemPreprocessor(
                    CommonEnvironmentImports.FileSystem.RemoveTrailingSep(
                        required_ancestor_dir,
                    ),
                )
                for required_ancestor_dir in required_ancestor_dirs
            ]

            # ----------------------------------------------------------------------
            def IsValidAncestor(fullpath):
                return any(
                    fullpath.startswith(required_ancestor_dir)
                    for required_ancestor_dir in required_ancestor_dirs
                )

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
                    if (
                        index == len_repository_root_dirname
                        or c != repository_root_dirname[index]
                    ):
                        break

                return index

            # ----------------------------------------------------------------------
            def PushSearchItem(fullpath):
                fullpath = os.path.realpath(os.path.normpath(fullpath))

                parts = fullpath.split(os.path.sep)
                if len(parts) > search_depth:
                    return

                parts_lower = set([part.lower() for part in parts])

                priority = 1
                for bump_name in CODE_DIRECTORY_NAMES:
                    if bump_name in parts_lower:
                        priority = 0
                        break

                # Every item except the last is used for sorting
                search_items.append(
                    (
                        -FirstNonmatchingChar(fullpath),                    # Favor ancestors over other locations
                        priority,                                           # Favor names that look like source locations
                        len(parts),                                         # Favor locations near the root
                        fullpath.lower(),                                   # Case insensitive sort
                        fullpath,
                    ),
                )
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
                    if os.path.exists(
                        os.path.join(
                            search_item,
                            Constants.IGNORE_DIRECTORY_AS_BOOTSTRAP_DEPENDENCY_SENTINEL_FILENAME,
                        ),
                    ):
                        continue

                    yield search_item

                    ctr += 1
                    if max_num_searches and ctr == max_num_searches:
                        break

                    # Add the parent to the queue
                    try:
                        potential_parent = os.path.dirname(search_item)
                        if potential_parent != search_item:
                            if IsValidAncestor(potential_parent) and (
                                not skip_root
                                or os.path.dirname(potential_parent) != potential_parent
                            ):
                                PushSearchItem(ItemPreprocessor(potential_parent))

                    except (PermissionError, FileNotFoundError, OSError):
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

                    except (PermissionError, FileNotFoundError, OSError):
                        pass

            # ----------------------------------------------------------------------

            PushSearchItem(ItemPreprocessor(repository_root))

            if CommonEnvironmentImports.CurrentShell.CategoryName == "Windows":
                for result in Impl(True):
                    yield result

                if not required_ancestor_dirs:
                    # If here, look at other drive locations
                    import win32api
                    import win32file

                    # <Module 'win32api' has not 'GetLogicalDriveStrings' member, but source is unavailable. Consider adding this module to extension-pkg-whitelist if you want to perform analysis based on run-time introspection of living objects.> pylint: disable = I1101

                    for drive in [
                        drive
                        for drive in win32api.GetLogicalDriveStrings().split("\000")
                        if drive
                        and win32file.GetDriveType(drive) == win32file.DRIVE_FIXED
                    ]:
                        PushSearchItem(drive)

                    for result in Impl(False):
                        yield result

            else:
                for result in Impl(False):
                    yield result

        # ----------------------------------------------------------------------

        for directory in Enumerate():
            verbose_stream.write("Searching in '{}'\n".format(directory))

            result = RepositoryBootstrap.GetRepositoryInfo(
                directory,
                raise_on_error=False,
            )
            if result is None:
                continue

            repo_name, repo_id = result

            yield cls._EnumerateResult(repo_name, repo_id, directory)

        verbose_stream.write("\n")


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GetCustomizationMod(repository_root):
    potential_customization_filename = os.path.join(
        repository_root,
        Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME,
    )
    if os.path.isfile(potential_customization_filename):
        sys.path.insert(0, repository_root)
        with CommonEnvironmentImports.CallOnExit(lambda: sys.path.pop(0)):
            module_name = os.path.splitext(
                Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME,
            )[0]

            module = importlib.import_module(module_name)
            del sys.modules[module_name]

            return module

    return None


# ----------------------------------------------------------------------
def _CreateRepoMap(
    repository_root,
    supported_configurations,
    recurse,
    output_stream,
    verbose,
    search_depth=None,
    max_num_searches=None,
    required_ancestor_dirs=None,
    additional_repo_search_dirs=None,
):
    customization_mod = _GetCustomizationMod(repository_root)
    if customization_mod is None:
        output_stream.write(
            "ERROR: '{}' is not a valid repository root.\n".format(repository_root),
        )
        return -1

    return _RepositoriesMap.Create(
        repository_root,
        _RepoData.Create(
            customization_mod,
            supported_configurations=supported_configurations,
        ),
        recurse,
        output_stream,
        verbose,
        supported_configurations=supported_configurations,
        search_depth=search_depth,
        max_num_searches=max_num_searches,
        required_ancestor_dirs=required_ancestor_dirs,
        additional_search_dirs=additional_repo_search_dirs,
    )

# ----------------------------------------------------------------------
def _SimpleFuncImpl(
    callback,                               # def Func(output_stream, repo_map) -> result code
    repository_root,
    recurse,
    scm,
    explicit_configurations,
    output_stream,
    verbose,
    search_depth=None,
    max_num_searches=None,
    required_ancestor_dirs=None,
    use_ascii=False,
    additional_repo_search_dirs=None,
):
    """Scaffolding the creates a repo map, displays it, and invokes the provided callback within a command line context"""

    with CommonEnvironmentImports.StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        # Create the repo map
        repo_map = _CreateRepoMap(
            repository_root,
            explicit_configurations,
            recurse,
            dm.stream,
            verbose,
            search_depth=search_depth,
            max_num_searches=max_num_searches,
            required_ancestor_dirs=required_ancestor_dirs,
            additional_repo_search_dirs=additional_repo_search_dirs,
        )
        if isinstance(repo_map, int):
            return repo_map

        # Display the repo map as a tree

        # ----------------------------------------------------------------------
        DisplayInfo = namedtuple(
            "DisplayInfo",
            [
                "Id",
                "Configuration",
                "Root",
                "GetCloneUri",
            ],
        )

        # ----------------------------------------------------------------------
        def Traverse(value, configuration):
            result_tree = OrderedDict()
            result_display_infos = []

            display_infos.append(
                DisplayInfo(value.Id, configuration, value.root, value.get_clone_uri_func),
            )

            if configuration in value.dependencies:
                for child_id, child_configuration in value.dependencies[configuration]:
                    assert child_id in repo_map, child_id
                    child_value = repo_map[child_id]

                    child_tree, child_display_infos = Traverse(
                        child_value,
                        child_configuration,
                    )

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
                tree = OrderedDict([("", tree)])
            else:
                added_line = False

            from asciitree import LeftAligned
            from asciitree.drawing import BoxStyle, BOX_LIGHT, BOX_ASCII

            create_tree_func = LeftAligned(
                draw=BoxStyle(
                    gfx=BOX_ASCII if use_ascii else BOX_LIGHT,
                    horiz_len=1,
                ),
            )

            lines = create_tree_func(tree).split("\n")

            if added_line:
                lines = lines[1:]

            resolved_display_infos = []
            max_configuration_name_length = 0
            max_location_length = 0
            max_uri_length = 0

            for display_info in display_infos:
                configuration = display_info.Configuration or "<default>"
                max_configuration_name_length = max(
                    max_configuration_name_length,
                    len(configuration),
                )

                location = display_info.Root or "N/A"
                max_location_length = max(max_location_length, len(location))

                uri = (
                    display_info.GetCloneUri(scm) if display_info.GetCloneUri else None
                ) or "N/A"
                max_uri_length = max(max_uri_length, len(uri))

                resolved_display_infos.append(
                    [
                        configuration,
                        display_info.Id,
                        location,
                        uri,
                    ],
                )

            # ----------------------------------------------------------------------
            def TrimValues(header, max_length, item_index):
                """Space is tight, so attempt to extract a common prefix from all of the values; returns the header value."""

                values = [
                    resolved_display_info[item_index]
                    for resolved_display_info in resolved_display_infos
                    if resolved_display_info[item_index] != "N/A"
                ]

                common_prefix = os.path.commonprefix(values)
                if not common_prefix:
                    return header, max_length

                if common_prefix[-1] in ["\\", "/"]:
                    common_prefix = common_prefix[:-1]

                header = "{} ({}...)".format(header, common_prefix)

                # Replace values
                common_prefix_len = len(common_prefix)

                for rdi_index, resolved_display_info in enumerate(resolved_display_infos):
                    if resolved_display_info[item_index] == "N/A":
                        continue

                    resolved_display_infos[rdi_index][item_index] = "...{}".format(
                        resolved_display_info[item_index][common_prefix_len:],
                    )

                return header, max_length - len(common_prefix) + 3

            # ----------------------------------------------------------------------

            location_header, max_location_length = TrimValues(
                "Location",
                max_location_length,
                2,
            )
            uri_header, max_uri_length = TrimValues("Clone Uri", max_uri_length, 3)

            # Space is tight here, so minimize the display width
            display_cols = [
                max(
                    len("Repository"),
                    len(
                        max(
                            lines,
                            key=len,
                        ),
                    ),
                ),
                max(len("Configuration"), max_configuration_name_length),
                max(len("Id"), 32),
                max(len(location_header), max_location_length),
                max(len(uri_header), max_uri_length),
            ]

            display_template = "{{0:<{0}}}  {{1:<{1}}}  {{2:<{2}}}  {{3:<{3}}}  {{4}}".format(
                *display_cols
            )

            dm.stream.write(
                textwrap.dedent(
                    """\
                    {}
                    {}
                    {}
                    """,
                ).format(
                    display_template.format(
                        "Repository",
                        "Configuration",
                        "Id",
                        location_header,
                        uri_header,
                    ),
                    display_template.format(
                        *["-" * col_size for col_size in display_cols]
                    ),
                    "\n".join(
                        [
                            display_template.format(line, *resolved_display_info)
                            for line,
                            resolved_display_info in zip(
                                lines,
                                resolved_display_infos,
                            )
                        ]
                    ),
                )
            )

        # ----------------------------------------------------------------------
        def CreateTreeKey(name, index):
            # Tree keys must be unique. Therefore, append whitespace based on the index
            # to ensure that we create unique values.
            return "{}{}".format(name, " " * index)

        # ----------------------------------------------------------------------

        # Display all the items that are used
        roots = [value for value in six.itervalues(repo_map) if not value.dependents]

        display_tree = OrderedDict()
        display_infos = []

        for root in roots:
            for index, config_name in enumerate(six.iterkeys(root.dependencies)):
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
                    display_infos.append(
                        DisplayInfo(
                            value.Id,
                            config_name,
                            value.root,
                            value.get_clone_uri_func,
                        ),
                    )

        if display_tree:
            output_stream.write(
                textwrap.dedent(
                    """\



                    Unused Configurations
                    =====================

                    """,
                ),
            )

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
    return None


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommonEnvironmentImports.CommandLine.Main())
    except KeyboardInterrupt:
        pass
