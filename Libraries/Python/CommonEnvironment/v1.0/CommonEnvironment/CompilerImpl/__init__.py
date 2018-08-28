# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 08:28:42
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the CompilerImpl object"""

import copy
import os
import re
import sys
import textwrap

import inflect as inflect_mod
import six

from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import Interface, \
                                        abstractmethod, \
                                        abstractproperty, \
                                        extensionmethod
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import StringHelpers

from CommonEnvironment.TypeInfo.FundamentalTypes.DirectoryTypeInfo import DirectoryTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
class CompilerImpl(Interface):
    """
    Base class for Compilers, CodeGenerators, Validators, and other compiler-like
    derived classes. For simplicity, these classes are referred to as "compilers"
    within this file.
    """

    # ----------------------------------------------------------------------
    # |  
    # |  Public Types
    # |  
    # ----------------------------------------------------------------------
    class DiagnosticException(Exception):
        """Exception that should be displayed without stack trace information."""
        IsDiagnosticException               = True

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------

    @abstractproperty
    def Name(self):
        """Name of the compiler"""
        raise Exception("Abstract property")

    @abstractproperty
    def Description(self):
        """Description of the compiler"""
        raise Exception("Abstract property")

    @abstractproperty
    def InputTypeInfo(self):
        """Returns the TypeInfo used to validate input files or directories"""
        raise Exception("Abstract property")

    @abstractproperty
    def InvokeVerb(self):
        """Verb used to invoke the compiler"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  One of these flags will be set to True by a derived class
    IsCompiler                              = False
    IsCodeGenerator                         = False
    IsVerifier                              = False

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------

    @staticmethod
    @extensionmethod
    def ValidateEnvironment():
        """
        Used to determine if a compiler can run in the current environment. This method
        prevents the invocation of a compiler in an environment where it will never be
        successful (for example, an environment where the necessary dependencies are not
        installed).

        Return 0 or None if the environment is valid or a string that describes why the
        environment isn't valid if not.
        """

        # No validation by default
        pass 

    # ----------------------------------------------------------------------
    @classmethod
    def IsSupported(cls, filename):
        """Returns True if the filename provided is valid and has valid content."""
        return cls.InputTypeInfo.IsValid(filename) and cls.IsSupportedContent(filename)

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def IsSupportedContent(filename):
        """
        Returns True if the given input is supported by the compiler.
        
        In most cases, InputTypeInfo is sufficient to determine if an input is valid.
        However, this method exists in case it is necessary to look at the contents
        of the item itself.
        """
        
        # Rely on InputTypeInfo by default
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def IsSupportedTestItem(item):
        """
        Return True if the item is a valid test file.

        Test files can have unique requirements, which can be verified here.
        """

        # Assume no special requirements
        return True

    # ----------------------------------------------------------------------
    @classmethod
    @extensionmethod
    def ItemToTestName(cls, item_name, test_type_name):
        """
        Converts from an item name to its corresponding test file name.

        Override this method if the derived compiler uses custom conventions to 
        convert from an item's name to its corresponding test name.
        """

        if isinstance(cls.InputTypeInfo, DirectoryTypeInfo):
            # We can't reason about test directories, so just return the directory itself.
            # A derived class may want to handle this scenario more gracefully.
            return item_name

        elif isinstance(cls.InputTypeInfo, FilenameTypeInfo):
            dirname, basename = os.path.split(item_name)
            name, ext = os.path.splitext(basename)

            return os.path.join(dirname, test_type_name, "{name}.{test_type}{ext}".format( name=name,
                                                                                           test_type=inflect.singular_noun(test_type_name) or test_type_name,
                                                                                           ext=ext,
                                                                                         ))

        assert False, (cls.Name, cls.InputTypeInfo)
        return None

    # ----------------------------------------------------------------------
    @classmethod
    @extensionmethod
    def TestToItemName(cls, test_filename):
        """
        Converts from a test name to its corresponding item name.

        Override this method if the derived compiler uses custom conventions to 
        convert from a test's name to its corresponding item name.
        """

        if isinstance(cls.InputTypeInfo, DirectoryTypeInfo):
            # We can't reason about item directories, so just return the directory itself.
            # A derived class may want to handle this scenario more gracefully.
            return test_filename

        elif isinstance(cls.InputTypeInfo, FilenameTypeInfo):
            dirname, basename = os.path.split(test_filename)

            match = re.match( r"^(?P<name>.+)\.(?P<test_type>[^_\.]+Test)(?P<ext>\..+)$",
                              basename,
                            )
            if not match:
                raise Exception("'{}' is not a recognized test name".format(test_filename))

            name = "{}{}".format(match.group("name"), match.group("ext"))
            test_type = match.group("test_type")

            if dirname and os.path.basename(dirname) == inflect.plural(test_type):
                dirname = os.path.dirname(dirname)

            return os.path.join(dirname, name)

        assert False, (cls.Name, cls.InputTypeInfo)
        return None

    # ----------------------------------------------------------------------
    @classmethod
    def GenerateContextItems( cls,
                              inputs,
                              **kwargs
                            ):
        """
        Yields one or more context items from the given input.

        Context objects are arbitrary python objects used to define state/context
        about the invocation of the compiler. This information is used to specify 
        input and determine if the compiler should be invoked. 
        
        This context object must support pickling.
        """

        if not isinstance(inputs, list):
            inputs = [ inputs, ]

        # Inputs may be grouped or produce a number of invocation groups.
        invocation_group_inputs = []

        for input in inputs:
            if os.path.isfile(input):
                if isinstance(cls.InputTypeInfo, FilenameTypeInfo):
                    result = cls.InputTypeInfo.ValidateItemNoThrow(input)   # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
                    if result is not None:
                        raise cls.DiagnosticException(result)

                    potential_inputs = [ input, ]
                elif isinstance(cls.InputTypeInfo, DirectoryTypeInfo):
                    raise cls.DiagnosticException("The filename '{}' was provided as input, but this object operates on directories.".format(input))
                else:
                    assert False, (cls.Name, cls.InputTypeInfo)

            elif os.path.isdir(input):
                if isinstance(cls.InputTypeInfo, FilenameTypeInfo):
                    potential_inputs = [ filename for filename in FileSystem.WalkFiles(input) if cls.InputTypeInfo.IsValid(filename) ]      # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
                elif isinstance(cls.InputTypeInfo, DirectoryTypeInfo):
                    result = cls.InputTypeInfo.ValidateItem(input)          # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
                    if result is not None:
                        raise cls.DiagnosticException(result)

                    potential_inputs = [ input, ]
                else:
                    assert False, (cls.Name, cls.InputTypeInfo)

            else:
                raise Exception("The input '{}' is not a valid filename or directory".format(input))

            invocation_group_inputs += [ potential_input for potential_input in potential_inputs if cls.IsSupportedContent(potential_input) ]

        # Populate default metadata
        optional_metadata = cls._GetOptionalMetadata()
        
        if optional_metadata is None:
            # ----------------------------------------------------------------------
            def MetadataGenerator():
                # <Using a conditional statement with a constant value> pylint: disable = W0125
                if False:
                    yield

            # ----------------------------------------------------------------------

        elif isinstance(optional_metadata, dict):
            # ----------------------------------------------------------------------
            def MetadataGenerator():
                for kvp in six.iteritems(optional_metadata):
                    yield kvp

            # ----------------------------------------------------------------------

        elif isinstance(optional_metadata, list):
            # ----------------------------------------------------------------------
            def MetadataGenerator():
                for t in optional_metadata:
                    yield t

            # ----------------------------------------------------------------------

        else:
            assert False, type(optional_metadata)

        for k, v in MetadataGenerator():
            if k not in kwargs or kwargs[k] is None or kwargs[k] == '':
                kwargs[k] = v

        for metadata in cls._GenerateMetadataItems(invocation_group_inputs, copy.deepcopy(kwargs)):
            for required_name in cls._GetRequiredMetadataNames():
                if required_name not in metadata:
                    raise Exception("'{}' is required metadata".format(required_name))

            metadata = copy.deepcopy(metadata)

            if not cls.GetInputItems(metadata):
                continue

            display_name = cls._GetDisplayName(metadata)
            if display_name:
                metadata["display_name"] = display_name

            context = cls._CreateContext(metadata)
            if not context:
                continue

            for required_name in cls._GetRequiredContextNames():
                if required_name not in context:
                    raise Exception("'{}' is required for {} ({})".format( required_name,
                                                                           cls.Name,
                                                                           ', '.join([ "'{}'".format(input) for input in cls.GetInputItems(context) ]),
                                                                         ))

            yield context

    # ----------------------------------------------------------------------
    @classmethod
    def GetContextItem( cls,
                        input,
                        **kwargs
                      ):
        """Calls GenerateContextItems, ensuring that there is only one context generated"""

        contexts = list(cls.GenerateContextItems(input, **kwargs))
        if not contexts:
            return None

        if len(contexts) != 1:
            raise Exception("Multiple contexts were found ({})".format(len(contexts)))

        return contexts[0]

    # ----------------------------------------------------------------------
    @classmethod
    def Clean(cls, context, optional_output_stream):
        """
        Handles the complexities associated with cleaning previously generated output,
        ultimately invoking _CleanImpl.
        """

        assert context
        output_stream = StreamDecorator(optional_output_stream)

        output_stream.write(cls._GetStatusText("Cleaning", context, cls.GetInputItems(context)))
        with output_stream.DoneManager() as dm:
            dm.result = cls._CleanImpl(context, dm.stream) or 0
            return dm.result

    # ----------------------------------------------------------------------
    # |  
    # |  Protected Methods
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    def _Invoke(cls, context, status_stream, verbose):
        """Handles the complexities of compiler invocation, ultimately calling _InvokeImpl."""
    
        assert context
        status_stream = StreamDecorator(status_stream)

        invoke_reason = cls._GetInvokeReason(context, StreamDecorator(status_stream if verbose else None))
        if invoke_reason is None:
            status_stream.write("No changes were detected.\n")
            return 0

        input_items = cls.GetInputItems(context)
        assert input_items

        status_stream.write(cls._GetStatusText(cls.InvokeVerb, context, input_items))
        with status_stream.DoneManager() as dm:
            if verbose:
                output_items = cls.GetOutputItems(context)

                if "display_name" in context or len(input_items) == 1:
                    indentation = 4
                else:
                    indentation = 8

                verbose_stream = StreamDecorator( dm.stream,
                                                  prefix=StringHelpers.LeftJustify( textwrap.dedent(
                                                                                        # <Wrong hanging indentation> pylint: disable = C0330
                                                                                        """\

                                                                                        ========================================
                                                                                        VERBOSE Output

                                                                                        {}
                                                                                                ->
                                                                                            {}
                                                                                        ========================================      
                                                                                        """).format( '\n'.join(input_items),
                                                                                                     StringHelpers.LeftJustify('\n'.join(output_items) if output_items else "[None]", 4),
                                                                                                   ),
                                                                                    2,
                                                                                    skip_first_line=False,
                                                                                  ),
                                                  suffix='\n',
                                                  line_prefix=' ' * indentation,
                                                )
                status_stream = verbose_stream
            else:
                status_stream = dm.stream
                verbose_stream = StreamDecorator(None)

            dm.result = cls._InvokeImpl( invoke_reason,
                                         context,
                                         status_stream,
                                         verbose_stream,
                                         verbose,
                                       ) or 0

            if dm.result >= 0:
                cls._PersistContext(context)

            return dm.result

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetInputItems(contet):
        """Implemented by an InputProcessingMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def GetOutputItems(context):
        """Implemented by an OutputMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def _GetDisplayName(metadata_or_context):
        """Name used to uniquely identify the compliation in status messages."""
        return None

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def _GetOptionalMetadata():
        """
        Metadata that should be applied if it doesn't already exist. 

        [ ( key, value ), ... ]
        """

        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def _GetRequiredMetadataNames():
        """
        Names that must be a part of the metadata.

        This method is invoked on metadata provided by the caller.
        """
        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def _GetRequiredContextNames():
        """
        Names that must be a part of the context.

        This method is invoked on context after the caller-provided metadata has
        been converted to context via _CreateContext.
        """
        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def _CreateContext(metadata):
        """Returns a context object tuned specifically for the provided metadata"""

        # No conversion by default
        return metadata

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GenerateMetadataItems(invocation_group_inputs, user_provided_metadata):
        """Implemented by an InputProcessingMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _CleanImpl(context, output_stream):
        """Implemented by an OutputMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _InvokeImpl(invoke_reason, context, status_stream, verbose_stream, verbose):
        """Implemented by an InvocationMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GetInvokeReason(context, output_stream):
        """Implemented by an InvocationQueryMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _PersistContext(context):
        """Implemented by an InvocationQueryMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _GetStatusText(cls, verb, context, input_items):
        if "display_name" in context:
            status_suffix = '"{}"...'.format(context["display_name"])
        elif len(input_items) == 1:
            status_suffix = '"{}"...'.format(input_items[0])
        else:
            status_suffix = textwrap.dedent(
                                # <Wrong hanging indentation> pylint: disable = C0330
                                """\

                                {}
                                """).fromat('\n'.join([ "    - {}".format(input_item) for input_item in input_items ]))

        return "{} {}".format(verb, status_suffix)
