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

from CommonEnvironment.CompilerImpl.InputProcessingMixin import InputProcessingMixin

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class AtomicInputProcessingMixin(InputProcessingMixin):
    """All inputs are grouped together as a single group."""

    AttributeName                           = "inputs"

    # ----------------------------------------------------------------------
    @classmethod
    def _GenerateMetadataItemsImpl(cls, invocation_group_inputs, metadata):
        if cls.AttributeName in user_provided_metadata:
            raise Exception("'{}' is a reserved keyword".format(cls.AttributeName))

        metadata[cls.AttributeName] = invocation_group_inputs
        yield metadata

    # ----------------------------------------------------------------------
    @classmethod
    def _GetInputItemsImpl(cls, context):
        return context[cls.AttributeName]
