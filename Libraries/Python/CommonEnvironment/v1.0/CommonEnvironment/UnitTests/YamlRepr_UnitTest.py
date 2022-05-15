# ----------------------------------------------------------------------
# |
# |  YamlRepr_UnitTest.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-08-25 20:41:41
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Unit test for YamlRepr.py"""

import os
import textwrap

from typing import Dict, List, Optional, Tuple

from dataclasses import dataclass, field

import CommonEnvironment
from CommonEnvironment.YamlRepr import *

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@dataclass(frozen=True, repr=False)
class BasicWithClassInfoAndCustomDisplay(ObjectReprImplBase):
    A: int
    B: bool
    C: str

    # ----------------------------------------------------------------------
    def __post_init__(self):
        ObjectReprImplBase.__init__(
            self,
            include_class_info=True,
            B=lambda value: None,
            C=lambda value: "**{}**".format(value),
        )


# ----------------------------------------------------------------------
@dataclass(frozen=True, repr=False)
class Simple(ObjectReprImplBase):
    A: int
    B: bool
    C: Optional[str]
    S: Optional["Simple"]                   = field(default=None)


# ----------------------------------------------------------------------
@dataclass(frozen=True, repr=False)
class Complex(ObjectReprImplBase):
    Simple: Simple

    Strings: List[Optional[str]]
    Simples: List[Simple]

    EmptyList: List[int]                    = field(init=False, default_factory=list)
    EmptyDict: Dict[Any, Any]               = field(init=False, default_factory=dict)

    ATuple: Tuple[int, ...]

    String: str
    MultilineString: str

    Obj: BasicWithClassInfoAndCustomDisplay

    # ----------------------------------------------------------------------
    def __post_init__(self):
        object.__setattr__(self, "_private_var", 10)

    # ----------------------------------------------------------------------
    def Method1(self):
        pass

    # ----------------------------------------------------------------------
    def _PrivateMethod(self):
        pass


# ----------------------------------------------------------------------
class TestStandard(object):
    _object                                 = Complex(
        Simple(1, True, "A"),
        ["one", "two", None, "three"],
        [
            Simple(100, True, "a string"),
            Simple(200, False, "b string"),
            Simple(300, True, None),
            Simple(400, False, None, Simple(400000, True, "An embedded object\nwith\n  **multiple**\nlines!")),
            Simple(500, True, "e string"),
        ],
        (1, 2),
        "This is a single string",
        textwrap.dedent(
            """\
            This is
                a multiline
                    string.
            """,
        ),
        BasicWithClassInfoAndCustomDisplay(1, True, "A"),
    )

    # ----------------------------------------------------------------------
    def test_Repr(self):
        assert str(self._object) == textwrap.dedent(
            """\
            # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Complex'>
            ATuple:
              - 1
              - 2
            EmptyDict: {}
            EmptyList: []
            MultilineString: |-
              This is
                  a multiline
                      string.

            Obj: # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.BasicWithClassInfoAndCustomDisplay'>
              A: 1 # <class 'int'>
              C: "**A**"
            Simple: # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
              A: 1
              B: true
              C: "A"
              S: null
            Simples:
              - # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                A: 100
                B: true
                C: "a string"
                S: null
              - # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                A: 200
                B: false
                C: "b string"
                S: null
              - # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                A: 300
                B: true
                C: null
                S: null
              - # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                A: 400
                B: false
                C: null
                S: # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                  A: 400000
                  B: true
                  C: |-
                    An embedded object
                    with
                      **multiple**
                    lines!
                  S: null
              - # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                A: 500
                B: true
                C: "e string"
                S: null
            String: "This is a single string"
            Strings:
              - "one"
              - "two"
              - null
              - "three"
            """,
        )

    # ----------------------------------------------------------------------
    def test_CustomSettings(self):
        assert self._object.ToYamlString(
            include_id=True,
            include_class_info=True,
            include_private=True,
            scrub_results=True,
        ) == textwrap.dedent(
            """\
            # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Complex'>
            <<<id>>> : __scrubbed_id__ # <class 'int'>
            ATuple:
              - 1 # <class 'int'>
              - 2 # <class 'int'>
            EmptyDict: {}
            EmptyList: []
            MultilineString: |-
              This is
                  a multiline
                      string.

            Obj: # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.BasicWithClassInfoAndCustomDisplay'>
              <<<id>>> : __scrubbed_id__ # <class 'int'>
              A: 1 # <class 'int'>
              C: "**A**"
            Simple: # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
              <<<id>>> : __scrubbed_id__ # <class 'int'>
              A: 1 # <class 'int'>
              B: True # <class 'bool'>
              C: "A"
              S: None # <class 'NoneType'>
            Simples:
              - # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                <<<id>>> : __scrubbed_id__ # <class 'int'>
                A: 100 # <class 'int'>
                B: True # <class 'bool'>
                C: "a string"
                S: None # <class 'NoneType'>
              - # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                <<<id>>> : __scrubbed_id__ # <class 'int'>
                A: 200 # <class 'int'>
                B: False # <class 'bool'>
                C: "b string"
                S: None # <class 'NoneType'>
              - # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                <<<id>>> : __scrubbed_id__ # <class 'int'>
                A: 300 # <class 'int'>
                B: True # <class 'bool'>
                C: None # <class 'NoneType'>
                S: None # <class 'NoneType'>
              - # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                <<<id>>> : __scrubbed_id__ # <class 'int'>
                A: 400 # <class 'int'>
                B: False # <class 'bool'>
                C: None # <class 'NoneType'>
                S: # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                  <<<id>>> : __scrubbed_id__ # <class 'int'>
                  A: 400000 # <class 'int'>
                  B: True # <class 'bool'>
                  C: |-
                    An embedded object
                    with
                      **multiple**
                    lines!
                  S: None # <class 'NoneType'>
              - # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
                <<<id>>> : __scrubbed_id__ # <class 'int'>
                A: 500 # <class 'int'>
                B: True # <class 'bool'>
                C: "e string"
                S: None # <class 'NoneType'>
            String: "This is a single string"
            Strings:
              - "one"
              - "two"
              - None # <class 'NoneType'>
              - "three"
            _private_var: 10 # <class 'int'>
            """,
        )

    # ----------------------------------------------------------------------
    def test_MaxRecursionDepth(self):
        assert self._object.ToYamlString(
            max_recursion_depth=2,
        ) == textwrap.dedent(
            """\
            # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Complex'>
            ATuple:
              - 1
              - 2
            EmptyDict: {}
            EmptyList: []
            MultilineString: |-
              This is
                  a multiline
                      string.

            Obj: # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.BasicWithClassInfoAndCustomDisplay'>
              A: 1 # <class 'int'>
              C: "**A**"
            Simple: # <class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>
              A: 1
              B: true
              C: "A"
              S: null
            Simples:
              - "-- recursion is disabled: complex element '<class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>' --"
              - "-- recursion is disabled: complex element '<class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>' --"
              - "-- recursion is disabled: complex element '<class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>' --"
              - "-- recursion is disabled: complex element '<class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>' --"
              - "-- recursion is disabled: complex element '<class 'CommonEnvironment.UnitTests.YamlRepr_UnitTest.Simple'>' --"
            String: "This is a single string"
            Strings:
              - "one"
              - "two"
              - null
              - "three"
            """,
        )
