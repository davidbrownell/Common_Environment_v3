# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-20 19:28:09
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains types and methods that are fundamental"""

import datetime
import os
import sys
import time

from collections import OrderedDict
from contextlib import contextmanager

import six

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Nonlocals(object):
    """
    Python 2.7 compatible replacement for the nonlocal keyword.

    Example:
        nonlocals = Nonlocals(x=10, y=20)

        def Foo():
            nonlocals.x = 30
            nonlocals.y = 40

        Foo()

        # nonlocals.x == 30
        # nonlocals.y == 40
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
# Data type used to short-circuit infinite loops when attempting to describe
# object with circular dependencies. 
_describe_stack                             = set()

def Describe( item,                         # str, dict, iterable, obj
              output_stream=sys.stdout,
              unique_id=None,
              **kwargs                      # { "<attribute_name>" : def Func(<attribute_value>) -> string, ... }
            ):
    """Writes information about the item to the provided stream."""

    if unique_id is None:
        unique_id = (type(item), id(item))

    if unique_id in _describe_stack:
        output_stream.write("The item '{}' has already been described.\n".format(unique_id))
        return

    _describe_stack.add(unique_id)

    try:
        # ----------------------------------------------------------------------
        def OutputDict(item, indentation_str):
            if not item:
                output_stream.write("-- empty dict --\n")
                return

            if hasattr(item, "_asdict"):
                item = item._asdict()

            keys = OrderedDict([ (key, key if isinstance(key, six.string_types) else str(key)) for key in item.keys() ])

            max_length = 0
            for key in six.itervalues(keys):
                max_length = max(max_length, len(key))

            item_indentation_str = indentation_str + (' ' * (max_length + len(" : ")))
            
            for index, (key, key_name) in enumerate(six.iteritems(keys)):
                output_stream.write("{0}{1:<{2}} : ".format( indentation_str if index else '',
                                                             key_name,
                                                             max_length,
                                                           ))

                if key in kwargs:
                    output_stream.write("{}\n".format(kwargs[key](item[key])))
                else:
                    Impl(item[key], item_indentation_str)

        # ----------------------------------------------------------------------
        def OutputList(item, indentation_str):
            if not item:
                output_stream.write("-- empty list --\n")
                return

            item_indentation_str = indentation_str + (' ' * 5)

            for index, i in enumerate(item):
                output_stream.write("{0}{1:<5}".format( indentation_str if index else '',
                                                        "{})".format(index),
                                                      ))
                Impl(i, item_indentation_str)

        # ----------------------------------------------------------------------
        def Impl(item, indentation_str):
            if isinstance(item, six.string_types):
                output_stream.write("{}\n".format(('\n{}'.format(indentation_str)).join(item.split('\n'))))
            elif isinstance(item, dict):
                OutputDict(item, indentation_str)
            elif isinstance(item, list):
                OutputList(item, indentation_str)
            else:
                # ----------------------------------------------------------------------
                def Display():
                    try:
                        # Is the item iterable?
                        potential_attribute_name = next(iter(item))
                    except (TypeError, IndexError, StopIteration):
                        # Not iterable
                        return False

                    # Is the item dict-like?
                    try:
                        ignore_me = item[potential_attribute_name]
                        OutputDict(item, indentation_str)
                    except (TypeError, IndexError):
                        # No, it isn't
                        OutputList(item, indentation_str)

                    return True

                # ----------------------------------------------------------------------

                if not Display():
                    content = str(item).strip()
                    
                    if "<class" not in content:
                        content += "{}{}".format( '\n' if content.count('\n') > 1 else ' ',
                                                  type(item),
                                                )
                    
                    if " object at " in content:
                        content += "\n\n{}".format(ObjectReprImpl(item))
                    
                    output_stream.write("{}\n".format(('\n{}'.format(indentation_str)).join(content.split('\n'))))

        # ----------------------------------------------------------------------

        Impl(item, '')
        output_stream.write('\n\n')

    finally:
        _describe_stack.remove(unique_id)

# ----------------------------------------------------------------------
def ObjectToDict(obj):
    """Converts an object into a dict."""

    keys = [ k for k in dir(obj) if not k.startswith("__") ]
    return { k : getattr(obj, k) for k in keys }

# ----------------------------------------------------------------------
def ObjectReprImpl( obj, 
                    include_methods=False,
                    include_private=False,
                    **kwargs                # { "<attribute_name>" : def Func(<attribute_value>) -> string, ... }
                  ):
    """\
    Implementation of an object's __repr__ method.

    Example:
        def __repr__(self):
            return CommonEnvironment.ObjReprImpl(self)
    """
    
    d = ObjectToDict(obj)
    
    # Displaying builtins prevents anything from being displayed after it
    if "f_builtins" in d:
        del d["f_builtins"]
    
    for k, v in list(six.iteritems(d)):
        if callable(v):
            if include_methods:
                d[k] = "callable"
            else:
                del d[k]
                continue
        
        if not include_private and k.startswith('_'):
            del d[k]
            continue

    sink = six.moves.StringIO()
    Describe( d, 
              sink, 
              unique_id=(type(obj), id(obj)),
              **kwargs
            )

    return "{}\n{}\n".format(type(obj), sink.getvalue().rstrip())
