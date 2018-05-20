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

from CommonEnvironment.TypeInfo.FundamentalTypeInfo.DirectoryTypeInfo import DirectoryTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypeInfo.FilenameTypeInfo import FilenameTypeInfo

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

    @extensionmethod
    @staticmethod
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
    @extensionmethod
    @staticmethod
    def IsSupported(item):
        """
        Returns True if the given input is supported by the compiler.
        
        In most cases, InputTypeInfo is sufficient to determine if an input is valid.
        However, this method exists in case it is necessary to look at the contents
        of the item itself.
        """
        
        # Rely on InputTypeInfo by default
        return True

    # ----------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def IsSupportedTestFile(item):
        """
        Return True if the item is a valid test file.

        Test files can have unique requirements, which can be verified here.
        """

        # Assume no special requirements
        return True

    # ----------------------------------------------------------------------
    @extensionmethod
    @classmethod
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

        else:
            assert False, (cls.Name, cls.InputTypeInfo)

    # ----------------------------------------------------------------------
    @extensionmethod
    @classmethod
    def TestToItemNae(cls, test_name):
        """
        Converts from a test name to its corresponding item name.

        Override this method if the derived compiler uses custom conventions to 
        convert from a test's name to its corresponding item name.
        """

        if isinstance(cls.InputTypeInfo, DirectoryTypeInfo):
            # We can't reason about item directories, so just return the directory itself.
            # A derived class may want to handle this scenario more gracefully.
            return test_name

        elif isinstance(cls.InputTypeInfo, FilenameTypeInfo):
            dirname, basename = os.path.split(test_filename)

            match = repr.match( r"^(?P<name>.+?)\.(?P<test_type>.+?)(?P<ext>\..+?)$",
                                basename,
                              )
            if not match:
                raise Exception("'{}' is not a recognized test name".format(test_name))

            name = "{}{}".format(match.group("name"), match.group("ext"))
            test_type = match.group("test_type")

            if path and os.path.basename(path) == inflect.plural(test_type):
                path = os.path.dirname(path)

            return os.path.join(path, name)

        else:
            assert False, (cls.Name, cls.InputTypeInfo)

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
                    potential_inputs = [ input, ]
                elif isinstance(cls.InputTypeInfo, DirectoryTypeInfo):
                    raise Exception("The filename '{}' was provided as input, but this object operates on directories.".format(input))
                else:
                    assert False, (cls.Name, cls.InputTypeInfo)

            elif os.path.isdir(input):
                if isinstance(cls.InputTypeInfo, FilenameTypeInfo):
                    potential_inputs = list(FileSystem.WalkFiles(input))
                elif isinstance(cls.InputTypeInfo, DirectoryTypeInfo):
                    potential_inputs = [ input, ]
                else:
                    assert False, (cls.Name, cls.InputTypeInfo)

            else:
                raise Exception("The input '{}' is not a valid filename or directory".format(input))

            invocation_group_inputs += [ potential_input for potential_input in potential_inputs if cls.IsSupported(potential_input) ]

        # Populate default metadata
        optional_metadata = cls._GetOptionalMetadata()
        
        if optional_metadata is None:
            # ----------------------------------------------------------------------
            def MetadataGenerator():
                if False:
                    yield

            # ----------------------------------------------------------------------

        elif isinstance(optional_metadata, dict):
            # ----------------------------------------------------------------------
            def MetadataGenerator():
                for kvp in six.iterites(optional_metadata):
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

            if not cls._GetInputItems(metadata):
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
                                                                           ', '.join([ "'{}'".format(input) for input in cls._GetInputItems(context) ]),
                                                                         ))

            yield context

    # ----------------------------------------------------------------------
    @classmethod
    def GetContextItem( cls,
                        input,
                        **kwargs
                      ):
        """Calls GenerateContextItems, ensuring that there is only one context generated"""

        contexts = list(cls.GenerateContextItems(inputs, **kwargs))
        if not contexts:
            return

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

        output_stream.write(cls._GetStatusText("Cleaning", context, cls._GetInputItems(context)))
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

        input_items = cls._GetInputItems(context)
        assert input_items

        status_stream.write(cls._GetStatusText(cls.InvokeVerb, context, input_items))
        with status_stream.DoneManager() as dm:
            if verbose:
                output_items = cls._GetOutputFilenames(context)

                if "display_name" in context or len(input_items) == 1:
                    indentation = 4
                else:
                    indentation = 8

                verbose_stream = StreamDecorator( dm.stream,
                                                  prefix=StringHelpers.LeftJustify( textwrap.dedent(
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
                                       )

            if dm.result >= 0:
                cls._PersistContext(context)

            return dm.result

    # BugBug: ApplyExternalConfigurations
    # BugBug: ShouldProcessConfigInfo
    
    # ----------------------------------------------------------------------
    @classmethod
    def PopulateEnvironmentVars( s, 
                                 _placeholder_prefix="${",
                                 _placeholder_suffix="}",
                                 **additional_args,
                               ):
        """
        Will replace placeholders in the form '${var}' in the given string with
        the value in the current environment.

        This can be helpful when populating metadata/context items.
        """

        placeholder = "<!!--__"
        
        additional_args_lower = {}
        for k, v in six.iteritems(additional_args):
            additional_args_lower[k.lower()] = v

        environ_lower = {}
        for k, v in six.iteritems(os.environ):
            environ_lower[k.lower()] = v

        regex = re.compile(r"{prefix}(?P<var>.+?){suffix}".format( re.escape(_placeholder_prefix),
                                                                   re.escape(_placeholder_suffix),
                                                                 ))

        # ----------------------------------------------------------------------
        def Sub(match):
            var = match.group("var").lower()

            if var in additional_args_lower:
                return additional_args_lower[var]

            if var in environ_lower:
                return environ_lower[var]

            # Match wasn't found. Give it a placeholder so we don't keep trying
            # to evaluate it.
            return match.string[match.start() : match.end()].replace(_placeholder_prefix, placeholder)

        # ----------------------------------------------------------------------

        # Recursively apply placeholders
        while _placeholder_prefix in s:
            s = regex.sub(Sub, s)

        return s.replace(placeholder, _placeholder_prefix)

    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------

    # BugBug: Move this
    @extensionmethod
    @staticmethod
    def _GetAdditionalGeneratorFiles(context):
        """
        Specify a list of additional filenames that are used to implement compilation
        functionality. Any changes to these files imply that all previously generated
        content should be regenerated when invoked again.
        """

        # No additional generator files
        return []

    # ----------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def _GetDisplayName(metadata_or_context):
        """Name used to uniquely identify the compliation in status messages."""
        return None

    # ----------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def _GetOptionalMetadata():
        """
        Metadata that should be applied if it doesn't already exist. 
        
        The return value can be a dict or list of (key, value) tuples.
        """

        return []

    # ----------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def _GetRequiredMetadataNames():
        """
        Names that must be a part of the metadata.

        This method is invoked on metadata provided by the caller.
        """
        return []

    # ----------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def _GetRequiredContextNames():
        """
        Names that must be a part of the context.

        This method is invoked on context after the caller-provided metadata has
        been converted to context via _CreateContext.
        """
        return []

    # ----------------------------------------------------------------------
    @extensionmethod
    @staticmethod
    def _CreateContext(metadata):
        """Returns a context object tuned specifically for the provided metadata"""

        # No conversion by default
        return metadata

    # ----------------------------------------------------------------------
    @abstractmethod
    @staticmethod
    def _GenerateMetadataItems(invocation_group_inputs, user_provided_metadata):
        """Implemented by an InputProcessingMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @abstractmethod
    @staticmethod
    def _GetInputItems(contet):
        """Implemented by an InputProcessingMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @abstractmethod
    @staticmethod
    def _GetOutputFilenames(context):
        """Implemented by an OutputMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @abstractmethod
    @staticmethod
    def _CleanImpl(context, output_stream):
        """Implemented by an OutputMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @abstractmethod
    @staticmethod
    def _InvokeImpl(invoke_reason, context, status_stream, verbose_stream, verbose):
        """Implemented by an InvocationMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @abstractmethod
    @staticmethod
    def _GetInvokeReason(context, output_stream):
        """Implemented by an InvocationQueryMixin"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
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
                                """\

                                {}
                                """).fromat('\n'.join([ "    - {}".format(input_item) for input_item in input_items ]))

        return "{} {}".format(prefix, status_suffix)
