# ----------------------------------------------------------------------
# |  
# |  EnvironmentHelpers.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-31 21:19:14
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Methods that help when working with the environment and environment variables"""

import os
import re
import sys

import six

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
def PopulateEnvironmentVars( s, 
                             _placeholder_prefix="${",
                             _placeholder_suffix="}",
                             **additional_args
                           ):
    """
    Will replace placeholders in the form '${var}' in the given string with
    the value in the current environment.

    This can be helpful when populating metadata/context items.
    """

    placeholder = "<!!--__"
    
    additional_args_lower = {}
    for k, v in six.iteritems(additional_args):
        additional_args_lower[k.lower()] = v

    environ_lower = {}
    for k, v in six.iteritems(os.environ):
        environ_lower[k.lower()] = v

    regex = re.compile(r"{prefix}(?P<var>.+?){suffix}".format( prefix=re.escape(_placeholder_prefix),
                                                               suffix=re.escape(_placeholder_suffix),
                                                             ))

    # ----------------------------------------------------------------------
    def Sub(match):
        var = match.group("var").lower()

        if var in additional_args_lower:
            return additional_args_lower[var]

        if var in environ_lower:
            return environ_lower[var]

        # Match wasn't found. Give it a placeholder so we don't keep trying
        # to evaluate it.
        return match.string[match.start() : match.end()].replace(_placeholder_prefix, placeholder)

    # ----------------------------------------------------------------------

    # Recursively apply placeholders
    while _placeholder_prefix in s:
        s = regex.sub(Sub, s)

    return s.replace(placeholder, _placeholder_prefix)
