# ----------------------------------------------------------------------
# |
# |  AutomatedTestHelpers.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-08-12 10:33:03
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Functionality that is helpful when writing automated tests"""

import inspect
import os
import textwrap

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
def ResultsFromFile(
    suffix: str=None,
    subdir: str="Results",
) -> str:
    """\
    Returns results saved to a file.

    The results are expected to be stored in a file with the name:

        Results/<basename>.<testname>.txt
        Results/<basename>.<classname>.<testname>.txt

        Results/<basename>.<testname><suffix>.txt
        Results/<basename>.<classname>.<testname><suffix>.txt
    """

    # Create the filename
    caller = inspect.getouterframes(inspect.currentframe(), 2)[1]

    testname = caller.function

    self_value = caller.frame.f_locals.get("self", None)
    if self_value is not None:
        testname = "{}.{}".format(self_value.__class__.__name__, testname)

    dirname, basename = os.path.split(caller.filename)
    basename = os.path.splitext(basename)[0]

    fullpath = os.path.realpath(
        os.path.join(
            dirname,
            subdir,
            "{}.{}{}.txt".format(
                basename,
                testname,
                suffix or "",
            ),
        ),
    )

    if not os.path.isfile(fullpath):
        return textwrap.dedent(
            """\
            ********************************************************************************
            ********************************************************************************
            ********************************************************************************

            The filename does not exist:

                {}

            ********************************************************************************
            ********************************************************************************
            ********************************************************************************
            """,
        ).format(fullpath)

    with open(fullpath) as f:
        return f.read()
