# ----------------------------------------------------------------------
# |  
# |  AtomicInputProcessingMixin.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 14:16:19
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the AtomicInputProcessingMixin object"""

import os
import sys

from CommonEnvironment.Interface import override, mixin
from CommonEnvironment.CompilerImpl.InputProcessingMixin import InputProcessingMixin

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@mixin
class AtomicInputProcessingMixin(InputProcessingMixin):
    """All inputs are grouped together as a single group."""

    AttributeName                           = "inputs"

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GenerateMetadataItemsImpl(cls, invocation_group_inputs, metadata):
        if cls.AttributeName in metadata:
            raise Exception("'{}' is a reserved keyword".format(cls.AttributeName))

        metadata[cls.AttributeName] = invocation_group_inputs
        yield metadata

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetInputItems(cls, context):
        return context[cls.AttributeName]
