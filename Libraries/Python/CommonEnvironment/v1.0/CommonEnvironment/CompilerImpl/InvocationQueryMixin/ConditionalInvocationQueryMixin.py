# ----------------------------------------------------------------------
# |  
# |  ConditionalInvocationQueryMixin.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 20:16:44
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the ConditionalInvocationQueryMixin object"""

import base64
import inspect
import os
import stat
import sys
import textwrap

import inflect as inflect_mod
import six
import six.moves.cPickle as pickle

from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import extensionmethod, override, mixin
from CommonEnvironment import RegularExpression

from CommonEnvironment.CompilerImpl.InvocationQueryMixin import InvocationQueryMixin

from CommonEnvironment.TypeInfo.FundamentalTypes.DirectoryTypeInfo import DirectoryTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
@mixin
class ConditionalInvocationQueryMixin(InvocationQueryMixin):

    # Derived classes can override this value to potentially force generation
    AlwaysGenerate                          = False

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetOptionalMetadata(cls):
        return [ ( "force", False ),
                 ( "output_data_filename_prefix", '' ),
               ] + super(ConditionalInvocationQueryMixin, cls)._GetOptionalMetadata()

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetRequiredContextNames(cls):
        return [ "output_dir",
               ] + super(ConditionalInvocationQueryMixin, cls)._GetRequiredContextNames()

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _CreateContext(cls, metadata):
        metadata["output_dir"] = os.path.realpath(metadata["output_dir"])

        FileSystem.MakeDirs(metadata["output_dir"])

        return super(ConditionalInvocationQueryMixin, cls)._CreateContext(metadata)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetInvokeReasonImpl(cls, context, output_stream):

        prev_info, prev_modified_time = _PersistedInfo.Load(cls, context, output_stream)
        
        # Don't persist force
        force = context["force"]
        del context["force"]

        # Check the basic reasons
        for invoke_reason, desc, functor in [ ( cls.InvokeReason.Force, "force was specified", lambda: force ),
                                              ( cls.InvokeReason.PrevContextMissing, "previous context is missing", lambda: not prev_info ),
                                            ]:
            if functor():
                output_stream.write("\nInvoking because {}.\n\n".format(desc))
                return invoke_reason

        # Check calculated reasons
        # ----------------------------------------------------------------------
        def HaveGeneratorFilesBeenModified():
            
            # ----------------------------------------------------------------------
            def CheckObject(obj):
                if not isinstance(obj, type):
                    obj = type(obj)

                try:
                    for class_ in inspect.getmro(obj):
                        try:
                            filename = inspect.getfile(class_)

                            # The file may not exist if we are working with a bundled distribution
                            if not os.path.isfile(filename):
                                continue

                            if cls._GetModifiedTime(filename) > prev_modified_time:
                                return filename

                        except TypeError:
                            # Will be raised when attempting to get a file associated with a builtin
                            pass

                except:
                    output_stream.write("ERROR attempting to get the bases for '{}'".format(obj.Name))
                    raise

                return None

            # ----------------------------------------------------------------------

            result = CheckObject(cls)
            if result is not None:
                return result

            for item in cls._GetAdditionalGeneratorItems(context):
                if isinstance(item, six.string_types):
                    if cls._GetModifiedTime(item) > prev_modified_time:
                        return item
                else:
                    result = CheckObject(item)
                    if result is not None:
                        return result

            return None

        # ----------------------------------------------------------------------
        def AreGeneratedItemsMissing():
            for fullpath in cls._GetOutputItems(context):
                if not os.path.exists(fullpath):
                    return fullpath

            return None

        # ----------------------------------------------------------------------
        def HaveOutputsChanged():
            return cls._GetOutputItems(context) != prev_info.OutputItems

        # ----------------------------------------------------------------------
        def HaveInputsChanged():
            return cls._GetInputItems(context) != prev_info.InputItems

        # ----------------------------------------------------------------------
        def HaveInputsBeenModified():
            # If the compiler is based on directories, see if there is anything in the
            # directory that has changed.
            if isinstance(cls.InputTypeInfo, FilenameTypeInfo):
                input_filenames = cls._GetInputItems(context)
            elif isinstance(cls.InputTypeInfo, DirectoryTypeInfo):
                input_filenames = []
                output_filenames = set(cls._GetOutputItems(context))

                for input_dir in cls._GetInputItems(context):
                    for item in os.listdir(input_dir):
                        fullpath = os.path.join(input_dir, item)
                        if not os.path.isfile(fullpath):
                            continue

                        if fullpath in output_filenames:
                            continue

                        input_filenames.append(fullpath)
            else:
                assert False, type(cls.InputTypeInfo)

            for input_filename in input_filenames:
                if not os.path.isfile(input_filename) or cls._GetModifiedTime(input_filename) > prev_modified_time:
                    return input_filename

            return None

        # ----------------------------------------------------------------------
        def HasMetadataChanged():
            prev_metadata_keys = [ key for key in six.iterkeys(prev_info.Context) if not key.startswith('_') ]

            for k, v in six.iteritems(context):
                if k.startswith('_'):
                    continue

                if k not in prev_metadata_keys:
                    return "'{}' has been added".format(k)

                if v != prev_info.Context[k]:
                    return "'{}' has been modified".format(k)

                prev_metadata_keys.remove(k)

            if prev_metadata_keys:
                return "{} {} removed".format( ', '.join([ "'{}'".format(key) for key in prev_metadata_keys ]),
                                               inflect.plural("has", len(prev_metadata_keys)),
                                             )

            return None

        # ----------------------------------------------------------------------
        def HasCustomMetadataChanged():
            return cls._CustomContextComparison(context, prev_info.Context)

        # ----------------------------------------------------------------------
        def ShouldGenerate():
            return getattr(cls, "AlwaysGenerate", None)

        # ----------------------------------------------------------------------

        for invoke_reason, desc_template, functor in [ ( cls.InvokeReason.NewerGenerators, "generator files have been modified ({result})", HaveGeneratorFilesBeenModified ),
                                                       ( cls.InvokeReason.DifferentOutput, "items to generate have changed", HaveOutputsChanged ),
                                                       ( cls.InvokeReason.MissingOutput, "items to generate are missing ({result})", AreGeneratedItemsMissing ),
                                                       ( cls.InvokeReason.DifferentInput, "input items have changed", HaveInputsChanged ),
                                                       ( cls.InvokeReason.NewerInput, "input has been modified ({result})", HaveInputsBeenModified ),
                                                       ( cls.InvokeReason.DifferentMetadata, "metadata has changed ({result}) [standard]", HasMetadataChanged ),
                                                       ( cls.InvokeReason.DifferentMetadata, "metadata has changed ({result}) [custom]", HasCustomMetadataChanged ),
                                                       ( cls.InvokeReason.OptIn, "the generator opted-in to generation", ShouldGenerate ),
                                                     ]:
            result = functor()
            if result:
                output_stream.write("\nInvoking because {}.\n\n".format(desc_template.format(result=result)))
                return invoke_reason

        return None
    
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _PersistContextImpl(cls, context):
        _PersistedInfo(cls, context).Save()

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _GetModifiedTime(filename):
        # When it comes to python files, we don't care when the file was compiled but rather
        # when the corresponding source file was modified. If passed a compiled file, look
        # at the corresponding .py file instead.
        if os.path.splitext(filename)[1].lower() in [ ".pyc", ".pyo", ]:
            filename = filename[:-1]
            if not os.path.isfile(filename):
                grandparent_dir = os.path.basename(os.path.dirname(filename))
                if grandparent_dir == "__pycache__":
                    dirname, basename = os.path.split(filename)
                    dirname = os.path.dirname(dirname)

                    filename = os.path.join(dirname, basename)

            assert os.path.isfile(filename), filename

        return os.stat(filename)[stat.ST_MTIME]

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def _CustomContextComparison(context, prev_context):
        """
        Opportunity for a compiler to perform custom comparison when determining if invocation should 
        continue. Returns a string describing mis-compare reasons (if any).
        """

        # No custom comparison by default
        return

    # ----------------------------------------------------------------------
    @staticmethod
    @extensionmethod
    def _GetAdditionalGeneratorItems(context):
        """
        Specify a list of additional filenames or objects that are used to implement 
        compilation functionality. Any changes to these files imply that all previously 
        generated content should be regenerated when invoked again.
        """

        # No additional generator files or items
        return []

# ----------------------------------------------------------------------
class _PersistedInfo(object):
    FILENAME                                = "Compiler.ConditionalInvocationQueryMixin.data"
    TEMPLATE                                = textwrap.dedent(
        """\
        - Generated by ConditionalInvocationQueryMixin to track context changes between
        - compilation invocations.
        -
        - ***** Please do not modify this file *****
        {data}
        """)

    # ----------------------------------------------------------------------
    @classmethod
    def Load(cls, compiler, context, output_stream):
        filename = cls._GetPersistedFilename(context)

        if os.path.isfile(filename):
            try:
                match = RegularExpression.TemplateStringToRegex(cls.TEMPLATE).match(open(filename).read())
                if match:
                    data = base64.b64decode(match.group("data"))
                    return pickle.loads(bytearray(data)), os.stat(filename)[stat.ST_MTIME]

            except:
                output_stream.write("WARNING: Context information associated with the previous compilation appears to be corrupt; new data will be generated.\n")

        return cls(compiler, context), 0

    # ----------------------------------------------------------------------
    def __init__(self, compiler, context):
        self.Context                        = context
        self.InputItems                     = compiler.GetInputItems(context)
        self.OutputItems                    = compiler.GetOutputItems(context)

    # ----------------------------------------------------------------------
    def Save(self):
        data = pickle.dumps(self)
        data = base64.b64encode(data)
        data = data.decode("utf-8")
        
        filename = self._GetPersistedFilename(self.Context)

        FileSystem.MakeDirs(os.path.dirname(filename))

        with open(filename, 'w') as f:
            f.write(self.TEMPLATE.format(data=data))

    # ----------------------------------------------------------------------
    @classmethod
    def _GetPersistedFilename(cls, context):
        return os.path.join(context["output_dir"], "{}{}".format(context["output_data_filename_prefix"], cls.FILENAME))
