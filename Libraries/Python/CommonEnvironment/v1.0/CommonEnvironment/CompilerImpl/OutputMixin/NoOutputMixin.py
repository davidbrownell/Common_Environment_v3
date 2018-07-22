# ----------------------------------------------------------------------
# |  
# |  NoOutputMixin.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 20:31:28
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the NoOutputMixin object"""

import os
import sys

from CommonEnvironment.Interface import override, mixin
from CommonEnvironment.CompilerImpl.OutputMixin import OutputMixin

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

@mixin
class NoOutputMixin(OutputMixin):
    """No output"""

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GetOutputItems(context):
        return []

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _CleanImplEx(context, output_stream):
        pass
