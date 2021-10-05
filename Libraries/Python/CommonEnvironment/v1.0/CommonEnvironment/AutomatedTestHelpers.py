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

from typing import Optional

import CommonEnvironment

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
def ResultsFromFile(
    suffix: str=None,                       # Default is None
    subdir: str=None,                       # Default is "Results"
    file_ext: str=None,                     # Default is ".yaml"
    callstack_offset: int=0,
) -> str:
    """\
    Returns results saved to a file.

    The results are expected to be stored in a file with the name:

        Results/<basename>.<testname>.txt
        Results/<basename>.<classname>.<testname>.txt

        Results/<basename>.<testname><suffix>.txt
        Results/<basename>.<classname>.<testname><suffix>.txt
    """

    fullpath = _GetResultsFilename(suffix, subdir, file_ext, callstack_offset + 1)

    if not os.path.isfile(fullpath):
        return textwrap.dedent(
            """\
            ********************************************************************************
            ********************************************************************************
            ********************************************************************************

            WARNING:
                The filename does not exist:

                    {}

            ********************************************************************************
            ********************************************************************************
            ********************************************************************************
            """,
        ).format(fullpath)

    with open(fullpath) as f:
        return f.read()


# ----------------------------------------------------------------------
class ReallyReallyWantToDoThis(object):
    """\
    Overwriting the existing file content with the results provided is a risky operation, as we aren't
    actually validating the results of the test. Therefore, this class and the excessively long argument
    name are intended to prevent the unintended use of the functionality.

    This functionality should only be invoked when the format of the comparison output has changed,
    but not the functionality associated with the system under test. In other words, the format change
    should be done independent of any changes to the system under test.

    USE AT YOUR OWN RISK!
    """
    pass


def CompareResultsFromFile(
    results: str,
    *,
    suffix: str=None,                       # See `ResultsFromFile` for default values
    subdir: str=None,                       # See `ResultsFromFile` for default values
    file_ext: str=None,                     # See `ResultsFromFile` for default values
    overwrite_content_with_these_results: ReallyReallyWantToDoThis=None,    # See notes in `ReallyReallyWantToDoThis` above
):
    """\
    Compares the results provided with the results from a file on the filesystem (whose name is
    calculated based on the calling function's name).

    To use this functionality with pytest, include the following statements BEFORE this file is
    imported:

        import pytest
        pytest.register_assert_rewrite("CommonEnvironment.AutomatedTestHelpers")

    """

    if overwrite_content_with_these_results is not None:
        filename = _GetResultsFilename(suffix, subdir, file_ext, 1)
        assert os.path.isfile(filename), filename

        print(
            textwrap.dedent(
                """\
                ********************************************************************************
                ********************************************************************************
                ********************************************************************************

                WARNING:
                    File contents are being overwritten for:

                        {}

                ********************************************************************************
                ********************************************************************************
                ********************************************************************************
                """,
            ).format(filename),
        )

        with open(filename, "w") as f:
            f.write(results)

    assert results == ResultsFromFile(suffix, subdir, file_ext, 1)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _GetResultsFilename(
    suffix: Optional[str],
    subdir: Optional[str],
    file_ext: Optional[str],
    callstack_offset: int,
) -> str:
    if subdir is None:
        subdir = "Results"
    if file_ext is None:
        file_ext = ".yaml"

    # Create the filename
    caller = inspect.getouterframes(inspect.currentframe(), 2)[1 + callstack_offset]

    testname = caller.function

    self_value = caller.frame.f_locals.get("self", None)
    if self_value is not None:
        testname = "{}.{}".format(self_value.__class__.__name__, testname)

    dirname, basename = os.path.split(caller.filename)
    basename = os.path.splitext(basename)[0]

    return os.path.realpath(
        os.path.join(
            dirname,
            subdir,
            "{}.{}{}{}".format(
                basename,
                testname,
                suffix or "",
                file_ext,
            ),
        ),
    )
