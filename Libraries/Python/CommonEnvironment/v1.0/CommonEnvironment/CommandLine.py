# ----------------------------------------------------------------------
# |  
# |  CommandLine.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-24 16:14:37
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Tools and utilities that automatically create command line parsers."""

import inspect
import os
import re
import sys
import textwrap
import types

from collections import OrderedDict

import six
import wrapt

import CommonEnvironment
from CommonEnvironment.Constraints import Constraints
from CommonEnvironment import StringHelpers

from CommonEnvironment.TypeInfo import ValidationException
from CommonEnvironment.TypeInfo.All import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------

# When this arg is provided, the tool will output debugging diagnostics
# rather than processing the command.
DEBUG_COMMAND_LINE_ARG                      = "_debug_command_line"

MAX_COLUMN_WIDTH                            = 100

# The following methods can be optionally defined by the calling file
# to customize output characteristics.
CUSTOMIZATION_METHODS                       = [
    # Overrides the displayed script name; the calling file's name
    # will be used if not provided.
    "CommandLineScriptName",                # def Func() -> string

    # Overrides the script description; the calling file's docstring
    # will be used if not provided.
    "CommandLineScritpDescription",         # def Func() -> string

    # Content displayed after the description but before usage
    # information; no prefix will be displayed if not provided.
    "CommandLineDocPrefix",                 # def Func() -> string

    # Content displayed after usage information; no prefix will 
    # be displayed if not provided.
    "CommandLineDocSuffix",                 # def Func() -> string
]

class UsageException(Exception):
    """Exception whose contents will be displayed along with verbose help information."""
    pass

# ----------------------------------------------------------------------
@wrapt.decorator
class EntryPoint(object):
    """
    Decorates a method/function that should be made available on the 
    command line.

    @EntryPoint
    def ExternallyVisible():
        pass
    """

    # ----------------------------------------------------------------------
    # |  Public Types

    class Parameter(object):
        """Information about a parameter made available on the commend line."""
        def __init__( self,
                      description='',
                      postprocess_func=None,            # def Func(value) -> new_value
                      allow_duplicates=False,
                      ignore=False,
                    ):
            self.Description                = description
            self.PostprocessFunc            = postprocess_func or (lambda value: value)
            self.AllowDuplicates            = allow_duplicates
            self.Ignore                     = ignore

        # ----------------------------------------------------------------------
        def __str__(self):
            return CommonEnvironment.ObjectStrImpl(self)

    # ----------------------------------------------------------------------
    # |  Public Methods
    def __init__( self,
                  _name_override=None,      # Prefixed with an underscore so it doesn't conflect with function parameters
                  **parameters
                ):
        """
        Example:

            @EntryPoint( a=EntryPoint.Parameters("A description for 'a'"),
                         b=EntryPoint.Parameters("A description for 'b'"),
                       )
            def Func(a, b):
                pass
        """

        self.NameOverride                   = _name_override
        self.Parameters                     = parameters

    # ----------------------------------------------------------------------
    def __call__(self, wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class EntryPointInformation(object):
    """Information about an entry point calculated from the code."""

    # ----------------------------------------------------------------------
    # |  Public Types
    class ParameterInfo(object):
        class NoDefault(object): pass

        # ----------------------------------------------------------------------
        def __init__( self,
                      type_info,
                      name,
                      description,
                      display_arity,
                      postprocess_func,
                      allow_duplicates,
                      is_positional,
                      is_required,
                      is_switch,
                      default_value,
                   ):
            self.TypeInfo                   = type_info
            self.Name                       = name
            self.Description                = description
            self.DisplayArity               = display_arity
            self.PostprocessFunc            = postprocess_func
            self.AllowDuplicates            = allow_duplicates
            self.IsPositional               = is_positional
            self.IsRequired                 = is_required
            self.IsSwitch                   = is_switch
            self.DefaultValue               = default_value

            if self.DefaultValue is not self.NoDefault and self.TypeInfo.Arity.Min != 0:
                raise Exception("Parameters with default values should have an optional arity ({})".format(self.Name))

        # ----------------------------------------------------------------------
        def __str__(self):
            return CommonEnvironment.ObjectStrImpl(self)

    # ----------------------------------------------------------------------
    # |  Public Methods

    @classmethod
    def FromFunction(cls, function):
        """Constructs an object from a python function definition."""

        entry_point_decorator = None
        constraints_decorator = None

        # ----------------------------------------------------------------------
        def EnumDecorators(function):
            while function:
                if not hasattr(function, "_self_wrapper"):
                    break

                decorator = getattr(function._self_wrapper, "_im_self", function._self_wrapper)
                if decorator:
                    yield decorator

                function = getattr(function, "__wrapped__", None)

        # ----------------------------------------------------------------------

        for decorator in EnumDecorators(function):
            # isinstance doesn't place nice with these decorators, so use equality instead.
            if type(decorator) == EntryPoint:
                assert entry_point_decorator is None, function
                entry_point_decorator = decorator

            elif type(decorator) == Constraints:
                assert constraints_decorator is None, function
                constraints_decorator = decorator

        if entry_point_decorator is not None:
            arg_spec = cls._GetArgSpec(function)

            if (constraints_decorator is None or not constraints_decorator.Preconditions) and len(arg_spec.args) != len(arg_spec.defaults or []):
                raise Exception("'{}' must be associated with a Constraints decorator with preconditions".format(function.__name__))

            return cls( function,
                        entry_point_decorator,
                        constraints_decorator,
                      )

    # ----------------------------------------------------------------------
    @classmethod
    def FromModule(cls, mod):
        """Returns a list of all entry points in a module."""

        entry_points = []

        for item_name in dir(mod):
            item = getattr(mod, item_name)

            epi = cls.FromFunction(item)
            if epi is not None:
                entry_points.append(epi)

        # Sort by line number, as we want the functions displayed in the order in which
        # they were declared.
        entry_points.sort(key=lambda x: six.get_function_code(x.Function).co_firstlineno)

        return entry_points

    # ----------------------------------------------------------------------
    def __init__( self,
                  function,
                  entry_point_decorator,
                  constraints_decorator,
                ):
        self.Function                       = function
        self.EntryPointDecorator            = entry_point_decorator
        self.ConstraintsDecorator           = constraints_decorator
        self.Name                           = self.EntryPointDecorator.NameOverride or function.__name__
        self.Description                    = function.__doc__ or ''

        # Populate the parameters
        parameters = []

        arg_spec = self._GetArgSpec(function)
        
        args = arg_spec.args
        defaults = list(arg_spec.defaults or [])

        first_optional_arg_index = len(args) - len(defaults)

        # Remove any explicitly ignore parameters and verify that all items
        # are accounted for.
        entry_point_decorator_names = set(six.iterkeys(self.EntryPointDecorator.Parameters))
        new_args = []

        for index, arg in enumerate(args):
            if arg in entry_point_decorator_names:
                entry_point_decorator_names.remove(arg)

            if ( (self.ConstraintsDecorator and arg in self.ConstraintsDecorator.Preconditions and self.ConstraintsDecorator.Preconditions[arg] is None) or
                 (arg in self.EntryPointDecorator.Parameters and (entry_point_decorator.Parameters[arg] is None or entry_point_decorator.Parameters[arg].Ignore))
               ):
                if index < first_optional_arg_index:
                    raise Exception("'{}' in the function '{}' was explicitly ignored but does not have a default python value.".format(arg, self.Name))

                # This arg will not be included in the list of args; remove the default value.
                defaults.remove(defaults[index - first_optional_arg_index])

            else:
                new_args.append(arg)

        if entry_point_decorator_names:
            raise Exception("Parameter information was provided for parameters in the function '{}' that do not match existing definition ({}).".format( self.Name,
                                                                                                                                                         ', '.join(entry_point_decorator_names),
                                                                                                                                                       ))

        args = new_args
        first_optional_arg_index = len(args) - len(defaults)

        # Populate all parameter information
        is_positional = True

        all_types_tuple = tuple(ALL_FUNDAMENTAL_TYPES) + ( DictTypeInfo, AnyOfTypeInfo )

        for index, name in enumerate(args):
            if self.ConstraintsDecorator is None or (name not in self.ConstraintsDecorator.Preconditions and index >= first_optional_arg_index):
                type_info = CreateFromPythonType(type(defaults[index - first_optional_arg_index]), arity='?')
            else:
                assert name in self.ConstraintsDecorator.Preconditions, (self.Name, name)
                type_info = self.ConstraintsDecorator.Preconditions[name]

            assert type_info, (self.Name, name)

            if not isinstance(type_info, all_types_tuple):
                raise Exception("Only fundamental types are supported ({}, {}, {})".format( self.Name,
                                                                                            name,
                                                                                            type_info,
                                                                                          ))

            if name in self.EntryPointDecorator.Parameters:
                provided_info = self.EntryPointDecorator.Parameters[name]
            else:
                provided_info = EntryPoint.Parameter()

            # Calculate the dispay arity
            if isinstance(type_info, DictTypeInfo):
                if not type_info.Arity.IsSingle and not type_info.Arity.IsOptional:
                    raise Exception("Dictionaries must have an arity of 1 or ? ({}, {})".format( self.Name,
                                                                                                 name,
                                                                                               ))

                for k, v in six.iteritems(type_info.Items):
                    if not isinstance(v, StringTypeInfo):
                        raise Exception("Dictionary value types must be strings ({}, {}, {})".format( self.Name,
                                                                                                      name,
                                                                                                      k,
                                                                                                    ))

                display_arity = '*' if type_info.Arity.IsOptional or not is_positional else '+'

            elif type_info.Arity.IsSingle:
                display_arity = '1'
            elif type_info.Arity.IsOptional:
                display_arity = '?'
            elif type_info.Arity.IsCollection:
                display_arity = '*' if type_info.Arity.Min == 0 else '+'
            else:
                raise Exception("Types must have an arity of '1', '?', '+', or '*' ({}, {})".format( self.Name,
                                                                                                     name,
                                                                                                   ))

            # Are we still looking at positional args?
            if ( is_positional and
                 (index >= first_optional_arg_index or display_arity != '1') and
                 index != len(args) - 1
               ):
                is_positional = False

            parameters.append(self.ParameterInfo( type_info,
                                                  name,
                                                  provided_info.Description,
                                                  display_arity,
                                                  provided_info.PostprocessFunc,
                                                  provided_info.AllowDuplicates,
                                                  is_positional,
                                                  index < first_optional_arg_index,
                                                  isinstance(type_info, BoolTypeInfo) and index >= first_optional_arg_index and defaults[index - first_optional_arg_index] is not None,
                                                  defaults[index - first_optional_arg_index] if index >= first_optional_arg_index else self.ParameterInfo.NoDefault,
                                                ))

        self.Parameters                     = parameters

    # ----------------------------------------------------------------------
    def __call__(self, *args, **kwargs):
        return self.Function(*args, **kwargs)

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

    # ----------------------------------------------------------------------
    # |  Private Methods
    @staticmethod
    def _GetArgSpec(function):
        if sys.version_info[0] == 2:
            return inspect.getargspec(function)
        
        return inspect.getfullargspec(function)

# ----------------------------------------------------------------------
class Executor(object):
    """Command line processor and invoker."""

    # ----------------------------------------------------------------------
    def __init__( self,
                  args=sys.argv,
                  command_line_arg_prefix='/',
                  command_line_keyword_separator='=',
                  command_line_dict_tag_value_separator=':',
                  args_in_a_file_prefix='@',
                  script_name=None,
                  script_description=None,
                  script_description_prefix=None,
                  script_description_suffix=None,
                  entry_points=None,
                ):
        mod = sys.modules["__main__"]

        self.Args                                       = args
        self.CommandLineArgPrefix                       = command_line_arg_prefix
        self.CommandLineKeywordSeparator                = command_line_keyword_separator
        self.CommandLineDictTagValueSeparator           = command_line_dict_tag_value_separator
        self.ArgsInAFilePrefix                          = args_in_a_file_prefix
        self.ScriptName                                 = script_name or (mod.CommandLineScriptName() if hasattr(mod, "CommandLineScriptName") else os.path.basename(self.Args[0]))
        self.ScriptDescription                          = script_description or (mod.CommandLineScriptDescription() if hasattr(mod, "CommandLineScriptDescription") else mod.__doc__) or ''
        self.ScriptDescriptionPrefix                    = script_description_prefix or (mod.CommandLinePrefix() if hasattr(mod, "CommandLinePrefix") else '')
        self.ScriptDescriptionSuffix                    = script_description_suffix or (mod.CommandLineSuffix() if hasattr(mod, "CommandLineSuffix") else '')
        self.EntryPoints                                = entry_points or EntryPointInformation.FromModule(mod)

        if not self.EntryPoints:
            raise Exception("No entry points were provided or found")

        self._keyword_regex = re.compile(textwrap.dedent(
                                           r"""^(?#
                                            Prefix:             )\s*{prefix}(?#
                                            Tag:                )(?P<tag>\S+?)(?#
                                            [optional begin]    )(?:(?#
                                                Sep:            )\s*(?<!\\){separator}\s*(?#
                                                Value:          )(?P<value>.+?)\s*(?#
                                            [optional end]      ))?(?#
                                            )$""").format( prefix=re.escape(self.CommandLineArgPrefix),
                                                           separator=re.escape(self.CommandLineKeywordSeparator),
                                                        ))

        self._dict_regex = re.compile(textwrap.dedent(
                                           r"""^(?#
                                            Tag:                )\s*(?P<tag>.+?)(?#
                                            Sep:                )\s*(?<!\\){separator}\s*(?#
                                            Value:              )(?P<value>.+?)\s*(?#
                                            )$""").format( separator=re.escape(self.CommandLineDictTagValueSeparator),
                                                         ))

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

    # ----------------------------------------------------------------------
    def Invoke( self,
                output_stream=sys.stdout,
                verbose=False,
                print_results=False,
                allow_exceptions=False,
              ):
        arg_strings = list(self.Args)
        
        debug_mode = False
        if len(arg_strings) > 1 and arg_strings[1].lower() == DEBUG_COMMAND_LINE_ARG:
            debug_mode = True
            del arg_strings[1]

        # Is there a request for verbose help?
        # TODO: Method-specific help
        if any(arg.startswith(self.CommandLineArgPrefix) and arg[len(self.CommandLineArgPrefix):].lower() in [ "?", "help", "h", ] for arg in arg_strings):
            return self.Usage(verbose=True)

        # Get the function to call
        if len(self.EntryPoints) == 1:
            # If there is only 1 entry point, don't make the user provide the name
            # on the command line
            entry_point = self.EntryPoints[0]
            arg_strings = arg_strings[1:]
        else:
            # The first arg is the entry point name
            if len(arg_strings) < 2:
                return self.Usage(verbose=verbose)

            name = arg_strings[1]
            name_lower = name.lower()

            arg_strings = arg_strings[2:]

            entry_point = next((ep for ep in self.EntryPoints if ep.Name.lower() == name_lower), None)
            if entry_point is None:
                return self.Usage( error="'{}' is not a valid command".format(name),
                                   verbose=verbose,
                                 )

        assert entry_point

        if debug_mode:
            output_stream.write(textwrap.dedent(
                """\
                DEBUG INFO:
                {}
                """).format('\n'.join([ str(parameter) for parameter in entry_point.Parameters ])))
            return 1

        # Read the arguments from a file if necessary
        if len(arg_strings) == 1 and arg_strings[0].startswith(self.ArgsInAFilePrefix):
            filename = os.path.join(os.getcwd(), arg_strings[0][len(self.ArgsInAFilePrefix):])

            if not os.path.isfile(filename):
                return self.Usage( error="'{}' is not a valid filename".format(filename),
                                   verbose=verbose,
                                 )

            with open(filename) as f:
                arg_strings = [ line.strip() for line in f.readlines() if line.strip() ]

        # Parse the command line
        result = self._ParseCommandLine(entry_point, arg_strings)
        if isinstance(result, six.string_types):
            return self.Usage( error=result,
                               verbose=verbose,
                             )

        kwargs = result

        if verbose:
            output_stream.write(textwrap.dedent(
                """\

                INFO: Calling '{name}' was the arguments:
                {args}

                """).format( name=entry_point.Name,
                             args='\n'.join([ "    {k:<20}  {v}".format( k="{}:".format(k),
                                                                         v=v,
                                                                       )
                                              for k, v in six.iteritems(kwargs)
                                            ]),
                           ))

        # Invoke the method
        try:
            result = entry_point(**kwargs)
            
            if print_results:
                if isinstance(result, types.GeneratorType):
                    result = '\n'.join([ "{}) {}".format(index, str(item)) for index, item in enumerate(result) ])

                output_stream.write(textwrap.dedent(
                    """\
                    ** Result **
                    {}
                    """).format(result))

                result = 0

            if result is None:
                result = 0

        except UsageException as ex:
            result = self.Usage( error=str(ex),
                                 verbose=verbose,
                               )

        except ValidationException as ex:
            result = self.Usage( error=str(ex),
                                 verbose=verbose,
                               )

        except KeyboardInterrupt:
            result = -1

        except:
            if allow_exceptions:
                raise

            if not getattr(sys.exc_info()[1], "_DisplayedException", False):
                import traceback

                output_stream.write("ERROR: {}".format('\n'.join([ "       {}".format(line) for line in traceback.format_exc().split('\n') ])))

            result = -1

        return result

    # ----------------------------------------------------------------------
    def Usage( self,
               error=None,
               error_stream=sys.stderr,
               verbose=False,
             ):
        error_stream.write(textwrap.dedent(
            """\
            {desc}{prefix}

                Usage:
            """).format( desc=StringHelpers.Wrap(self.ScriptDescription, MAX_COLUMN_WIDTH),
                         prefix='' if not self.ScriptDescriptionPrefix else "\n\n{}".format(self.ScriptDescriptionPrefix),
                       ))

        if len(self.EntryPoints) == 1:
            standard, verbose_desc = self._GenerateUsageInformation(self.EntryPoints[0])
            if verbose:
                standard = "{}\n\n{}".format(standard, verbose_desc)

            error_stream.write("    {} {}".format(self.ScriptName, '\n'.join([ "    {}".format(line) for line in standard.split('\n') ])))
        else:
            pass

        print("BugBug******************", error)
        return -1


    # ----------------------------------------------------------------------
    def _ParseCommandLine(self, entry_point, args):
        argument_values = {}

        # ----------------------------------------------------------------------
        def ApplyImpl(parameter, arg):
            if isinstance(parameter.TypeInfo, DictTypeInfo):
                # Add the dictionary values; we will validate later.
                match = self._dict_regex.match(arg)
                if not match:
                    return "'{}' is not a valid dictionary entry".format(arg)

                tag = match.group("tag")
                tag = tag.replace("\\{}".format(self.CommandLineDictTagValueSeparator), self.CommandLineDictTagValueSeparator)

                value = match.group("value")

                argument_values.setdefault(parameter.Name, OrderedDict())

                if tag not in argument_values[parameter.Name]:
                    if parameter.AllowDuplicates:
                        argument_values[parameter.Name][tag] = [ value, ]
                    else:
                        argument_values[parameter.Name][tag] = value
                else:
                    if not parameter.AllowDuplicates:
                        return "A value for '{}'s tag '{}' has already been provided ({})".format( parameter.Name,
                                                                                                   tag,
                                                                                                   argument_values[parameter.Name][tag],
                                                                                                 )

                    argument_values[parameter.Name][tag].append(value)

                return

            if parameter.IsSwitch:
                # Preserve the value as a string so it can be deserialized below
                arg = StringSerialization.SerializeItem(parameter.TypeInfo, not parameter.DefaultValue)

            try:
                if isinstance(parameter.TypeInfo, tuple(ALL_FUNDAMENTAL_TYPES)):
                    value = StringSerialization.DeserializeItem(parameter.TypeInfo, arg)
                elif isinstance(parameter.TypeInfo, AnyOfTypeInfo):
                    found = False

                    for eti in parameter.TypeInfo.ElementTypeInfos:
                        try:
                            value = StringSerialization.DeserializeItem(eti, arg)
                            found = True
                            break
                        except ValidationException:
                            pass

                    if not found:
                        value = arg

                else:
                    value = arg

                if parameter.PostprocessFunc:
                    value = parameter.PostprocessFunc(value)

            except ValidationException as ex:
                return str(ex)

            if parameter.DisplayArity in [ '?', '1', ]:
                if parameter.Name in argument_values:
                    return "A value for '{}' has already been provided ({})".format( parameter.Name,
                                                                                     argument_values[parameter.Name],
                                                                                   )

                argument_values[parameter.Name] = value

            elif parameter.DisplayArity in [ '*', '+', ]:
                argument_values.setdefault(parameter.Name, []).append(value)

            else:
                assert False

        # ----------------------------------------------------------------------
        def ApplyPositionalArgument(parameter, arg):
            if parameter.IsSwitch:
                if ( not arg.startswith(self.CommandLineArgPrefix) or 
                     arg[len(self.CommandLineArgPrefix):].lower() != parameter.Name.lower()
                   ):
                    return "'{}' is not a recognized command line argument".format(arg)

                return ApplyImpl(parameter, None)

            return ApplyImpl(parameter, arg)

        # ----------------------------------------------------------------------
        def ApplyKeywordArgument(arg):
            match = self._keyword_regex.match(arg)
            if not match:
                return "'{}' is not a valid keyword argument".format(arg)

            tag = match.group("tag")
            value = match.group("value")

            tag_lower = tag.lower()

            parameter = None
            for potential_param in entry_point.Parameters:
                if potential_param.Name.lower() == tag_lower and not potential_param.IsPositional:
                    parameter = potential_param
                    break

            if parameter is None:
                return "'{}' is not a recognized command line argument".format(tag)
            if value is None and not parameter.IsSwitch:
                return "A value was expected with the keyword argument '{}'".format(tag)
            if value is not None and parameter.IsSwitch:
                return "A value was not expected with the switch '{}'".format(tag)

            return ApplyImpl(parameter, value)

        # ----------------------------------------------------------------------

        arg_index = 0
        param_index = 0

        while param_index != len(entry_point.Parameters) and arg_index != len(args):
            parameter = entry_point.Parameters[param_index]
            arg = args[arg_index]

            if parameter.IsPositional:
                result = ApplyPositionalArgument(parameter, arg)
            else:
                result = ApplyKeywordArgument(arg)

            if isinstance(result, six.string_types):
                return result

            arg_index += 1

            if parameter.DisplayArity == '1':
                param_index += 1

        # We have problems if there are still args to process
        if arg_index != len(args):
            return "Too many arguments were provided"

        # Ensure that all of the required parameters are present
        for parameter in entry_point.Parameters:
            if parameter.IsRequired and parameter.Name not in argument_values:
                return "'{}' is a required argument".format(parameter.Name)

            if isinstance(parameter.TypeInfo, DictTypeInfo):
                if parameter.Name in argument_values:
                    result = parameter.TypeInfo.ValidateNoThrow(argument_values[parameter.Name])
                    if result is not None:
                        return "'{}' is not in a valid state - {}".format(parameter.Name, result)

                many_default_value = {}
            else:
                many_default_value = parameter.DefaultValue

            # In theory, this will never trigger because we are ensuring arity through argument
            # positionality. However, better safe than sorry.
            result = parameter.TypeInfo.ValidateArityNoThrow(argument_values.get(parameter.Name, many_default_value))
            if result is not None:
                return "'{}' is not in a valid state - {} [unexpected]".format(parameter.Name, result)

        return argument_values

    # ----------------------------------------------------------------------
    def _GenerateUsageInformation(self, entry_point):
        cols = OrderedDict([ ( "Name", 30 ),
                             ( "Type", 15 ),
                             ( "Arity", 8 ),
                             ( "Default", 20 ),
                             ( "Description", 80 ),
                           ])
        # Calculate the verbose template and the left padding associated with verbose
        # descriptions.
        col_padding = 2
        verbose_template = []

        verbose_desc_offset = 0
        for index, width in enumerate(six.itervalues(cols)):
            verbose_template.append("{{{}:<{}}}".format(index, width))

            verbose_desc_offset += width + col_padding

        # Remove the description size from the verbose offset
        verbose_desc_offset -= width
        verbose_template = (col_padding * ' ').join(verbose_template)

        assert verbose_desc_offset < MAX_COLUMN_WIDTH, (verbose_desc_offset, MAX_COLUMN_WIDTH)
        verbose_desc_offset = ' ' * verbose_desc_offset

        # Gather the command line and verbose parts
        command_line = []
        verbose = []

        if entry_point.Parameters:
            verbose.append(verbose_template.format(*six.iterkeys(cols)))
            verbose.append(verbose_template.format(*[ '-' * col_width for col_width in six.itervalues(cols) ]))

            is_multi_line = len(entry_point.Parameters) > 4

            for index, parameter in enumerate(entry_point.Parameters):
                arg = parameter.Name

                if parameter.IsSwitch:
                    arg = "{}{}".format( self.CommandLineArgPrefix,
                                         arg,
                                       )

                elif isinstance(parameter.TypeInfo, DictTypeInfo):
                    if not parameter.IsPositional:
                        prefix = "{}{}{}".format( self.CommandLineArgPrefix,
                                                  arg,
                                                  self.CommandLineKeywordSeparator,
                                                )
                    else:
                        prefix = ''

                    arg = "{}<tag>{}<value>".format( prefix,
                                                     self.CommandLineDictTagValueSeparator,
                                                   )

                elif not parameter.IsPositional:
                    arg = "{}{}{}<value>".format( self.CommandLineArgPrefix,
                                                  arg,
                                                  self.CommandLineKeywordSeparator,
                                                )

                if parameter.IsRequired:
                    arg = "<{}>".format(arg)
                else:
                    arg = "[{}]".format(arg)

                if parameter.DisplayArity in [ '*', '+', ]:
                    arg += parameter.DisplayArity

                if is_multi_line:
                    arg = "\n    {}".format(arg)
                elif index:
                    arg = " {}".format(arg)

                # Verbose
                if parameter.DefaultValue is not EntryPointInformation.ParameterInfo.NoDefault:
                    if parameter.IsSwitch:
                        default_value = "on" if parameter.DefaultValue else "off"
                    else:
                        default_value = parameter.DefaultValue
                else:
                    default_value = ''

                verbose.append(verbose_template.format( parameter.Name,
                                                        "switch" if parameter.IsSwitch else "Dictionary" if isinstance(parameter.TypeInfo, DictTypeInfo) else parameter.TypeInfo.Desc,
                                                        parameter.DisplayArity,
                                                        str(default_value),
                                                        '\n'.join([ "{}{}".format( verbose_desc_offset,
                                                                                   line,
                                                                                 )
                                                                    for line in StringHelpers.Wrap(parameter.Description, MAX_COLUMN_WIDTH - len(verbose_desc_offset)).split('\n')
                                                                  ]),
                                                      ))

                constraints = parameter.TypeInfo.ConstraintsDesc
                if constraints:
                    verbose.append("        - {}\n".format(constraints))

        return ''.join(command_line), '\n'.join(verbose)

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def Main( output_stream=sys.stdout,
          verbose=False,
          print_results=False,
          allow_exceptions=False,
          **executor_kwargs
        ):
    return Executor(**executor_kwargs) \
                .Invoke( output_stream=output_stream,
                         verbose=verbose,
                         print_results=print_results,
                         allow_exceptions=allow_exceptions,
                       )
