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

# ----------------------------------------------------------------------
if sys.version[0] == "2":
    sys.stdout.write("This script does not run with python 2.\n")

    # ----------------------------------------------------------------------
    class TestSuite(unittest.TestCase):
        def testStandard(self):
            self.assertTrue(True)

    # ----------------------------------------------------------------------

else:
    sys.path.insert(0, os.path.join(_script_dir, ".."))
    with CallOnExit(lambda: sys.path.pop(0)):
        from PythonFormatter import Formatter

    # ----------------------------------------------------------------------
    class TestImpl(unittest.TestCase):
        # ----------------------------------------------------------------------
        def setUp(self):
            self.maxDiff = None

        # ----------------------------------------------------------------------
        def Test(
            self,
            original,
            expected,
            black_line_length=120,
            include_plugin_names=None,
            exclude_plugin_names=None,
            **plugin_args
        ):
            result = Formatter.Format(
                original,
                black_line_length=black_line_length,
                include_plugin_names=include_plugin_names,
                exclude_plugin_names=exclude_plugin_names,
                **plugin_args
            )

            self.assertEqual(result[0], expected)
            self.assertEqual(result[1], not expected == original)

    # ----------------------------------------------------------------------
    class CompleteTests(TestImpl):
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

                    return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))

                    return '$env:{name}="{values};" + $env:{name}'.format( name=command.Name,
                                                                           values=os.pathsep.join(command.Values),   # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
                                                                         )

                    @Decorator1(foo=bar)
                    @Decorator2()
                    def Func():
                        pass


                    @staticmethod
                    @Interface.override
                    def DecorateTokens(
                        tokenizer,
                        tokenize_func,                      # <Unused argument> pylint: disable = W0613
                        recurse_count,                      # <Unused argument> pylint: disable = W0613
                    ):
                        pass


                    def CommentHeader(
                        one,
                        # This is a comment for the argument that follows
                        two,
                    ):
                        pass


                    Func1(
                        a,
                        b # There should be a comma after b
                    )


                    Func2(
                        a,
                        b   # There should be a comma
                            # after b
                    )


                    Func3(
                        a,  # Trailing comment
                        # Header comment
                        b   # There should be a comma
                            # after b
                    )


                    Func4(
                        # no trailing comma
                    )
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

                    return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))

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


                    @staticmethod
                    @Interface.override
                    def DecorateTokens(
                        tokenizer,
                        tokenize_func,                          # <Unused argument> pylint: disable = W0613
                        recurse_count,                          # <Unused argument> pylint: disable = W0613
                    ):
                        pass


                    def CommentHeader(
                        one,
                        # This is a comment for the argument that follows
                        two,
                    ):
                        pass


                    Func1(
                        a,
                        b,                                      # There should be a comma after b
                    )


                    Func2(
                        a,
                        b,                                      # There should be a comma
                                                                # after b
                    )


                    Func3(
                        a,                                      # Trailing comment
                        # Header comment
                        b,                                      # There should be a comma
                                                                # after b
                    )


                    Func4(
                        # no trailing comma
                    )
                    """,
                ),
            )

    # ----------------------------------------------------------------------
    class ShortLineTests(TestImpl):
        # ----------------------------------------------------------------------
        def test_70Chars(self):
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

                    return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))

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
                    )

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
                black_line_length=70,
            )

        # ----------------------------------------------------------------------
        def test_40Chars(self):
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

                    return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))

                    return '$env:{name}="{values};" + $env:{name}'.format( name=command.Name,
                                                                           values=os.pathsep.join(command.Values),
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
                    )

                    return '$env:{name}="{values};" + $env:{name}'.format(
                        name=command.Name,
                        values=os.pathsep.join(
                            command.Values,
                        ),
                    )


                    @Decorator1(
                        foo=bar,
                    )
                    @Decorator2()
                    def Func():
                        pass
                    """,
                ),
                black_line_length=40,
            )

    # ----------------------------------------------------------------------
    class PluginArgsTests(TestImpl):
        # ----------------------------------------------------------------------
        def test_CommentColumns(self):
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

                    return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))

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
                    a        = [1, 2, 3]
                    b        = [
                        4,
                        5,
                        6,
                        7,
                    ]
                    c        = {1, 2, 3}
                    d        = {
                        4,
                        5,
                        6,
                        7,
                    }
                    e        = (1, 2, 3)
                    f        = (
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

                    x        = 10
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
                        a    = 10
                        abc  = 20


                    a        = [
                        one(
                            a,
                            b,
                            c=3,
                        ),                                      # first value
                        two,
                        three,                                  # third value
                    ]

                    b        = [
                        one,                                    # first value
                        two,
                        three,                                  # third value
                        four,
                    ]

                    return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))

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
                AlignAssignments={
                    "alignment_columns": [
                        10,
                        20,
                        30,
                        40,
                    ],
                },
            )

    # ----------------------------------------------------------------------
    class IncludeExcludedTests(TestImpl):
        # ----------------------------------------------------------------------
        def test_Includes(self):
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

                    return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))

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
                    b                                           = [4, 5, 6, 7]
                    c                                           = {1, 2, 3}
                    d                                           = {4, 5, 6, 7}
                    e                                           = (1, 2, 3)
                    f                                           = (4, 5, 6, 7)


                    def func(a, b, c, d=[1, 2, [a, b, c, d, e], 4, 5], unique_value=3, **kwargs):
                        pass


                    if True:
                        func(1, 2, 3, 4, 5=a)

                    [1, [2, 3, 4, 5], 6, 7]

                    [1, func(a=2), 3]


                    def Func(one_two_three, four_five_six, seven_eight_nine, ten_eleven_twelve, thirteen_fourteen_fifteen=131415):
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
                                \"\"\"
                                ),
                                3,
                            )

                    Func((1, 2, 3))

                    x                                           = 10
                    OrderedDict([kvp for kvp in sorted(six.iteritems(entities), key=EntitySortKey)])
                    {a: b for (a, b) in sorted(six.iteritems(entities), key=EntitySortKey)}


                    class Foo(object):
                        a                                       = 10
                        abc                                     = 20


                    a                                           = [one(a, b, c=3), two, three]  # first value  # third value

                    b                                           = [one, two, three, four]       # first value  # third value

                    return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))

                    return '$env:{name}="{values};" + $env:{name}'.format(name=command.Name, values=os.pathsep.join(command.Values)) # <Class '<name>' has no '<attr>' member> pylint: disable = E1101


                    @Decorator1(foo=bar)
                    @Decorator2()
                    def Func():
                        pass
                    """,
                ),
                include_plugin_names=["AlignAssignments", "AlignTrailingComments"],
            )

        # ----------------------------------------------------------------------
        def test_Excludes(self):
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

                    return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))

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
                    d                                           = {4, 5, 6, 7}
                    e                                           = (1, 2, 3)
                    f                                           = (4, 5, 6, 7)


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
                    {a: b for (a, b) in sorted(
                        six.iteritems(entities),
                        key=EntitySortKey,
                    )}


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

                    return '$env:{}="{}"'.format(command.Name, os.pathsep.join(command.Values))

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
                exclude_plugin_names=set(["DictSplitter", "TupleSplitter"]),
            )


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
