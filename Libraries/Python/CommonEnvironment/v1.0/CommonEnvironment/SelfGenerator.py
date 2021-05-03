# ----------------------------------------------------------------------
# |
# |  SelfGenerator.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-05-03 10:20:39
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the SelfGenerator decorator"""

from functools import wraps
import os

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class SelfGenerator(object):
    """\
    Generator decorator for generators with a self parameter.

    This code is based off of https://stackoverflow.com/questions/21808113/is-there-anything-similar-to-self-inside-a-python-generator.

    Example:

        @SelfGenerator
        def A(self):
        while True:
            message = yield
            print(self is message)

            a = A()
            b = A()
            a.send(a)  # outputs True
            a.send(b)  # outputs False
    """

    # ----------------------------------------------------------------------
    def __new__(cls, func):
        # ----------------------------------------------------------------------
        @wraps(func)
        def Decorated(*args, **kwargs):
            obj = object.__new__(cls)
            obj.__init__(func, args, kwargs)

            return obj

        # ----------------------------------------------------------------------

        return Decorated

    # ----------------------------------------------------------------------
    def __init__(self, generator, args, kwargs):
        self._generator = generator(self, *args, **kwargs)

    # ----------------------------------------------------------------------
    def __iter__(self):
        return self

    # ----------------------------------------------------------------------
    def __next__(self):
        return next(self._generator)

    next = __next__

    # ----------------------------------------------------------------------
    def send(self, value):
        return self._generator.send(value)
