# ----------------------------------------------------------------------
# |  
# |  SingleOutputMixin.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-31 17:28:26
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the SingleOutputMixin object"""

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
class SingleOutputMixin(OutputMixin):
    """Mixin for compilers that generate a single file"""

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetRequiredContextItems(cls):
        return [ "output_filename",
               ] + super(SingleOutputMixin, cls)._GetRequiredContextItems()

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _CreateContext(cls, metadata):
        metadata["output_filename"] = os.path.realpath(metadata["output_filename"])

        FileSystem.MakeDirs(os.path.dirname(metadata["output_filename"]))

        return super(SingleOutputMixin, cls)._CreateContext(metadata)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetOutputItems(context):
        return [ context["output_filename"], ]

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _CleanImplEx(cls, context, output_stream):
        if context["output_filename"] not in cls.GetInputItems(context) and os.path.isfile(context["output_filename"]):
            output_stream.write("Removing '{}'...".format(context["output_filename"]))
            with StreamDecorator(output_stream).DoneManager():
                FileSystem.RemoveFile(context["output_filename"])

        return super(SingleOutputMixin, cls)._CleanImplEx(context, output_stream)
