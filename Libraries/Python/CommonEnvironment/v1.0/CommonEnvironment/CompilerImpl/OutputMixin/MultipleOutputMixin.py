# ----------------------------------------------------------------------
# |  
# |  MultipleOutputMixin.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-31 17:35:39
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the MultipleOutputMixin object"""

import os
import sys

from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import override, mixin
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironment.CompilerImpl.OutputMixin import OutputMixin

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@mixin
class MultipleOutputMixin(OutputMixin):
    """Mixin for compilers that generate multiple output files"""

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetRequiredContextNames(cls):
        return [ "output_filenames",
               ] + super(MultipleOutputMixin, cls)._GetRequiredContextNames()

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _CreateContext(cls, metadata):
        for index, output_filename in enumerate(metadata["output_filenames"]):
            metadata["output_filenames"][index] = os.path.realpath(output_filename)
            FileSystem.MakeDirs(os.path.dirname(metadata["output_filenames"][index]))

        return super(MultipleOutputMixin, cls)._CreateContext(metadata)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetOutputItems(context):
        return context["output_filenames"]

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _CleanImplEx(cls, context, output_stream):
        output_stream = StreamDecorator(output_stream)
        input_items = set(cls.GetInputItems(context))

        for output_filename in context["output_filenames"]:
            if output_filename in input_items:
                continue

            if os.path.isfile(output_filename):
                output_stream.write("Removing '{}'...".format(output_filename))
                with output_stream.DoneManager():
                    FileSystem.RemoveFile(output_filename)

        return super(MultipleOutputMixin, cls)._CleanImplEx(context, output_stream)
