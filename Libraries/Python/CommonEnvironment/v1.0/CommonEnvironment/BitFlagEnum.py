# ----------------------------------------------------------------------
# |  
# |  BitFlagEnum.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-07-09 20:01:05
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the BitFlagEnum object"""

import os
import sys

from enum import IntFlag, auto as auto_func

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

auto                                        = auto_func

# ----------------------------------------------------------------------
class BitFlagEnum(IntFlag):
    """\
    Enum class that ensures auto values are set as unique bits.

    Example:
        >>> class MyFlag(BitFlagEnum):
            Value1 = auto()
            Value2 = auto()
            Value3 = auto()
        
        >>> MyFlag.Value1.value
        1
        >>> MyFlag.Value2.value
        2
        >>> MyFlag.Value3.value
        4
        >>> (MyFlag.Value1 | MyFlag.Value3).value
        5
    """

    # ----------------------------------------------------------------------
    def _generate_next_value_(name, start, count, last_values):
        return 1 << count
