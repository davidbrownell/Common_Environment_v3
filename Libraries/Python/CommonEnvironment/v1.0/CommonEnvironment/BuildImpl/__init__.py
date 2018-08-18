# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-21 07:44:58
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""
Provides functionality for files that implement on consume builder functionality.
A builder is a file that is capable of building or cleaning one or more artifacts,
where the mechanics associated with the implementation of that functionality is 
opaque to the user. When using build files, the means of invoking a build are the
same regardless of what the build is actually doing.
"""

import inspect
import os
import re
import sys
import textwrap

import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment import RegularExpression
from CommonEnvironment.Shell.All import CurrentShell

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from RepositoryBootstrap import Constants as RepositoryBootstrapConstants
    
# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Configuration(object):
    """Metadata about an individual build"""

    # ----------------------------------------------------------------------
    # |  Public Types

    # This is just an arbitrary number, chosen so that builds can be given 
    # lower- and higher priority than this default value.
    DEFAULT_PRIORITY                        = 10000

    # ----------------------------------------------------------------------
    # |  Public Methods
    def __init__( self,
                  name,
                  priority=DEFAULT_PRIORITY,
                  suggested_output_dir_location='',                         # A default suffix added to user-supplied output directories
                  requires_output_dir=True,                                 # If True, the user must support an output directory
                  configurations=None,                                      # Different configurations that the build can be invoked with (e.g. "Debug", "Release", etc.)
                  required_development_environment=None,                    # The Name or CategoryName of an environment that must be active for the build to be invoked
                  required_development_configurations=None,                 # Configuration names for an environment that must be active for the build to be invoked
                  disable_if_dependency_environment=False,                  # If True, disable the build if it is part of an environment that has been activated as a dependency environment; when True, the build will only be active when its associated repository was activated directly.
                  configuration_required_on_clean=True,                     # If True, a configuration must be provided when Cleaning. If False, the entire ouptut directory is deleted (even if it contains the output from building with different configurations)
                ):
        self.Name                                       = name
        self.Priority                                   = priority
        self.RequiresOutputDir                          = requires_output_dir
        self.Configurations                             = configurations or []
        self.ConfigurationRequiredOnClean               = configuration_required_on_clean
        self.RequiredDevelopmentEnvironment             = required_development_environment
        self.RequiredDevelopmentConfigurations          = required_development_configurations or []
        self.DisableIfDependencyEnvironment             = disable_if_dependency_environment
        self.SuggestedOutputDirLocation                 = suggested_output_dir_location

# ----------------------------------------------------------------------
class CompleteConfiguration(Configuration):
    """
    Configuration objects are optimized to be easy to use when creating a build file.
    CompleteConfiguration objects are optimized to be easy to use when consuming
    information about a build file.
    """

    # ----------------------------------------------------------------------
    @classmethod
    def FromBuildFile( cls,
                       build_filename,
                       strip_path=None,
                     ):
        assert os.path.isfile(build_filename), build_filename

        # Extract metadata auto-generated from the build file to create the 
        # configuration. Note that some portions of the metadata will be based
        # on the current dir, so switch to the root dir before extracting the
        # information to ensure that things work as expected.
        if strip_path:
            assert os.path.isdir(strip_path), strip_path

            current_dir = os.getcwd()
            os.chdir(strip_path)

            # ----------------------------------------------------------------------
            def Cleanup():
                os.chdir(current_dir)

            # ----------------------------------------------------------------------
        else:
            # ----------------------------------------------------------------------
            def Cleanup():
                pass

            # ----------------------------------------------------------------------

        with CallOnExit(Cleanup):
            result, output = Process.Execute('python "{}" Metadata'.format(build_filename))
            assert result == 0, (result, output)

            match = RegularExpression.TemplateStringToRegex( cls._VIEW_METADATA_TEMPLATE, 
                                                             optional_tags=[ "suggested_output_dir_location", 
                                                                           ],
                                                           ).match(output)
            if not match:
                raise Exception("'{}' did not produce valid metadata results".format(build_filename))
            
            # ----------------------------------------------------------------------
            def FromList(value):
                value = match.group(value)
                return [] if value == "None" else [ item.strip() for item in value.split(',') if item.strip() ]

            # ----------------------------------------------------------------------
            def FromOptional(value):
                value = match.group(value)
                return None if value == "None" else value

            # ----------------------------------------------------------------------
            def FromBool(value):
                value = match.group(value)
                return value == "True"

            # ----------------------------------------------------------------------

            return cls( exposed_functions=FromList("commands"),
                        config=Configuration( name=match.group("name"),
                                              priority=int(match.group("priority")),
                                              suggested_output_dir_location=match.group("suggested_output_dir_location"),
                                              requires_output_dir=FromBool("requires_output_dir"),
                                              configurations=FromList("configurations"),
                                              required_development_environment=FromOptional("required_dev_environment"),
                                              required_development_configurations=FromList("required_dev_configurations"),
                                              disable_if_dependency_environment=FromBool("disable_if_dependency"),
                                            ),
                      )

    # ----------------------------------------------------------------------
    # <__init__ method from base class 'Configuration' is not called> pylint: disable = W0231
    def __init__(self, exposed_functions, config):
        self.__dict__                       = config.__dict__
        self.ExposedFunctions               = list(exposed_functions)

    # ----------------------------------------------------------------------
    def GetCustomCommands(self):
        return [ command for command in self.ExposedFunctions if command not in [ "Build",
                                                                                  "Clean",
                                                                                  "Rebuild",
                                                                                  "Metadata",
                                                                                ] ]

    # ----------------------------------------------------------------------
    def __str__(self):
        custom_commands = self.GetCustomCommands()

        return self._VIEW_METADATA_TEMPLATE.format( name=self.Name,
                                                    priority=self.Priority,
                                                    requires_output_dir="True" if self.RequiresOutputDir else "False",
                                                    suggested_output_dir_location=self.SuggestedOutputDirLocation,
                                                    configurations=', '.join(self.Configurations) if self.Configurations else "None",
                                                    commands=', '.join(self.ExposedFunctions),
                                                    custom_commands=', '.join(custom_commands) if custom_commands else "None",
                                                    required_dev_environment=self.RequiredDevelopmentEnvironment or "None",
                                                    required_dev_configurations=', '.join(self.RequiredDevelopmentConfigurations) if self.RequiredDevelopmentConfigurations else "None",
                                                    disable_if_dependency="True" if self.DisableIfDependencyEnvironment else "False",
                                                    configuration_required_on_clean="None" if not self.Configurations else "True" if self.ConfigurationRequiredOnClean else "False",
                                                  ) 

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    _VIEW_METADATA_TEMPLATE                             = textwrap.dedent(
        # <Wrong hanging indentation> pylint: disable = C0330
       r"""
        Name:                                                   {name}
        Priority:                                               {priority}

        Requires Output Dir:                                    {requires_output_dir}
        Suggested Output Dir Location:                          {suggested_output_dir_location}
        
        Available Configurations:                               {configurations}
        Available Commands:                                     {commands}
        Custom Commands:                                        {custom_commands}

        Required Development Environment:                       {required_dev_environment}
        Required Development Environment Configurations:        {required_dev_configurations}
        Disable If Dependency Environment:                      {disable_if_dependency}
        Configuration Required On Clean:                        {configuration_required_on_clean}
        """).lstrip()

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def Main( config,
          original_args=sys.argv,                       # <Dangerous default value> pylint: disable = W0102
          command_line_arg_prefix='/',
          command_line_keyword_separator='=',
          command_line_dict_tag_value_separator=':',
          verbose=False,
          output_stream=sys.stdout,
        ):
    """Method called in a build file's entry point"""

    assert config
    assert original_args
    assert command_line_arg_prefix
    assert command_line_keyword_separator
    assert command_line_dict_tag_value_separator
    assert output_stream

    # Some build file functions are required, others are not
    required = { "build" : lambda ep: _RedirectEntryPoint("Build", ep, config),
                 "clean" : lambda ep: _RedirectEntryPoint("Clean", ep, config),
               }

    required_names = set(required.keys())

    entry_points = CommandLine.EntryPointInformation.FromModule(sys.modules["__main__"])
    for entry_point in entry_points:
        entry_point_name_lower = entry_point.Name.lower()

        if entry_point_name_lower in required_names:
            required[entry_point_name_lower](entry_point)
            required[entry_point_name_lower] = entry_point

            required_names.remove(entry_point_name_lower)

        else:
            for reserved_name in [ "Rebuild",
                                   "Metadata",
                                 ]:
                if entry_point_name_lower == reserved_name.lower():
                    raise Exception("The name '{}' is reserved and will be automatically generated".format(reserved_name))

    if required_names:
        raise Exception("These methods must be defined: {}".format(', '.join(required_names)))

    entry_points.append(CommandLine.EntryPointInformation.FromFunction(_GenerateRebuild( required["build"],
                                                                                         required["clean"],
                                                                                         config,
                                                                                       )))

    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    def Metadata():
        """Metadata associated with the build"""
        sys.stdout.write(str(config))

    # ----------------------------------------------------------------------

    entry_points.append(CommandLine.EntryPointInformation.FromFunction(Metadata))

    config = CompleteConfiguration( [ entry_point.Name for entry_point in entry_points ],
                                    config,
                                  )

    script_description_suffix = None
    if config.Configurations:
        script_description_suffix = "    Where <configuration> can be:\n\n{}\n".format('\n'.join([ "        - {}".format(cfg) for cfg in config.Configurations ]))

    # Execute
    stack_frame = inspect.stack()[-1]
    
    current_dir = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(stack_frame[1])))

    with CallOnExit(lambda: os.chdir(current_dir)):
        # Ensure that an output directory is created prior to invoking build functionality
        if config.RequiresOutputDir and len(original_args) >= 2 and original_args[1].lower() in [ "build", "rebuild", ]:
            output_dir = None

            if config.Configurations:
                # Command line is: <script> build <config> <output_dir> ...
                if len(original_args) >= 4:
                    output_dir = original_args[3]
            else:
                # Command line is: <script build <output_dir>
                if len(original_args) >= 3:
                    output_dir = original_args[2]

            if output_dir:
                FileSystem.MakeDirs(output_dir)

        return CommandLine.Executor( args=original_args,
                                     command_line_arg_prefix=command_line_arg_prefix,
                                     command_line_keyword_separator=command_line_keyword_separator,
                                     command_line_dict_tag_value_separator=command_line_dict_tag_value_separator,
                                     script_description=inspect.getmodule(stack_frame[0]).__doc__ or '',
                                     script_description_suffix=script_description_suffix,
                                     entry_points=entry_points,
                                   ).Invoke( verbose=verbose,
                                             output_stream=output_stream,
                                           )

