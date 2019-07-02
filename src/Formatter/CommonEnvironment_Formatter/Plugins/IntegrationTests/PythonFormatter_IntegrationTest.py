# ----------------------------------------------------------------------
# |
# |  PythonFormatter_IntegrationTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-30 08:19:16
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Integration tests for PythonFormattter.py"""

import os
import sys
import textwrap
import unittest

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.path.join(_script_dir, ".."))
with CallOnExit(lambda: sys.path.pop(0)):
    from PythonFormatter import Formatter

# ----------------------------------------------------------------------
if sys.version[0] == "2":
    sys.stdout.write("This script does not run with python 2.\n")

    # ----------------------------------------------------------------------
    class TestSuite(unittest.TestCase):
        def testStandard(self):
            self.assertTrue(True)

    # ----------------------------------------------------------------------

else:
    # ----------------------------------------------------------------------
    class TestBase(unittest.TestCase):
        # ----------------------------------------------------------------------
        def setUp(self):
            self.maxDiff = None

        # ----------------------------------------------------------------------
        def Test(
            self,
            original,
            expected,
            black_line_length=120,
            *plugin_names,
            **plugin_args
        ):
            result = Formatter.Format(
                original,
                black_line_length=black_line_length,
                include_plugin_names=plugin_names,
                **plugin_args
            )

            self.assertEqual(result[0], expected)
            self.assertEqual(result[1], not expected == original)

    # ----------------------------------------------------------------------
    class CompleteTests(TestBase):
        # ----------------------------------------------------------------------
        def test_Standard(self):
            self.Test(
                textwrap.dedent(
                    """\
                    a = [1,2, 3]
                    b = [4, 5, 6, 7]
                    c = {1, 2, 3}
                    d = {4, 5, 6, 7}
                    e = (1, 2, 3)
                    f = (4, 5, 6, 7)

                    def func(a, b, c, d=[1,2,[a,b,c,d,e],4,5], unique_value=3, **kwargs):
                        pass

                    if True:
                        func(1, 2, 3, 4, 5=a)

                    [1, [2, 3, 4, 5], 6, 7]

                    [
                        1,
                        func(
                            a=2,
                        ),
                        3,
                    ]

                    def Func(one_two_three, four_five_six, seven_eight_nine, ten_eleven_twelve, thirteen_fourteen_fifteen=131415):
                        pass

                    if True:
                        if True:
                            Test(1, textwrap.dedent(
                                '''\\
                                Line 1
                                    Line 2
                                Line 3
                                '''
                            ), 3)

                    Func((1,2,3))

                    x=10
                    OrderedDict([ kvp for kvp in sorted(six.iteritems(entities), key=EntitySortKey) ])
                    { a : b for (a, b) in sorted(six.iteritems(entities), key=EntitySortKey) }

                    class Foo(object):
                        a = 10
                        abc = 20

                    a = [
                        one(a, b, c=3),    # first value
                        two,
                        three,  # third value
                    ]

                    b = [
                        one,    # first value
                        two,
                        three,  # third value
                        four,
                    ]

                    return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))  # <Class '<name>' has no '<attr>' member> pylint: disable = E1101

                    return '$env:{name}="{values};" + $env:{name}'.format( name=command.Name,
                                                                           values=os.pathsep.join(command.Values),   # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
                                                                         )

                    @Decorator1(foo=bar)
                    @Decorator2()
                    def Func():
                        pass
                    """,
                ),
                textwrap.dedent(
                    """\
                    a                                           = [1, 2, 3]
                    b                                           = [
                        4,
                        5,
                        6,
                        7,
                    ]
                    c                                           = {1, 2, 3}
                    d                                           = {
                        4,
                        5,
                        6,
                        7,
                    }
                    e                                           = (1, 2, 3)
                    f                                           = (
                        4,
                        5,
                        6,
                        7,
                    )


                    def func(
                        a,
                        b,
                        c,
                        d=[
                            1,
                            2,
                            [
                                a,
                                b,
                                c,
                                d,
                                e,
                            ],
                            4,
                            5,
                        ],
                        unique_value=3,
                        **kwargs
                    ):
                        pass

                    if True:
                        func(
                            1,
                            2,
                            3,
                            4,
                            5=a,
                        )

                    [
                        1,
                        [
                            2,
                            3,
                            4,
                            5,
                        ],
                        6,
                        7,
                    ]

                    [
                        1,
                        func(
                            a=2,
                        ),
                        3,
                    ]


                    def Func(
                        one_two_three,
                        four_five_six,
                        seven_eight_nine,
                        ten_eleven_twelve,
                        thirteen_fourteen_fifteen=131415,
                    ):
                        pass

                    if True:
                        if True:
                            Test(
                                1,
                                textwrap.dedent(
                                    \"\"\"\\
                                    Line 1
                                        Line 2
                                    Line 3
                                    \"\"\",
                                ),
                                3,
                            )

                    Func((1, 2, 3))

                    x                                           = 10
                    OrderedDict(
                        [
                            kvp for kvp in sorted(
                                six.iteritems(entities),
                                key=EntitySortKey,
                            )
                        ],
                    )
                    {
                        a: b for (a, b) in sorted(
                            six.iteritems(entities),
                            key=EntitySortKey,
                        )
                    }


                    class Foo(object):
                        a                                       = 10
                        abc                                     = 20


                    a                                           = [
                        one(
                            a,
                            b,
                            c=3,
                        ),                                      # first value
                        two,
                        three,                                  # third value
                    ]

                    b                                           = [
                        one,                                    # first value
                        two,
                        three,                                  # third value
                        four,
                    ]

                    return '$env:{}="{}"'.format(
                        command.Name,
                        os.pathsep.join(command.Values),
                    )                                           # <Class '<name>' has no '<attr>' member> pylint: disable = E1101

                    return '$env:{name}="{values};" + $env:{name}'.format(
                        name=command.Name,
                        values=os.pathsep.join(command.Values),             # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
                    )


                    @Decorator1(
                        foo=bar,
                    )
                    @Decorator2()
                    def Func():
                        pass
                    """,
                ),
            )

        # TODO: Test with short line
        # TODO: Test with altered plugin args
        # TODO: Test with excluded plugins
        # TODO: TOML Test
        # TODO: Verify that colons terminate logical blocks


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(
            unittest.main(
                verbosity=2,
            ),
        )
    except KeyboardInterrupt:
        pass
