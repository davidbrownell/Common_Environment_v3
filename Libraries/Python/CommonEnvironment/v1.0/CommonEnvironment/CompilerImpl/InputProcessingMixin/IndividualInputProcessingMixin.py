# ----------------------------------------------------------------------
# |  
# |  IndividualInputProcessingMixin.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 14:22:17
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the IndividualInputProcessingMixin object"""

import os
import sys

from CommonEnvironment.Interface import override, mixin
from CommonEnvironment.CompilerImpl.InputProcessingMixin import InputProcessingMixin

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# <Too few public methods> pylint: disable = R0903
@mixin
class IndividualInputProcessingMixin(InputProcessingMixin):
    """Each input is processed in isolation."""

    AttributeName                           = "input"

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GenerateMetadataItemsImpl(cls, invocation_group_inputs, metadata):
        if cls.AttributeName in metadata:
            raise Exception("'{}' is a reserved keyword".format(cls.AttributeName))

        for input in invocation_group_inputs:
            metadata[cls.AttributeName] = input
            yield metadata

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetInputItems(cls, context):
        return [ context[cls.AttributeName], ]
