# ----------------------------------------------------------------------
# |
# |  DoesNotExist_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.db@DavidBrownell.com>
# |      2022-05-10 09:10:12
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for DoesNotExist.py"""

import os

from typing import Dict, Optional, Union

import CommonEnvironment

from CommonEnvironmentEx.Package import InitRelativeImports

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

with InitRelativeImports():
    from ..DoesNotExist import *


# ----------------------------------------------------------------------
def test_Standard():
    d: Dict[str, Optional[str]] = {
        "FOO": None,
        "BAR": "bar"
    }

    assert d.get("FOO", None) is None
    assert d.get("not in dict", DoesNotExist.instance) is DoesNotExist.instance


# ----------------------------------------------------------------------
def test_ParameterDefault():
    # ----------------------------------------------------------------------
    def Func(
        value: Union[None, str, DoesNotExist]=DoesNotExist.instance,
    ):
        return value

    # ----------------------------------------------------------------------

    assert Func(None) is None
    assert Func("value") == "value"
    assert Func() is DoesNotExist.instance