# ----------------------------------------------------------------------
# |  
# |  Private Methods
# |  
# ----------------------------------------------------------------------
def _RedirectEntryPoint_IsSupportedDevelopmentConfiguration(configurations):
    dev_configuration = os.getenv(RepositoryBootstrapConstants.DE_REPO_CONFIGURATION_NAME)
    return any(re.match(config, dev_configuration) for config in configurations)

# ----------------------------------------------------------------------
def _RedirectEntryPoint(function_name, entry_point, config):
    assert function_name
    assert entry_point
    assert config

    # <Use of exec> pylint: disable = W0122
    # <Use of eval> pylint: disable = W0123

    required_arguments = []

    if config.Configurations:
        if function_name != "Clean" or config.ConfigurationRequiredOnClean:
            assert "configuration" in entry_point.ConstraintsDecorator.Preconditions, function_name
            entry_point.ConstraintsDecorator.Preconditions["configuration"] = CommandLine.EnumTypeInfo(config.Configurations)

            required_arguments.append("configuration")

    if config.RequiresOutputDir:
        required_arguments.append("output_dir")

    num_required_args = six.get_function_code(entry_point.Function).co_argcount - len(list(six.get_function_defaults(entry_point.Function) or []))
    arguments = six.get_function_code(entry_point.Function).co_varnames[:num_required_args]

    if required_arguments and list(arguments[:len(required_arguments) + 1]) != required_arguments:
        raise Exception("The entry point '{}' should begin with the arguments '{}' ('{}' were found)".format( function_name,
                                                                                                              ', '.join(required_arguments),
                                                                                                              ', '.join(arguments),
                                                                                                            ))

    # Dynamically redefine the function so that it prints information that lets the user know the the
    # functionality can't be executed on the current platform/configuration/environment.
    if config.RequiredDevelopmentEnvironment and config.RequiredDevelopmentEnvironment.lower() not in [ CurrentShell.Name.lower(),              # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
                                                                                                        CurrentShell.CategoryName.lower(),      # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
                                                                                                      ]:
        exec(textwrap.dedent(
            """\
            def {name}({args}):
                sys.stdout.write("\\nINFO: This can only be run on '{env}'.\\n")
                return 0
            """).format( name=function_name,
                         args=', '.join(arguments),
                         env=config.RequiredDevelopmentEnvironment,
                       ))

        entry_point.Function = eval(function_name)

    elif config.RequiredDevelopmentConfigurations and not _RedirectEntryPoint_IsSupportedDevelopmentConfiguration(config.RequiredDevelopmentConfigurations):
        exec(textwrap.dedent(
            """\
            def {name}({args}):
                sys.stdout.write("\\nINFO: This can only be run in development environments activated with the configurations {configs}.\\n")
                return 0
            """).format( name=function_name,
                         args=', '.join(arguments),
                         configs=', '.join([ "'{}'".format(configuration) for configuration in config.RequiredDevelopmentConfigurations ]),
                       ))

        entry_point.Function = eval(function_name)

    elif config.DisableIfDependencyEnvironment:
        repo_path = os.getenv(RepositoryBootstrapConstants.DE_REPO_ROOT_NAME)

        if FileSystem.GetCommonPath(repo_path, inspect.getfile(entry_point.Function)).rstrip(os.path.sep) != repo_path:
            exec(textwrap.dedent(
                """\
                def {name}({args}):
                    sys.stdout.write("\\nINFO: This module is not build when invoked as a dependency.\\n")
                    return 0
                """).format( name=function_name,
                             args=', '.join(arguments),
                           ))

            entry_point.Function = eval(function_name)

