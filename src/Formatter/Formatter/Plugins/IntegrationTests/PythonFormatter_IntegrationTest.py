# ----------------------------------------------------------------------
# |
# |  PythonFormatter_IntegrationTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-12-18 09:45:52
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit tests for PythonFormatter"""

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

sys.path.insert(0, os.path.join(_script_dir, "..", "PythonFormatterImpl"))
with CallOnExit(lambda: sys.path.pop(0)):
    from AlignAssignmentsPlugin import Plugin as AlignAssignmentsPlugin

# ----------------------------------------------------------------------
if sys.version[0] == "2":
    sys.stdout.write("The script does not run with python2.\n")

    # ----------------------------------------------------------------------
    class TestSuite(unittest.TestCase):
        def testStandard(self):
            self.assertTrue(True)


else:

    # ----------------------------------------------------------------------
    class TestBase(unittest.TestCase):
        # ----------------------------------------------------------------------
        def setUp(self):
            self.maxDiff = None

        # ----------------------------------------------------------------------
        def _Format(self, original, expected, *plugin_names, **plugin_args):
            result = Formatter.Format(
                original,
                black_line_length=200,
                include_plugin_names=plugin_names,
                **plugin_args
            )[0]

            self.assertEqual(result, expected)

    # ----------------------------------------------------------------------
    class AlignTrailingCommentsSuite(TestBase):
        # ----------------------------------------------------------------------
        def _Format(self, original, expected):
            return super(AlignTrailingCommentsSuite, self)._Format(
                original,
                expected,
                "AlignTrailingComments",
                AlignTrailingComments=[[10, 20, 30]],
            )

        # ----------------------------------------------------------------------
        def testStandard(self):
            self._Format(
                textwrap.dedent(
                    """\
                    one # Comment 1
                    two # Comment 2
                    skip
                    two.a # Comment 2.5


                    def Func1():
                        var # Comment A


                    three_____ # Comment 3
                    four # Comment 4
                    skip
                    four.a # Comment 4.5


                    def Func2():
                        var_____ # Comment B


                    five________________ # Comment 5
                    six # Comment 6
                    skip
                    six.a # Comment 6.5


                    def Func3():
                        var_____________ # Comment C
                    """,
                ),
                textwrap.dedent(
                    """\
                    one      # Comment 1
                    two      # Comment 2
                    skip
                    two.a    # Comment 2.5


                    def Func1():
                        var  # Comment A


                    three_____         # Comment 3
                    four               # Comment 4
                    skip
                    four.a             # Comment 4.5


                    def Func2():
                        var_____       # Comment B


                    five________________         # Comment 5
                    six                          # Comment 6
                    skip
                    six.a                        # Comment 6.5


                    def Func3():
                        var_____________         # Comment C
                    """,
                ),
            )

        # ----------------------------------------------------------------------
        def testLeadingComments(self):
            self._Format(
                textwrap.dedent(
                    """\
                    # This is a test
                    one # Comment 1
                    two # Comment 2
                    """,
                ),
                textwrap.dedent(
                    """\
                    # This is a test
                    one      # Comment 1
                    two      # Comment 2
                    """,
                ),
            )

        # ----------------------------------------------------------------------
        def testTrailingComments(self):
            self._Format(
                textwrap.dedent(
                    """\
                    # This is a test
                    one # Comment 1
                    two # Comment 2
                    # More Testing
                    """,
                ),
                textwrap.dedent(
                    """\
                    # This is a test
                    one      # Comment 1
                    two      # Comment 2
                             # More Testing
                    """,
                ),
            )

        # ----------------------------------------------------------------------
        def testInlineComments(self):
            self._Format(
                textwrap.dedent(
                    """\
                    value = [
                                                                # Overrides the displayed script name; the calling file's name
                                                                # will be used if not provided.
                        "CommandLineScriptName",                # def Func() -> string

                                                                # Overrides the script description; the calling file's docstring
                                                                # will be used if not provided.
                        "CommandLineScritpDescription",         # def Func() -> string

                                                                # Content displayed after the description but before usage
                                                                # information; no prefix will be displayed if not provided.
                        "CommandLineDocPrefix",                 # def Func() -> string

                                                                # Content displayed after usage information; no prefix will
                                                                # be displayed if not provided.
                        "CommandLineDocSuffix",                 # def Func() -> string
                    ]
                    """,
                ),
                textwrap.dedent(
                    """\
                    value = [
                        # Overrides the displayed script name; the calling file's name
                        # will be used if not provided.
                        "CommandLineScriptName",        # def Func() -> string
                                                        # Overrides the script description; the calling file's docstring
                                                        # will be used if not provided.
                        "CommandLineScritpDescription", # def Func() -> string
                                                        # Content displayed after the description but before usage
                                                        # information; no prefix will be displayed if not provided.
                        "CommandLineDocPrefix",         # def Func() -> string
                                                        # Content displayed after usage information; no prefix will
                                                        # be displayed if not provided.
                        "CommandLineDocSuffix",         # def Func() -> string
                    ]
                    """,
                ),
            )

        # ----------------------------------------------------------------------
        def testLongLine(self):
            self._Format(
                textwrap.dedent(
                    """\
                    Line_1
                    Line_2 # Comment
                    This_is_a_really_long_line
                    comment_should_come_after_the_end_of_the_content
                    Line_3 # Comment
                    """,
                ),
                textwrap.dedent(
                    """\
                    Line_1
                    Line_2                                           # Comment
                    This_is_a_really_long_line
                    comment_should_come_after_the_end_of_the_content
                    Line_3                                           # Comment
                    """,
                ),
            )

        # ----------------------------------------------------------------------
        def testIgnore(self):
            self._Format(
                textwrap.dedent(
                    """\
                    Line_1
                    Line_2 # Comment
                    Line_3 # fmt: off
                    Line_4 # Comment
                    Line_5 # yapf: disable

                    Line_7 # fmt: off

                    # fmt: off
                    Line_1 # Comment 1
                    Line_2 # Comment 2
                    # fmt: on

                    Line_3 # Comment 3

                    # yapf: disable
                    Line_4 # Comment 4
                    Line_5 # Comment 5
                    # yapf: enable

                    Line_6 # Comment 6
                    """,
                ),
                textwrap.dedent(
                    """\
                    Line_1
                    Line_2   # Comment
                    Line_3  # fmt: off
                    Line_4   # Comment
                    Line_5  # yapf: disable

                    Line_7  # fmt: off

                    # fmt: off
                    Line_1 # Comment 1
                    Line_2 # Comment 2
                    # fmt: on

                    Line_3   # Comment 3

                    # yapf: disable
                    Line_4 # Comment 4
                    Line_5 # Comment 5
                    # yapf: enable

                    Line_6   # Comment 6
                    """,
                ),
            )

    # ----------------------------------------------------------------------
    class AlignAssignmentsSuite(TestBase):
        # ----------------------------------------------------------------------
        def _Format(
            self,
            expected,
            flags,
            original=None,
        ):
            if original is None:
                original = textwrap.dedent(
                    """\
                    one = 1


                    class Foo(object):
                        two = 2

                        def __init__(self):
                            self.a = 10
                            b = 20

                        def method(self):
                            c = 30
                    """,
                )

            return super(AlignAssignmentsSuite, self)._Format(
                original,
                expected,
                "AlignAssignments",
                "AlignTrailingComments",
                AlignAssignments=[[10, 20, 30], flags],
                AlignTrailingComments=[[10, 20, 30]],
            )

        # ----------------------------------------------------------------------
        def testModule(self):
            self._Format(
                textwrap.dedent(
                    """\
                    one      = 1


                    class Foo(object):
                        two = 2

                        def __init__(self):
                            self.a = 10
                            b = 20

                        def method(self):
                            c = 30
                    """,
                ),
                AlignAssignmentsPlugin.ModuleLevel,
            )

        # ----------------------------------------------------------------------
        def testClass(self):
            self._Format(
                textwrap.dedent(
                    """\
                    one = 1


                    class Foo(object):
                        two  = 2

                        def __init__(self):
                            self.a = 10
                            b = 20

                        def method(self):
                            c = 30
                    """,
                ),
                AlignAssignmentsPlugin.ClassLevel,
            )

        # ----------------------------------------------------------------------
        def testInit(self):
            self._Format(
                textwrap.dedent(
                    """\
                    one = 1


                    class Foo(object):
                        two = 2

                        def __init__(self):
                            self.a     = 10
                            b = 20

                        def method(self):
                            c = 30
                    """,
                ),
                AlignAssignmentsPlugin.InitLevel,
            )

        # ----------------------------------------------------------------------
        def testInitAny(self):
            self._Format(
                textwrap.dedent(
                    """\
                    one = 1


                    class Foo(object):
                        two = 2

                        def __init__(self):
                            self.a     = 10
                            b          = 20

                        def method(self):
                            c = 30
                    """,
                ),
                AlignAssignmentsPlugin.InitAnyLevel,
            )

        # ----------------------------------------------------------------------
        def testMethod(self):
            self._Format(
                textwrap.dedent(
                    """\
                    one = 1


                    class Foo(object):
                        two = 2

                        def __init__(self):
                            self.a = 10
                            b = 20

                        def method(self):
                            c          = 30
                    """,
                ),
                AlignAssignmentsPlugin.MethodLevel,
            )

        # ----------------------------------------------------------------------
        def testModuleClassAndInit(self):
            self._Format(
                textwrap.dedent(
                    """\
                    one      = 1


                    class Foo(object):
                        two  = 2

                        def __init__(self):
                            self.a     = 10
                            b = 20

                        def method(self):
                            c = 30
                    """,
                ),
                AlignAssignmentsPlugin.ModuleLevel | AlignAssignmentsPlugin.ClassLevel | AlignAssignmentsPlugin.InitLevel,
            )

        # ----------------------------------------------------------------------
        def testAssignmentAndComment(self):
            self._Format(
                textwrap.dedent(
                    """\
                    one      = 1       # Comment


                    two_____           = 2       # Comment


                    one                = 1       # Comment
                    two_____           = 2       # Comment
                    """,
                ),
                AlignAssignmentsPlugin.ModuleLevel,
                original=textwrap.dedent(
                    """\
                    one = 1 # Comment


                    two_____ = 2 # Comment


                    one = 1 # Comment
                    two_____ = 2 # Comment
                    """,
                ),
            )

        # ----------------------------------------------------------------------
        def testIgnore(self):
            self._Format(
                textwrap.dedent(
                    """\
                    one      = 1
                    two = 2  # fmt: off
                    three = 3  # fmt: off
                    four     = 4
                    five = 5  # yapf: disable
                    six      = 6

                    # fmt: off
                    a = a
                    b = b
                    c = c
                    # fmt: on

                    d        = d

                    # yapf: disable
                    e = e
                    f = f
                    g = g
                    # yapf: enable

                    h        = h
                    """,
                ),
                AlignAssignmentsPlugin.ModuleLevel,
                original=textwrap.dedent(
                    """\
                    one = 1
                    two = 2  # fmt: off
                    three = 3  # fmt: off
                    four = 4
                    five = 5  # yapf: disable
                    six = 6

                    # fmt: off
                    a = a
                    b = b
                    c = c
                    # fmt: on

                    d = d

                    # yapf: disable
                    e = e
                    f = f
                    g = g
                    # yapf: enable

                    h = h
                    """,
                ),
            )

    # ----------------------------------------------------------------------
    class SplitLongFunctionsSuite(TestBase):
        # ----------------------------------------------------------------------
        def _Format(self, original, expected):
            return super(SplitLongFunctionsSuite, self)._Format(
                original,
                expected,
                "Splitter",
                Splitter={
                    "max_func_line_length": 20,
                    "split_func_args_with_default": False,
                },
            )

        # ----------------------------------------------------------------------
        def testStandard(self):
            self._Format(
                textwrap.dedent(
                    """\
                    def Func1(one, two):
                        pass


                    def Func2(one, two, three, four):
                        pass


                    Func3(one, two)
                    Func4(one, two, three, four)
                    """,
                ),
                textwrap.dedent(
                    """\
                    def Func1(one, two):
                        pass


                    def Func2(
                        one,
                        two,
                        three,
                        four,
                    ):
                        pass


                    Func3(one, two)
                    Func4(
                        one,
                        two,
                        three,
                        four,
                    )
                    """,
                ),
            )

    # ----------------------------------------------------------------------
    class SplitFunctionsWithDefaultsSuite(TestBase):
        # ----------------------------------------------------------------------
        def _Format(self, original, expected):
            return super(SplitFunctionsWithDefaultsSuite, self)._Format(
                original,
                expected,
                "Splitter",
                Splitter={
                    "max_func_line_length": 400,
                    "split_func_args_with_default": True,
                },
            )

        # ----------------------------------------------------------------------
        def testStandard(self):
            self._Format(
                textwrap.dedent(
                    """\
                    def Func1(one, two, three):
                        pass


                    def Func2(one, two, three=3):
                        pass


                    def Func3(one=1, two=2, three=3):
                        pass


                    def Func4(
                        one,
                        two, three=3
                    ):
                        pass


                    def Func(one, two=2, **kwargs):
                        pass


                    Func5(one, two=2)
                    Func6(one, two=2, three)
                    Func7(
                        one,
                        two, three=3
                    )
                    Func8(one, two, three)
                    """,
                ),
                textwrap.dedent(
                    """\
                    def Func1(one, two, three):
                        pass


                    def Func2(
                        one,
                        two,
                        three=3,
                    ):
                        pass


                    def Func3(
                        one=1,
                        two=2,
                        three=3,
                    ):
                        pass


                    def Func4(
                        one,
                        two,
                        three=3,
                    ):
                        pass


                    def Func(
                        one,
                        two=2,
                        **kwargs
                    ):
                        pass


                    Func5(
                        one,
                        two=2,
                    )
                    Func6(
                        one,
                        two=2,
                        three,
                    )
                    Func7(
                        one,
                        two,
                        three=3,
                    )
                    Func8(one, two, three)
                    """,
                ),
            )

        # ----------------------------------------------------------------------
        def testChainedCall(self):
            self._Format(
                textwrap.dedent(
                    """\
                    Executor().Invoke(output_stream=output_stream, verbose=verbose, print_results=print_results, allow_exceptions=allow_exceptions)
                    """,
                ),
                textwrap.dedent(
                    """\
                    Executor().Invoke(
                        output_stream=output_stream,
                        verbose=verbose,
                        print_results=print_results,
                        allow_exceptions=allow_exceptions,
                    )
                    """,
                ),
            )

        # ----------------------------------------------------------------------
        def testGenerator(self):
            self._Format(
                textwrap.dedent(
                    """\
                    for filename in FileSystem.WalkFiles(plugin_input_dir, include_file_extensions=[".py"], include_file_base_names=[lambda basename: basename.endswith("Plugin")]):
                        pass
                    """,
                ),
                textwrap.dedent(
                    """\
                    for filename in FileSystem.WalkFiles(
                        plugin_input_dir,
                        include_file_extensions=[".py"],
                        include_file_base_names=[lambda basename: basename.endswith("Plugin")],
                    ):
                        pass
                    """,
                ),
            )

        # ----------------------------------------------------------------------
        def testReturn(self):
            self._Format(
                textwrap.dedent(
                    """\
                    return self.Usage(verbose=True, potential_method_name=potential_method_name)
                    """,
                ),
                textwrap.dedent(
                    """\
                    return self.Usage(
                        verbose=True,
                        potential_method_name=potential_method_name,
                    )
                    """,
                ),
            )

    # ----------------------------------------------------------------------
    class SplitFunctionsSuite(TestBase):
        # ----------------------------------------------------------------------
        def _Format(self, original, expected):
            return super(SplitFunctionsSuite, self)._Format(
                original,
                expected,
                "Splitter",
                Splitter={
                    "max_func_line_length": 78,
                    "split_func_args_with_default": True,
                },
            )

        # ----------------------------------------------------------------------
        def testGeneral(self):
            self._Format(
                textwrap.dedent(
                    """\
                    Func1(Func2(1, two=2), 3)


                    Func3(Func4(1, two), 3)


                    (func1 or func2)(a, b, c)


                    EmptyFunc()


                    def Func1(one, two, three=3, four=Func(a, Func(1, 2), c)): pass


                    def Func2(one, two, three=3, four=Func(a, Func(1, two=2), c)): pass


                    class Foo(object):
                        def __init__(self):
                            self.func(1, 2, 3)


                    Another(one, two=Func(1, 2))


                    return self.Usage(verbose=True, another=Func(1, 2, 3), potential_method_name=potential_method_name)


                    Func1(1, 2, 3)


                    def Func2(one, two, three, four, five, six, seven, eight, nine, ten, eleven, twelve): pass


                    Func3(one, Func(two, three, four, five, six, seven, eight, nine, ten, eleven, twelve, thirteen, kwargs), **other)


                    def Func__(one, two, three=3): print("output")


                    def Func__2(one, two, three): print("output2")


                    Executor(one, two).Other(a, b, c=10).More(a, b)


                    Executor(one, two).Other(a, b, c).More(a, b=2)


                    # Comprehensions
                    [a for a in [one, two, three, four, five] if a & 1]


                    {k: k + 1 for k in [one, two, three, four, five] if k & 1}


                    {k: v for k, v in [(one, 1), (two, 2), (three, 3), (four, 4), (five, 5)] if k & 1}


                    (a for a in [one, two, three, four, five] if a & 1)


                    # Real-world examples that have been problematic
                    _Format(original, expected, "AlignAssignments", "AlignTrailingComments", AlignAssignments=[ [ 10, 20, 30, 40, ], flags ], AlignTrailingComments=[ [ 10, 20, 30, ], ], an_arg_to_make_it_longer___=10)


                    return super(AlignAssignmentsSuite, self)._Format(
                        AlignAssignments=[ [ 10, 20, 30, 40], flags ],
                        AlignTrailingComments=[ 100, 200, 300, 400, ],
                        more={ "a": 1, "b": 2, "c": 3, "d": 4 },
                    )


                    output_stream.write(textwrap.dedent(
                        '''\

                        INFO: Calling '{name}' with the arguments:
                        {args}

                        ''').format( name=entry_point.Name,
                                     args='\\n'.join([ "    {k:<20}  {v}".format( k="{}:".format(k),
                                                                                 v=v,
                                                                               )
                                                      for k, v in six.iteritems(kwargs)
                                                    ]),
                                   ))
                    """,
                ),
                textwrap.dedent(
                    """\
                    Func1(
                        Func2(
                            1,
                            two=2,
                        ),
                        3,
                    )


                    Func3(Func4(1, two), 3)


                    (func1 or func2)(a, b, c)


                    EmptyFunc()


                    def Func1(
                        one,
                        two,
                        three=3,
                        four=Func(a, Func(1, 2), c),
                    ):
                        pass


                    def Func2(
                        one,
                        two,
                        three=3,
                        four=Func(
                            a,
                            Func(
                                1,
                                two=2,
                            ),
                            c,
                        ),
                    ):
                        pass


                    class Foo(object):
                        def __init__(self):
                            self.func(1, 2, 3)


                    Another(
                        one,
                        two=Func(1, 2),
                    )


                    return self.Usage(
                        verbose=True,
                        another=Func(1, 2, 3),
                        potential_method_name=potential_method_name,
                    )


                    Func1(1, 2, 3)


                    def Func2(
                        one,
                        two,
                        three,
                        four,
                        five,
                        six,
                        seven,
                        eight,
                        nine,
                        ten,
                        eleven,
                        twelve,
                    ):
                        pass


                    Func3(
                        one,
                        Func(
                            two,
                            three,
                            four,
                            five,
                            six,
                            seven,
                            eight,
                            nine,
                            ten,
                            eleven,
                            twelve,
                            thirteen,
                            kwargs,
                        ),
                        **other
                    )


                    def Func__(
                        one,
                        two,
                        three=3,
                    ):
                        print("output")


                    def Func__2(one, two, three):
                        print("output2")


                    Executor(one, two).Other(
                        a,
                        b,
                        c=10,
                    ).More(a, b)


                    Executor(one, two).Other(a, b, c).More(
                        a,
                        b=2,
                    )


                    # Comprehensions
                    [
                        a for a in [
                            one,
                            two,
                            three,
                            four,
                            five,
                        ] if a & 1
                    ]


                    {
                        k: k + 1 for k in [
                            one,
                            two,
                            three,
                            four,
                            five,
                        ] if k & 1
                    }


                    {
                        k: v for k, v in [
                            (one, 1),
                            (two, 2),
                            (three, 3),
                            (four, 4),
                            (five, 5),
                        ] if k & 1
                    }


                    (
                        a for a in [
                            one,
                            two,
                            three,
                            four,
                            five,
                        ] if a & 1
                    )


                    # Real-world examples that have been problematic
                    _Format(
                        original,
                        expected,
                        "AlignAssignments",
                        "AlignTrailingComments",
                        AlignAssignments=[
                            [
                                10,
                                20,
                                30,
                                40,
                            ],
                            flags,
                        ],
                        AlignTrailingComments=[[10, 20, 30]],
                        an_arg_to_make_it_longer___=10,
                    )


                    return super(AlignAssignmentsSuite, self)._Format(
                        AlignAssignments=[
                            [
                                10,
                                20,
                                30,
                                40,
                            ],
                            flags,
                        ],
                        AlignTrailingComments=[
                            100,
                            200,
                            300,
                            400,
                        ],
                        more={
                            "a": 1,
                            "b": 2,
                            "c": 3,
                            "d": 4,
                        },
                    )


                    output_stream.write(
                        textwrap.dedent(
                            \"\"\"
                        INFO: Calling '{name}' with the arguments:
                        {args}

                        \"\"\",
                        ).format(
                            name=entry_point.Name,
                            args="\\n".join(
                                [
                                    "    {k:<20}  {v}".format(
                                        k="{}:".format(k),
                                        v=v,
                                    ) for k, v in six.iteritems(kwargs)
                                ],
                            ),
                        )
                    )
                    """,
                ),
            )

        # ----------------------------------------------------------------------
        def testIgnore(self):
            self._Format(
                textwrap.dedent(
                    """\
                    Func1(Func2(1, two=2), 3)  # fmt: off


                    Func3(Func4(1, two), 3)  # yapf: disable


                    # fmt: off
                    Func1(Func2(1, two=2), 3)


                    Func3(Func4(1, two), 3)
                    # fmt: on


                    # yapf: disable
                    Func1(Func2(1, two=2), 3)


                    Func3(Func4(1, two), 3)
                    # yapf: enable
                    """,
                ),
                textwrap.dedent(
                    """\
                    Func1(Func2(1, two=2), 3)  # fmt: off


                    Func3(Func4(1, two), 3)  # yapf: disable


                    # fmt: off
                    Func1(Func2(1, two=2), 3)


                    Func3(Func4(1, two), 3)
                    # fmt: on


                    # yapf: disable
                    Func1(Func2(1, two=2), 3)


                    Func3(Func4(1, two), 3)
                    # yapf: enable
                    """,
                ),
            )

    # ----------------------------------------------------------------------
    class TextwrapDedentPlugin(TestBase):
        # ----------------------------------------------------------------------
        def _Format(self, original, expected):
            return super(TextwrapDedentPlugin, self)._Format(
                original,
                expected,
                "Splitter",
                "TextwrapDedent",
                Splitter={
                    "max_func_line_length": 78,
                    "split_func_args_with_default": True,
                },
            )

        # ----------------------------------------------------------------------
        def testStandard(self):
            self._Format(
                textwrap.dedent(
                    """\
                    Func1_________________(Func2_____________________(textwrap.dedent(
                        \"\"\"\\
                        This is a test
                        \"\"\").format(a_______________________________=b)))

                    Func(textwrap.dedent(\"\"\"One line\"\"\"))

                    Func3(textwrap.dedent(
                        '''Line 0
                                    Line 1

                        Line 3
                            Line 4
                                '''))

                    Func4(textwrap.dedent(
                        # This is a test
                        '''
                            Line 1

                        Line 3
                            Line 4
                                '''))

                    """,
                ),
                textwrap.dedent(
                    """\
                    Func1_________________(
                        Func2_____________________(
                            textwrap.dedent(
                                \"\"\"\\
                                This is a test
                                \"\"\",
                            ).format(
                                a_______________________________=b,
                            )
                        )
                    )

                    Func(textwrap.dedent(\"\"\"One line\"\"\"))

                    Func3(
                        textwrap.dedent(
                            \"\"\"Line 0
                                        Line 1

                            Line 3
                                Line 4
                                    \"\"\",
                        )
                    )

                    Func4(
                        textwrap.dedent(
                            # This is a test
                            \"\"\"
                                Line 1

                            Line 3
                                Line 4
                                    \"\"\"
                        )
                    )
                    """,
                ),
            )

    # ----------------------------------------------------------------------
    class CommaAfterArgsSuite(TestBase):

        # ----------------------------------------------------------------------
        def _Format(self, original, expected):
            result = Formatter.Format(
                original,
                include_plugin_names=["CommaAfterArgs"],
            )[0]

            self.assertEqual(result, expected)

        # ----------------------------------------------------------------------
        def testAll(self):
            self._Format(
                textwrap.dedent(
                    """\
                    Func0(
                    )

                    Func1(
                        one
                    )

                    Func2(
                        one,
                        two,
                    )

                    FuncTextwrap(
                        textwrap.dedent(
                            \"\"\"\\
                            Line 1
                            \"\"\"
                        )
                    )

                    FuncTextwrapWithFormat(
                        textwrap.dedent(
                            \"\"\"\\
                            Line {0}
                            Line {1}
                            \"\"\",
                        ).format(
                            "1",
                            "2",
                        )
                    )

                    Nested0(
                        Nested1(
                            textwrap.dedent(
                                \"\"\"\\
                                Line 1
                                \"\"\",
                            )
                        )
                    )

                    NestedA(
                        one,
                        NestedB(
                            textwrap.dedent(
                                \"\"\"\\
                                Line 1
                                \"\"\",
                            )
                        ),
                        two
                    )

                    KeywordArgs(
                        textwrap.dedent(
                            \"\"\"\\
                            Line 1
                            \"\"\",
                        ),
                        **kwargs
                    )

                    if any(
                        child
                        for child in self.Children
                        if child.ShouldBeSplit(
                            textwrap.dedent(
                                \"\"\"\\
                                Line A
                                \"\"\",
                            ),
                            **arg2
                        )
                    ):
                        return True
                    """,
                ),
                textwrap.dedent(
                    """\
                    Func0()

                    Func1(one)

                    Func2(one, two)

                    FuncTextwrap(
                        textwrap.dedent(
                            \"\"\"\\
                            Line 1
                            \"\"\",
                        ),
                    )

                    FuncTextwrapWithFormat(
                        textwrap.dedent(
                            \"\"\"\\
                            Line {0}
                            Line {1}
                            \"\"\",
                        ).format("1", "2"),
                    )

                    Nested0(
                        Nested1(
                            textwrap.dedent(
                                \"\"\"\\
                                Line 1
                                \"\"\",
                            ),
                        ),
                    )

                    NestedA(
                        one,
                        NestedB(
                            textwrap.dedent(
                                \"\"\"\\
                                Line 1
                                \"\"\",
                            ),
                        ),
                        two,
                    )

                    KeywordArgs(
                        textwrap.dedent(
                            \"\"\"\\
                            Line 1
                            \"\"\",
                        ),
                        **kwargs
                    )

                    if any(
                        child
                        for child in self.Children
                        if child.ShouldBeSplit(
                            textwrap.dedent(
                                \"\"\"\\
                                Line A
                                \"\"\",
                            ),
                            **arg2
                        )
                    ):
                        return True
                    """,
                ),
            )

    # ----------------------------------------------------------------------
    class CompleteSuite(TestBase):
        # ----------------------------------------------------------------------
        def _Format(self, original, expected):
            result = Formatter.Format(original)[0]

            self.assertEqual(result, expected)

        # ----------------------------------------------------------------------
        def testAll(self):
            self._Format(
                textwrap.dedent(
                    """\
                    # This should not split between the 'strip' parens
                    Func(
                        compound_statement=dest_writer.CreateCompoundElement(temporary, "attrib                       ").strip(),
                    )


                    # Trailing commas
                    indented_stream.write(
                        textwrap.dedent(
                            \"\"\"\\
                            # ----------------------------------------------------------------------
                            # ----------------------------------------------------------------------
                            \"\"\",
                        ),
                    )


                    indented_stream.write(
                        textwrap.dedent(
                            \"\"\"\\
                            # ----------------------------------------------------------------------
                            # ----------------------------------------------------------------------
                            {foo}
                            \"\"\",
                        ).format(
                            foo="bar",
                        ),
                    )


                    indented_stream.write(
                        textwrap.dedent(
                            \"\"\"\\
                            # ----------------------------------------------------------------------
                            # ----------------------------------------------------------------------
                            \"\"\",
                        ).format(),
                    )


                    value = textwrap.dedent(
                        \"\"\"\\
                        one
                        two
                        \"\"\"
                    )


                    value = textwrap.dedent(
                        \"\"\"\\
                        one
                        {value}
                        \"\"\"
                    ).format(
                        value="two",
                    )
                    """,
                ),
                textwrap.dedent(
                    """\
                    # This should not split between the 'strip' parens
                    Func(
                        compound_statement=dest_writer.CreateCompoundElement(temporary, "attrib                       ").strip(),
                    )


                    # Trailing commas
                    indented_stream.write(
                        textwrap.dedent(
                            \"\"\"\\
                            # ----------------------------------------------------------------------
                            # ----------------------------------------------------------------------
                            \"\"\",
                        ),
                    )


                    indented_stream.write(
                        textwrap.dedent(
                            \"\"\"\\
                            # ----------------------------------------------------------------------
                            # ----------------------------------------------------------------------
                            {foo}
                            \"\"\",
                        ).format(
                            foo="bar",
                        ),
                    )


                    indented_stream.write(
                        textwrap.dedent(
                            \"\"\"\\
                            # ----------------------------------------------------------------------
                            # ----------------------------------------------------------------------
                            \"\"\",
                        ).format(),
                    )


                    value                                       = textwrap.dedent(
                        \"\"\"\\
                        one
                        two
                        \"\"\",
                    )


                    value                                       = textwrap.dedent(
                        \"\"\"\\
                        one
                        {value}
                        \"\"\",
                    ).format(
                        value="two",
                    )
                    """,
                ),
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
