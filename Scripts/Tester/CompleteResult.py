# ----------------------------------------------------------------------
# |
# |  CompleteResult.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2020-12-31 14:10:28
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2020
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the CompleteResult object"""

import os
import textwrap

import colorama

import CommonEnvironment
from CommonEnvironment import Nonlocals, ObjectReprImpl
from CommonEnvironment import StringHelpers

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

from Results import Results

# ----------------------------------------------------------------------
class CompleteResult(object):
    """Results for both debug and release builds"""

    # ----------------------------------------------------------------------
    def __init__(self, item):
        self.Item                           = item
        self.debug                          = Results()
        self.release                        = Results()

    # ----------------------------------------------------------------------
    def __repr__(self):
        return ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    def ResultCode(self):
        result = None

        for results in [self.debug, self.release]:
            this_result = results.ResultCode()
            if this_result is None:
                continue

            if this_result < 0:
                result = this_result
                break
            elif result in [None, 0]:
                result = this_result

        return result

    # ----------------------------------------------------------------------
    def ToString(
        self,
        compiler,
        test_parser,
        optional_test_executor,
        optional_code_coverage_validator,
        include_benchmarks=False,
    ):
        header_length = max(180, len(self.Item) + 4)

        return textwrap.dedent(
            """\
            {color_push}{header}
            |{item:^{item_length}}|
            {header}{color_pop}

            {color_push}DEBUG:{color_pop}
            {debug}

            {color_push}RELEASE:{color_pop}
            {release}

            """,
        ).format(
            color_push="{}{}".format(colorama.Fore.WHITE, colorama.Style.BRIGHT),
            color_pop=colorama.Style.RESET_ALL,
            header="=" * header_length,
            item=self.Item,
            item_length=header_length - 2,
            debug="N/A" if not self.debug else StringHelpers.LeftJustify(
                self.debug.ToString(
                    compiler,
                    test_parser,
                    optional_test_executor,
                    optional_code_coverage_validator,
                    include_benchmarks=include_benchmarks,
                ),
                4,
                skip_first_line=False,
            ).rstrip(),
            release="N/A" if not self.release else StringHelpers.LeftJustify(
                self.release.ToString(
                    compiler,
                    test_parser,
                    optional_test_executor,
                    optional_code_coverage_validator,
                    include_benchmarks=include_benchmarks,
                ),
                4,
                skip_first_line=False,
            ).rstrip(),
        )