# ----------------------------------------------------------------------
def _GenerateRebuild(build_func, clean_func, config):
    assert build_func
    assert clean_func
    assert config

    # ----------------------------------------------------------------------
    def Impl(configuration, output_dir, build_func, clean_func):
        result = clean_func(configuration, output_dir)
        if result is not None and result != 0:
            return result

        if config.RequiresOutputDir and not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        result = build_func(configuration, output_dir)
        if result is not None and result != 0:
            return result

        return 0

    # ----------------------------------------------------------------------

    if config.Configurations:
        if config.RequiresOutputDir:
            # ----------------------------------------------------------------------
            @CommandLine.EntryPoint
            @CommandLine.Constraints( configuration=CommandLine.EnumTypeInfo(config.Configurations),
                                      output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                    )
            def Rebuild(configuration, output_dir):
                """Invokes Clean and Build functionality"""
                return Impl(configuration, output_dir, build_func, clean_func)

            # ----------------------------------------------------------------------
        else:
            # ----------------------------------------------------------------------
            @CommandLine.EntryPoint
            @CommandLine.Constraints( configuration=CommandLine.EnumTypeInfo(config.Configurations),
                                    )
            def Rebuild(configuration):
                """Invokes Clean and Build functionality"""
                return Impl( configuration,
                             None,
                             lambda cfg, output_dir: build_func(cfg),
                             lambda cfg, output_dir: clean_func(cfg),
                           )

            # ----------------------------------------------------------------------

    else:
        if config.RequiresOutputDir:
            # ----------------------------------------------------------------------
            @CommandLine.EntryPoint
            @CommandLine.Constraints( output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                                    )
            def Rebuild(output_dir):
                """Invokes Clean and Build functionality"""
                return Impl( None,
                             output_dir,
                             lambda cfg, output_dir: build_func(output_dir),
                             lambda cfg, output_dir: clean_func(output_dir),
                           )

            # ----------------------------------------------------------------------
        else:
            # ----------------------------------------------------------------------
            @CommandLine.EntryPoint
            def Rebuild():
                """Invokes Clean and Build functionality"""
                return Impl( None,
                             None,
                             lambda cfg, output_dir: build_func(),
                             lambda cfg, output_dir: clean_func(),
                           )

            # ----------------------------------------------------------------------

    return Rebuild
