# ----------------------------------------------------------------------
# |  
# |  DistutilsCompilerImpl.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-06-02 12:03:24
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the DistutilsCompilerImpl object"""

import os
import sys

from enum import Enum
import six

from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment.Interface import abstractmethod, override, DerivedProperty
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironment.CompilerImpl.Compiler import Compiler as CompilerImpl, CommandLineCompile, CommandLineClean
from CommonEnvironment.CompilerImpl.InputProcessingMixin.AtomicInputProcessingMixin import AtomicInputProcessingMixin
from CommonEnvironment.CompilerImpl.InvocationQueryMixin.AlwaysInvocationQueryMixin import AlwaysInvocationQueryMixin
from CommonEnvironment.CompilerImpl.OutputMixin.MultipleOutputMixin import MultipleOutputMixin

from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class DistutilsCompilerImpl( AtomicInputProcessingMixin,
                             AlwaysInvocationQueryMixin,
                             MultipleOutputMixin,
                             CompilerImpl,
                           ):
    """
    Many different python compilers (such as cx_Freexe, Py2Exe, etc.) rely on
    distutils functionality. This base class can be used to implement many of
    the common details.
    """

    # ----------------------------------------------------------------------
    # |  Public Properties
    Description                             = DerivedProperty("Creates an executable for a python file.")
    InputTypeInfo                           = DerivedProperty(FilenameTypeInfo(validation_expression=r".+\.py"))

    class BuildType(Enum):
        Console = 1
        Windows = 2

    # ----------------------------------------------------------------------
    # |  Public Methods
    @classmethod
    @override
    def _GetRequiredContextNames(cls):
        return [ "output_dir", ] + \
               super(DistutilsCompilerImpl, cls)._GetRequiredContextNames()

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetOptionalMetadata(cls):
        return [ ( "preserve_temp_dir", False ),

                 # General modifiers
                 ( "build_type", cls.BuildType.Console ),
                 ( "include_tcl", False ),
                 ( "no_optimize", False ),
                 ( "no_bundle", False ),
                 ( "manifest_filename", None ),
                 ( "icon_filename", None ),
                 ( "paths", [] ),
                 ( "includes", [] ),
                 ( "excludes", [] ),
                 ( "packages", [] ),
                 ( "distutil_args", [] ),
                 ( "output_name", None ),

                 # Embedded metadata
                 ( "comments", '' ),
                 ( "company_name", '' ),
                 ( "file_description", '' ),
                 ( "internal_name", '' ),
                 ( "copyright", '' ),
                 ( "trademark", '' ),
                 ( "name", '' ),
                 ( "version", '' ),
               ] +super(DistutilsCompilerImpl, cls)._GetOptionalMetadata()

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _CreateContext(cls, metadata):
        if len(metadata["inputs"]) != 1 and metadata["output_name"]:
            raise Exception("'output_name' cannot be specified when multiple input files are provided")

        # Don't specify output filenames, as there will be many
        metadata["output_filenames"] = []

        # Ensure that the paths of all the inputs are included as search paths
        for input_filename in metadata["inputs"]:
            dirname = os.path.dirname(input_filename)
            if dirname not in metadata["paths"]:
                metadata["paths"].append(dirname)

        if not metadata["include_tcl"]:
            metadata["excludes"] += [ "tkconstants", "tkinter", "tcl", ]
        del metadata["include_tcl"]

        return super(DistutilsCompilerImpl, cls)._CreateContext(metadata)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _InvokeImpl(cls, invoke_reason, context, status_stream, verbose_stream, verbose):
        with status_stream.DoneManager(associated_stream=verbose_stream) as (this_dm, this_verbose_stream):
            generated_python_context = cls._GenerateScriptContent(context)
            assert generated_python_context

            temp_filename = CurrentShell.CreateTempFilename(".py")
            with open(temp_filename, 'w') as f:
                f.write(generated_python_context)

            if context["preserve_temp_dir"]:
                this_dm.stream.write("Writing to '{}'\n".format(temp_filename))
                cleanup_func = lambda: None
            else:
                cleanup_func = lambda: os.remove(temp_filename)

            try:
                sink = six.moves.StringIO()

                this_dm.result = cls._Compile(context, temp_filename, StreamDecorator([ sink, this_verbose_stream, ]))
                if this_dm.result != 0:
                    if not verbose:
                        this_dm.stream.write(sink.getvalue())

                return this_dm.result

            finally:
                if this_dm.result == 0:
                    cleanup_func()

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _GenerateScriptContent(context):
        """
        Returns python code in a string that is written to a temporary file which is then
        passed to _Compile.
        """
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _Compile(context, script_filename, output_stream):
        """Returns a result code"""
        raise Exception("Abstract method")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def CreateCompileMethod(compiler_type):
    
    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    @CommandLine.Constraints( input=CommandLine.FilenameTypeInfo(arity='+'),
                              output_dir=CommandLine.DirectoryTypeInfo(ensure_exists=False),
                              output_name=CommandLine.StringTypeInfo(arity='?'),
                              build_type=CommandLine.EnumTypeInfo([ "console", "windows", ], arity='?'),
                              manifest_filename=CommandLine.FilenameTypeInfo(arity='?'),
                              icon_filename=CommandLine.FilenameTypeInfo(arity='?'),
                              path=CommandLine.DirectoryTypeInfo(arity='*'),
                              include_module=CommandLine.StringTypeInfo(arity='*'),
                              exclude_module=CommandLine.StringTypeInfo(arity='*'),
                              package=CommandLine.StringTypeInfo(arity='*'),
                              distutil_arg=CommandLine.StringTypeInfo(arity='*'),
                              
                              comments=CommandLine.StringTypeInfo(arity='?'),
                              company_name=CommandLine.StringTypeInfo(arity='?'),
                              file_description=CommandLine.StringTypeInfo(arity='?'),
                              internal_name=CommandLine.StringTypeInfo(arity='?'),
                              copyright=CommandLine.StringTypeInfo(arity='?'),
                              trademark=CommandLine.StringTypeInfo(arity='?'),
                              name=CommandLine.StringTypeInfo(arity='?'),
                              version=CommandLine.StringTypeInfo(arity='?'),
    
                              output_stream=None,
                            )
    def Compile( input,
                 output_dir,
                 output_name=None,
                 build_type="console",
                 include_tcl=False,
                 no_optimize=False,
                 no_bundle=False,
                 manifest_filename=None,
                 icon_filename=None,
                 path=None,
                 include_module=None,
                 exclude_module=None,
                 package=None,
                 distutil_arg=None,
    
                 comments=None,
                 company_name=None,
                 file_description=None,
                 internal_name=None,
                 trademark=None,
                 copyright=None,
                 name=None,
                 version=None,
    
                 preserve_temp_dir=False,
    
                 output_stream=sys.stdout,
                 no_verbose=False,
               ):
        """Creates an executable from one or more python files."""
        
        if build_type == "console":
            build_type = DistutilsCompilerImpl.BuildType.Console
        elif build_type == "windows":
            build_type = DistutilsCompilerImpl.BuildType.Windows
        else:
            assert False, build_type
    
        return CommandLineCompile( compiler_type,
                                   input,
                                   output_stream,
                                   verbose=not no_verbose,
    
                                   # Generate compiler options
                                   output_dir=output_dir,
                                   
                                   # This compiler options
                                   preserve_temp_dir=preserve_temp_dir,
                                   build_type=build_type,
                                   include_tcl=include_tcl,
                                   no_optimize=no_optimize,
                                   no_bundle=no_bundle,
                                   manifest_filename=manifest_filename,
                                   icon_filename=icon_filename,
                                   paths=path,
                                   includes=include_module,
                                   excludes=exclude_module,
                                   packages=package,
                                   distutil_args=distutil_arg,
                                   output_name=output_name,
    
                                   comments=comments,
                                   company_name=company_name,
                                   file_description=file_description,
                                   internal_name=internal_name,
                                   copyright=copyright,
                                   trademark=trademark,
                                   name=name,
                                   version=version,
                                 )

    # ----------------------------------------------------------------------

    return Compile
    
# ----------------------------------------------------------------------
def CreateCleanMethod(compiler_type):
    
    # ----------------------------------------------------------------------
    @CommandLine.EntryPoint
    @CommandLine.Constraints( output_dir=CommandLine.DirectoryTypeInfo(),
                              output_stream=None,
                            )
    def Clean( output_dir,
               output_stream=sys.stdout,
             ):
        """Cleans previously compiled output."""
        return CommandLineClean(output_dir, output_stream)
    
    # ----------------------------------------------------------------------

    return Clean
