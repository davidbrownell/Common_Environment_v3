# ----------------------------------------------------------------------
# |
# |  DoesNotExist.py
# |
# |  David Brownell <db@DavidBrownell.db@DavidBrownell.com>
# |      2022-05-10 09:04:18
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the DoesNotExist object"""

import os

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
class DoesNotExist(object):  # pylint: disable=too-few-public-methods
    """\
    Unique object to distinguish from None during lookup operations where None is a valid value.

    For Example:
        d: Dict[str, Optional[str] = {
            "Foo": None,
            "Bar": "Bar",
        }

        # Before
        if d.get("Foo", None) is None:
            d["Foo"] = "new foo value"      # Potential error, as we are overwriting a valid value

        # After
        if d.get("Foo", DoesNotExist.instance) is DoesNotExist.instance:
            raise Exception("This will never happen")
    """

    # Set below
    instance: "DoesNotExist"                = None  # type: ignore


DoesNotExist.instance                       = DoesNotExist()
