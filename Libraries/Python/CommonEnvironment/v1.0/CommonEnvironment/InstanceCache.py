# ----------------------------------------------------------------------
# |
# |  InstanceCache.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-10-15 21:08:32
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Functionality to cache results on an object"""

import inspect
import os
import types

from typing import Any, Callable, Dict, List, Optional, Tuple

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
DEFAULT_ATTRIBUTE_NAME                      = "_instance_cache_original_funcs"
SKIP_CACHE_KWARG_NAME                       = "instance_cache_skip"


# ----------------------------------------------------------------------
class InstanceCache(object):
    # ----------------------------------------------------------------------
    @classmethod
    def __clsinit__(cls):
        setattr(cls, DEFAULT_ATTRIBUTE_NAME, {})

    # ----------------------------------------------------------------------
    def __init__(
        self,
        attribute_name: Optional[str]=None,
    ):
        if attribute_name is None:
            attribute_name = DEFAULT_ATTRIBUTE_NAME

        object.__setattr__(self, attribute_name, {})


# ----------------------------------------------------------------------
def InstanceCacheGet(
    method,
    cache_key_func: Optional[Callable[[Any, Tuple[Any, ...], Dict[str, Any]], Any]]=None,
    *,
    attribute_name: Optional[str]=None,
):
    """\
    Decorates the method or classmethod with a cache.

    Note that this process is not thread-safe.
    """

    if cache_key_func is None:
        cache_key_func = lambda self_or_cls, *args, **kwargs: method.__name__

    if attribute_name is None:
        attribute_name = DEFAULT_ATTRIBUTE_NAME

    # ----------------------------------------------------------------------
    def Getter(self_or_cls, *args, **kwargs):
        # If here, it means that we have not replaced the func yet.
        skip_cache = kwargs.pop(SKIP_CACHE_KWARG_NAME, False)

        result = method(self_or_cls, *args, **kwargs)

        if not skip_cache:
            # Replace the method with a new method that always returns this
            # value. Store information so that the original method can be restored
            # if explicitly reset.
            cached_methods = getattr(self_or_cls, attribute_name)
            cached_methods[method.__name__] = Getter

            # ----------------------------------------------------------------------
            def NewMethod(self_or_cls, *args, **kwargs):
                skip_cache = kwargs.pop(SKIP_CACHE_KWARG_NAME, False)
                if skip_cache:
                    return method(self_or_cls, *args, **kwargs)

                return result

            # ----------------------------------------------------------------------

            new_method = types.MethodType(NewMethod, self_or_cls)

            if inspect.isclass(self_or_cls):
                setattr(self_or_cls, method.__name__, new_method)
            else:
                object.__setattr__(self_or_cls, method.__name__, new_method)

        return result

    # ----------------------------------------------------------------------

    return Getter


# ----------------------------------------------------------------------
def InstanceCacheReset(
    method,
    *,
    attribute_name: Optional[str]=None,
    attributes_to_reset: Optional[List[str]]=None,
):
    if attribute_name is None:
        attribute_name = DEFAULT_ATTRIBUTE_NAME

    if attributes_to_reset is None:
        # ----------------------------------------------------------------------
        def GetAllCachedItems(cached_methods):
            yield from cached_methods.items()

        # ----------------------------------------------------------------------

        get_cached_keys_and_values_func = GetAllCachedItems

    else:
        assert attributes_to_reset
        attributes_to_reset_set = set(attributes_to_reset)

        # ----------------------------------------------------------------------
        def GetSomeCachedItems(cached_methods):
            for k, v in cached_methods.items():
                if k in attributes_to_reset_set:
                    yield k, v

        # ----------------------------------------------------------------------

        get_cached_keys_and_values_func = GetSomeCachedItems

    # ----------------------------------------------------------------------
    def Reset(self_or_cls, *args, **kwargs):
        # Invoke the function
        result = method(self_or_cls, *args, **kwargs)

        # Restore the original methods

        if inspect.isclass(self_or_cls):
            # ----------------------------------------------------------------------
            def ReplaceClassMethod(name, method):
                setattr(self_or_cls, name, method)

            # ----------------------------------------------------------------------

            replace_func = ReplaceClassMethod

        else:
            # ----------------------------------------------------------------------
            def ReplaceInstanceMethod(name, method):
                object.__setattr__(self_or_cls, name, method)

            # ----------------------------------------------------------------------

            replace_func = ReplaceInstanceMethod

        cached_methods = getattr(self_or_cls, attribute_name)

        for k, v in list(get_cached_keys_and_values_func(cached_methods)):
            replace_func(k, types.MethodType(v, self_or_cls))
            del cached_methods[k]

        return result

    # ----------------------------------------------------------------------

    return Reset


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class _DoesNotExist(object):
    pass
