# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-20 19:28:09
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains types and methods that are fundamental"""

import datetime
import os
import re
import sys
import time

from collections import OrderedDict
from contextlib import contextmanager

import six

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
def ThisFullpath():
    """Returns the filename of the caller, taking into account symlinks and frozen executables."""

    if "python" not in sys.executable.lower():
        return sys.executable

    import inspect
    
    if sys.version_info[0] == 2:
        frame = inspect.stack()[1][0]
        filename = inspect.getframeinfo(frame).filename
    else:
        filename = os.path.realpath(os.path.abspath(inspect.stack()[1].filename))

    assert os.path.exists(filename), filename

    if os.path.islink(filename):
        filename = os.readlink(filename)

    return filename

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
        unique_id = (id(item), type(item))

    if unique_id in _describe_stack:
        # Display this value in a way that is similar to what is done inline so that normalization
        # functions normalize this value too.
        output_stream.write("The item '<<<id>>> : {} {}' has already been described.\n".format(id(item), type(item)))
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
                    result = kwargs[key](item[key])
                    
                    if result is not None:
                        output_stream.write("{}\n".format(result))
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
def ObjectToDict(obj, include_id=True):
    """Converts an object into a dict."""

    kvps = []

    if include_id:
        kvps.append(( "<<<id>>>", id(obj) ))

    keys = [ k for k in dir(obj) if not k.startswith("__") ]
    kvps += [ ( k, getattr(obj, k) ) for k in keys ]
    
    return OrderedDict(kvps)

# ----------------------------------------------------------------------
def ObjectReprImpl( obj, 
                    include_methods=False,
                    include_private=False,
                    include_id=True,
                    **kwargs                            # { "<attribute_name>" : def Func(<attribute_value>) -> string, ... }
                  ):
    """\
    Implementation of an object's __repr__ method.

    Example:
        def __repr__(self):
            return CommonEnvironment.ObjReprImpl(self)
    """
    
    d = ObjectToDict(obj, include_id=include_id)

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

# ----------------------------------------------------------------------
def NormalizeObjectReprOutput(output):
    """\
    Remove id specific information from the __repr__ output of an object so
    that it can be compared with another object.
    """

    # ----------------------------------------------------------------------
    def Sub(match):
        return "{} : __scrubbed_id__ {}".format( match.group("prefix"),
                                                 match.group("suffix"),
                                               )

    # ----------------------------------------------------------------------

    return re.sub( r"(?P<prefix>\<\<\<id\>\>\>\s*?) : (?P<id>\d+) (?P<suffix>[^\n]*?)",
                   Sub,
                   output,
                 )
