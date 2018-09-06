# ----------------------------------------------------------------------
# |  
# |  AlwaysInvocationQueryMixin.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 20:12:01
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the AlwaysInvocationQueryMixin object"""

import os
import sys

from CommonEnvironment.Interface import override, mixin
from CommonEnvironment.CompilerImpl.InvocationQueryMixin import InvocationQueryMixin

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@mixin
class AlwaysInvocationQueryMixin(InvocationQueryMixin):
    """Always invoke"""

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetInvokeReasonImpl(cls, context, output_stream):
        return cls.InvokeReason.Always

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _PersistContextImpl(context):
        pass
