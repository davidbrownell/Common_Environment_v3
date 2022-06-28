# ----------------------------------------------------------------------
# |
# |  Compare.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2022-06-27 11:11:08
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2022
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Compare function"""

import os

from enum import Enum
from typing import Any

import CommonEnvironment
from CommonEnvironment import Interface

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
def Compare(
    a: Any,
    b: Any,
    *,
    compare_across_types: bool=False,
) -> int:
    """Compares 2 instances, taking some of python's wonky comparison differences into account"""

    if a is None or b is None:
        if a is None and b is None:
            return 0
        if a is None:
            return -1
        if b is None:
            return 1

    type_a = type(a)
    type_b = type(b)

    if type_a != type_b and not compare_across_types:
        return Compare(type_a.__name__, type_b.__name__)

    if type_a.__name__ != "str" and type_b.__name__ != "str":
        # Attempt to compare by iterator
        try:
            a_iter = iter(a)
            b_iter = iter(b)

            while True:
                try:
                    a_value = next(a_iter)
                except StopIteration:
                    a_value = _internal_does_not_exist

                try:
                    b_value = next(b_iter)
                except StopIteration:
                    b_value = _internal_does_not_exist

                if a_value is _internal_does_not_exist or b_value is _internal_does_not_exist:
                    if a_value is _internal_does_not_exist and b_value is _internal_does_not_exist:
                        return 0

                    if a_value is _internal_does_not_exist:
                        return -1
                    if b_value is _internal_does_not_exist:
                        return 1

                result = Compare(a_value, b_value)
                if result != 0:
                    return result

            assert False, "We will never get here"  # pragma: no cover

        except TypeError:
            # They aren't iterators
            pass

    # Compare methods
    compare_func = getattr(a, "Compare", None)
    if compare_func is not None:
        # Invoke a static or class method if necessary
        if (
            Interface.IsStaticMethod(compare_func)
            or Interface.IsClassMethod(compare_func)
        ):
            return compare_func(a, b)

        assert Interface.IsStandardMethod(compare_func), compare_func
        return compare_func(b)

    if issubclass(type_a, Enum) and issubclass(type_b, Enum):
        a = a.value
        b = b.value

    # Standard compare
    if a < b:
        return -1
    if a > b:
        return 1

    return 0


# ----------------------------------------------------------------------
# |
# |  Internal Types
# |
# ----------------------------------------------------------------------
class _InternalDoesNotExist(object):
    pass


# ----------------------------------------------------------------------
# |
# |  Internal Data
# |
# ----------------------------------------------------------------------
_internal_does_not_exist                    = _InternalDoesNotExist()
