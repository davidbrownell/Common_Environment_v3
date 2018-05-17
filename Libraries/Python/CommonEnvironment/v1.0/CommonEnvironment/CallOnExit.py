# ----------------------------------------------------------------------
# |  
# |  CallOnExit.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-20 19:03:11
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the `CallOnExit` method"""

import os
import sys
import textwrap
import traceback

from contextlib import contextmanager

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class CallOnExitException(Exception):
    """Exception thrown after `CallOnExit` encounters an exception when calling a functor."""

    def __init__(self):
        super(CallOnExitException, self).__init__("")

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
@contextmanager
def CallOnExit(*arguments):
    """
    Calls a method or methods when __exit__ is called.

    Args:
        arguments:  Any of the following
                        - functor (def Func()) [+]
                        - error stream (stream-like) [1]
                        - style (bool) [1]
                            . True: call only if successful
                            . False: call only if exceptional
                            . Default is call always
    """

    functors = []
    stream = None
    style = None

    for argument in arguments:
        if isinstance(argument, bool):
            if style is not None:
                raise Exception("Only 1 bool arg can be specified")

            style = argument

        elif hasattr(argument, "write") and callable(argument.write):
            if stream is not None:
                raise Exception("Only 1 stream arg can be specified")

            stream = argument

        else:
            functors.append(argument)

    stream = stream or sys.stderr
    is_successful = True

    try:
        yield

    except:
        is_successful = False
        raise

    finally:
        if style in [ None, is_successful, ]:
            inner_exceptions = []

            for functor in functors:
                try:
                    functor()
                except:
                    inner_exceptions.append('\n'.join([ "    {}".format(line) for line in traceback.format_exc().split('\n') ]))

            if inner_exceptions:
                stream.write(textwrap.dedent(
                    """

                    ERROR while attempting to unwind stack in CallOnExit.

                    {}

                    """).format('\n'.join(inner_exceptions).rstrip()))

                raise CallOnExitException()
