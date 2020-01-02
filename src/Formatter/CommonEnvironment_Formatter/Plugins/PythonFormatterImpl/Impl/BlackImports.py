# ----------------------------------------------------------------------
# |
# |  BlackImports.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-09-08 12:54:43
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019-20
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains types helpful when using black"""

import os
import sys

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

if sys.version_info[0] == 2:
    black = None
    python_symbols = None
    python_tokens = None
else:
    sys.path.insert(0, os.path.join(_script_dir, "black"))
    with CallOnExit(lambda: sys.path.pop(0)):
        from PythonFormatterImpl.Impl.black import black

        import PythonFormatterImpl.Impl.black.blib2to3.pygram

        PythonFormatterImpl.Impl.black.blib2to3.pygram.initialize()

        from PythonFormatterImpl.Impl.black.blib2to3.pygram import python_symbols
        from PythonFormatterImpl.Impl.black.blib2to3.pygram import token as python_tokens
