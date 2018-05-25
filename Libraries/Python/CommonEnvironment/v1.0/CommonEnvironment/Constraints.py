# ----------------------------------------------------------------------
# |  
# |  Constraints.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 15:35:30
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Constraints decorator."""

import inspect
import os
import sys
import textwrap

import inflect as inflect_mod
import six
import wrapt

from CommonEnvironment.TypeInfo import ValidationException
from CommonEnvironment.TypeInfo.DictTypeInfo import DictTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.All import CreateFromPythonType as CreateFundamentalFromPythonType

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
@wrapt.decorator
class Constraints(object):
    """
    Decorator that validated pre- and post-condition constraints.

    Example:
        @Constraints( foo=IntTypeInfo(min=10, max=20),
                      bar=StringTypeInfo(min_length=2),
                    )
        def Func(foo, bar):
            # If here..., 
            #   - foo is an integer between 10 and 20
            #   - bar is a string with at least 2 characters
    """

    # ----------------------------------------------------------------------
    def __init__( self,
                  postcondition=None,       
                  postconditions=None,
                  **precondition_type_infos
                ):
        """Pre- and post-conditions are all derived TypeInfo objects"""

        self.Preconditions                  = precondition_type_infos or {}
        self.Postconditions                 = postconditions or []

        if postcondition:
            self.Postconditions.append(postcondition)

        if not self.Preconditions and not self.Postconditions:
            raise Exception("Preconditions and/or postconditions must be provided")

        self._args_to_kwargs_func           = None      # Lazy init

    # ----------------------------------------------------------------------
    def __call__(self, wrapped, instance, args, kwargs):
        if self._args_to_kwargs_func is None:
            # Create a function that will map all positional arguments into the keyboard map
            if sys.version_info[0] == 2:
                arg_info = inspect.getargspec(wrapped)
            else:
                arg_info = inspect.getfullargspec(wrapped)

            arg_defaults = arg_info.defaults or []
            optional_args = arg_info.args[len(arg_info.args) - len(arg_defaults) :]

            if self.Preconditions:
                first_optional_arg_index = len(arg_info.args) - len(optional_args)

                # Ensure that the precondition names match the function argument names
                precondition_names = set(six.iterkeys(self.Preconditions))
                missing = []

                for index, arg in enumerate(arg_info.args):
                    if arg in precondition_names:
                        precondition_names.remove(arg)
                    elif index < first_optional_arg_index:
                        missing.append(arg)
                    else:
                        # Create a TypeInfo object based on the default
                        default_value = arg_defaults[index - first_optional_arg_index]

                        these_kwargs = { "arity" : '?', }

                        if default_value == '':
                            these_kwargs["min_length"] = 0

                        self.Preconditions[arg] = CreateFundamentalFromPythonType(type(default_value), **these_kwargs)
                
                # Capture all errors
                errors = []

                errors += [ "A precondition was not provided for '{}'".format(arg) for arg in missing ]
                errors += [ "A precondition was provided for '{}'".format(arg) for arg in precondition_names ]

                if errors:
                    raise Exception(textwrap.dedent(
                                        """\
                                        Constraint configuration for '{}' is not valid:
                                        {}
                                        """).format( wrapped,
                                                     '\n'.join([ "    - {}".format(error) for error in errors ]),
                                                   ))

            # ----------------------------------------------------------------------
            def ArgsToKwargs(args, kwargs):
                # Copy the position args into the kwargs map
                assert len(args) <= len(arg_info.args)

                index = 0
                while index < len(args):
                    kwargs[arg_info.args[index]] = args[index]
                    index += 1

                # Copy the optional args
                for arg, default_value in six.moves.zip(optional_args, arg_defaults):
                    if arg not in kwargs:
                        kwargs[arg] = default_value

                        # Default parameter values in python arg string in that it is better
                        # to provide a None value in the function signature rather than an empty 
                        # list when the arity is '*', as that empty list may be modified within
                        # the function itself. However, parameter validation requires an empty list
                        # rather than None. Handle that wonkiness here by providing the actual value.
                        if ( default_value is None and
                             arg in self.Preconditions and
                             self.Preconditions[arg] is not None
                           ):
                            if self.Preconditions[arg].Arity.IsCollection:
                                kwargs[arg] = []
                            elif isinstance(self.Preconditions[arg], DictTypeInfo):
                                kwargs[arg] = {}

                return kwargs

            # ----------------------------------------------------------------------

            self._args_to_kwargs_func = ArgsToKwargs

        # Validate the arguments
        kwargs = self._args_to_kwargs_func(args, kwargs)

        if self.Preconditions:
            assert len(kwargs) == len(self.Preconditions)

            for k, v in six.iteritems(kwargs):
                assert k in self.Preconditions, k

                type_info = self.Preconditions[k]
                if type_info is None:
                    continue

                result = type_info.ValidateNoThrow(v)
                if result is not None:
                    raise ValidationException("Validation for the arg '{}' failed - {}".format(k, result))

        # Invoke the function
        func_result = wrapped(**kwargs)

        # Validate postconditions
        for postcondition in self.Postconditions:
            if postcondition is None:
                continue

            result = postcondition.ValidateNoThrow(func_result)
            if result is not None:
                raise ValidationException("Validation for the result failed - {}".format(result))

        return func_result
