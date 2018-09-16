# ----------------------------------------------------------------------
# |  
# |  StringHelpers_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-03 14:40:00
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for StringHelpers.py."""

import os
import sys
import unittest 

from CommonEnvironment.StringHelpers import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class PrependSuite(unittest.TestCase):
    def test_Standard(self):
        self.assertEqual(Prepend("prefix: ", "one\ntwo\nthree\n"), "one\nprefix: two\nprefix: three\n")
        self.assertEqual(Prepend("prefix: ", "one\ntwo\nthree\n", skip_first_line=False), "prefix: one\nprefix: two\nprefix: three\n")
        self.assertEqual(Prepend("prefix: ", "\none\ntwo\nthree\n"), "\nprefix: one\nprefix: two\nprefix: three\n")
        self.assertEqual(Prepend("prefix: ", "\none\ntwo\nthree\n", skip_first_line=False), "prefix: \nprefix: one\nprefix: two\nprefix: three\n")

# ----------------------------------------------------------------------
class LeftJustifySuite(unittest.TestCase):
    def test_Standard(self):
        self.assertEqual(LeftJustify("one\ntwo\nthree\n", 4), "one\n    two\n    three\n")
        self.assertEqual(LeftJustify("one\ntwo\nthree\n", 4, skip_first_line=False), "    one\n    two\n    three\n")
        self.assertEqual(LeftJustify("\none\ntwo\nthree\n", 4), "\n    one\n    two\n    three\n")
        self.assertEqual(LeftJustify("\none\ntwo\nthree\n", 4, skip_first_line=False), "    \n    one\n    two\n    three\n")

# ----------------------------------------------------------------------
class WrapSuite(unittest.TestCase):
    def test_Standard(self):
        self.assertEqual( Wrap( textwrap.dedent(
                                      """\
                                      
                                      This is a test of some longer text in multiple paragraphs.

                                      
                                      
                                      One two three four five six seven eight nine ten eleven.
                                      
                                      """),
                                width=15,
                              ),
                          textwrap.dedent(
                              """\
                              
                              This is a test
                              of some longer
                              text in
                              multiple
                              paragraphs.


                                                            
                              One two three
                              four five six
                              seven eight
                              nine ten
                              eleven.
                              
                              """),
                        )

        self.assertEqual( Wrap( textwrap.dedent(
                                      """\
                                      
                                      This is a test of some longer text in multiple paragraphs.

                                      
                                      
                                      One two three four five six seven eight nine ten eleven.
                                      
                                      """),
                                width=15,
                                replace_whitespace=True,
                              ),
                          textwrap.dedent(
                              """\
                              This is a test
                              of some longer
                              text in
                              multiple
                              paragraphs.
                              
                              
                              
                              One two three
                              four five six
                              seven eight
                              nine ten
                              eleven."""),
                        )

        self.assertEqual( Wrap( textwrap.dedent(
                                    """\
                                    
                                    This is a test
                                    of some longer
                                    text in
                                    multiple
                                    paragraphs.



                                    One two three
                                    four five six
                                    seven eight
                                    nine ten
                                    eleven.
                                    
                                    """),
                                width=115,
                              ),
                          textwrap.dedent(
                                      """\
                                      
                                      This is a test of some longer text in multiple paragraphs.

                                      
                                      
                                      One two three four five six seven eight nine ten eleven.
                                      
                                      """),
                        )

# ----------------------------------------------------------------------
class StringConversionSuite(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_ToPascalCase(self):
        self.assertEqual(ToPascalCase("this_is_a_test"), "ThisIsATest")
        self.assertEqual(ToPascalCase("_this_is_a_test"), "_ThisIsATest")
        self.assertEqual(ToPascalCase("this_is_a_test_"), "ThisIsATest_")
        self.assertEqual(ToPascalCase("__this_is_a_test"), "__ThisIsATest")
        self.assertEqual(ToPascalCase("this_is_a_test__"), "ThisIsATest__")
        self.assertEqual(ToPascalCase("__this_is_a_test__"), "__ThisIsATest__")
        self.assertEqual(ToPascalCase("ThisIsATest"), "ThisIsATest")
        self.assertEqual(ToPascalCase(""), "")

    # ----------------------------------------------------------------------
    def test_ToSnakeCase(self):
        self.assertEqual(ToSnakeCase("ThisIsATest"), "this_is_a_test")
        self.assertEqual(ToSnakeCase("_ThisIsATest"), "_this_is_a_test")
        self.assertEqual(ToSnakeCase("ThisIsATest_"), "this_is_a_test_")
        self.assertEqual(ToSnakeCase("__ThisIsATest"), "__this_is_a_test")
        self.assertEqual(ToSnakeCase("ThisIsATest__"), "this_is_a_test__")
        self.assertEqual(ToSnakeCase("__ThisIsATest__"), "__this_is_a_test__")
        self.assertEqual(ToSnakeCase("this_is_a_test"), "this_is_a_test")
        self.assertEqual(ToSnakeCase(""), "")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass