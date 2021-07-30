# ----------------------------------------------------------------------
# |
# |  DataclassDecorators.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-07-29 22:44:36
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Decorators that help when working with dataclass objects"""

import os

from typing import Any, Dict, Tuple

import wrapt

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
def DataclassDefaultValues(
    **kwargs: Any,
):
    """\
    Applies a default value for a dataclass member.

    Example:
        @DataclassDefaultValues(
            b=10,
        )
        @dataclass
        class MyDataClass(object):
            a: str
            b: int
            c: bool

        print(MyDataClass("hello", True))
        >>> Derived(a='hello', b=10, c=True)
    """

    default_values = kwargs

    # ----------------------------------------------------------------------
    class DoesNotExist(object):
        pass

    # ----------------------------------------------------------------------

    does_not_exist = DoesNotExist()

    # ----------------------------------------------------------------------
    @wrapt.decorator
    def Wrapper(
        wrapped: Any,
        instance: None,
        args: Tuple[Any],
        kwargs: Dict[str, Any],
    ):
        args_index = 0

        for attribute_name in wrapped.__dataclass_fields__.keys():
            if attribute_name in kwargs:
                continue

            potential_value = default_values.get(attribute_name, does_not_exist)
            if not isinstance(potential_value, DoesNotExist):
                kwargs[attribute_name] = potential_value
            else:
                if args_index == len(args):
                    continue

                kwargs[attribute_name] = args[args_index]
                args_index += 1

        return wrapped(**kwargs)

    # ----------------------------------------------------------------------

    return Wrapper
