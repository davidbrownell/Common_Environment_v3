# ----------------------------------------------------------------------
# |  
# |  RegularExpression_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-25 16:20:32
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for RegularExpression.py."""

import os
import sys
import unittest

from CommonEnvironment.RegularExpression import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class TemplateStringToRegexSuite(unittest.TestCase):
    def test_Standard(self):
        self.assertEqual(TemplateStringToRegex("This  {is}\n{a} {test}", as_string=True), r"^This  (?P<is>.+?)\r?\n(?P<a>.+?) (?P<test>.+?)$")
        self.assertEqual(TemplateStringToRegex("This  {is}\n{a} {test}", as_string=True, match_whole_string=False), r"This  (?P<is>.+?)\r?\n(?P<a>.+?) (?P<test>.+?)")
        self.assertEqual(TemplateStringToRegex("This  {is}\n{a} {is} {test}", as_string=True, match_whole_string=False), r"This  (?P<is>.+?)\r?\n(?P<a>.+?) (?P=is) (?P<test>.+?)")

        template_string = "{one}-{two}-"
        regex = TemplateStringToRegex(template_string)

        match = regex.match(template_string.format( one="ONE",
                                                    two="too",
                                                  ))
        self.assertTrue(match)
        self.assertEqual(match.group("one"), "ONE")
        self.assertEqual(match.group("two"), "too")

        self.assertEqual(TemplateStringToRegex("{tag}", as_string=True, optional_tags=set([ "tag", ])), r"^(?P<tag>.*?)$")

# ----------------------------------------------------------------------
class PythonToJavaScriptSuite(unittest.TestCase):
    def test_Standard(self):
        self.assertEqual(PythonToJavaScript(r"This (?P<is>.+) a_(?# great?)_(?P<test>.+)\."), r"This (.+) a__(.+)\.")
        self.assertEqual(PythonToJavaScript(r"This (?P<is>.+) a_(?# great?)_(?P<test>.+)\. (?# with)-(?P<more>more)"), r"This (.+) a__(.+)\. -(more)")

# ----------------------------------------------------------------------
class WildcardSearchToRegularExpressionSuite(unittest.TestCase):
    def test_Standard(self):
        self.assertEqual(WildcardSearchToRegularExpression("*.?xe", as_string=True), r"^.*\..xe$")
        self.assertEqual(WildcardSearchToRegularExpression("???.exe", as_string=True), r"^...\.exe$")
        
        regex = WildcardSearchToRegularExpression("fo?.*")
        
        self.assertTrue(regex.match("foo.bar"))
        self.assertTrue(regex.match("fox.bar"))
        self.assertTrue(regex.match("foo.b"))
        self.assertTrue(regex.match("foo."))
        self.assertFalse(regex.match("__foo.bar"))
        self.assertFalse(regex.match("foo"))
        
# ----------------------------------------------------------------------
class GenerateSuite(unittest.TestCase):
    def test_Standard(self):
        self.assertEqual(list(Generate(" ", "This is a test")), [ "This", "is", "a", "test", ])
        self.assertEqual(list(Generate(" ", "This_is_a_test")), [ "This_is_a_test", ])
        self.assertEqual(list(Generate(" ", " This is a test")), [ '', "This", "is", "a", "test", ])
        self.assertEqual(list(Generate(" ", "This is a test ")), [ "This", "is", "a", "test", '', ])

        self.assertEqual(list(Generate("(?P<delim>\d)", "This1is2a3test")), [ { None : "This", "delim" : '1', }, { None : "is", "delim" : '2', }, { None : "a", "delim" : '3', }, { None : "test", } ])
        self.assertEqual(list(Generate("(?P<delim>\d)", "0This1is2a3test")), [ { None : '', "delim" : '0', }, { None : "This", "delim" : '1', }, { None : "is", "delim" : '2', }, { None : "a", "delim" : '3', }, { None : "test", } ])
        self.assertEqual(list(Generate("(?P<delim>\d)", "This1is2a3test4")), [ { None : "This", "delim" : '1', }, { None : "is", "delim" : '2', }, { None : "a", "delim" : '3', }, { None : "test", "delim" : '4', }, ])
        self.assertEqual(list(Generate("(?P<delim>\d)", "This1is2a3test45")), [ { None : "This", "delim" : '1', }, { None : "is", "delim" : '2', }, { None : "a", "delim" : '3', }, { None : "test", "delim" : '4', }, { None : '', "delim" : '5', }, ])
        self.assertEqual(list(Generate("(?P<delim1>\d)_(?P<delim2>[a-z])_", "This1_a_is2_b_a3_c_test")), [ { None : "This", "delim1" : '1', "delim2" : 'a', }, { None : "is", "delim1" : '2', "delim2" : 'b', }, { None : "a", "delim1" : '3', "delim2" : 'c', }, { None : "test", }, ])
        self.assertEqual(list(Generate("(?P<delim1>\d)_(?P<delim2>[a-z])_", "0_z_This1_a_is2_b_a3_c_test")), [ { None : '', "delim1" : '0', "delim2" : 'z', }, { None : "This", "delim1" : '1', "delim2" : 'a', }, { None : "is", "delim1" : '2', "delim2" : 'b', }, { None : "a", "delim1" : '3', "delim2" : 'c', }, { None : "test", }, ])
        self.assertEqual(list(Generate("(?P<delim1>\d)_(?P<delim2>[a-z])_", "This1_a_is2_b_a3_c_test4_d_")), [ { None : "This", "delim1" : '1', "delim2" : 'a', }, { None : "is", "delim1" : '2', "delim2" : 'b', }, { None : "a", "delim1" : '3', "delim2" : 'c', }, { None : "test", "delim1" : '4', "delim2" : 'd', }, ])
        self.assertEqual(list(Generate("(?P<delim1>\d)_(?P<delim2>[a-z])_", "This1_a_is2_b_a3_c_test4_d_5_e_")), [ { None : "This", "delim1" : '1', "delim2" : 'a', }, { None : "is", "delim1" : '2', "delim2" : 'b', }, { None : "a", "delim1" : '3', "delim2" : 'c', }, { None : "test", "delim1" : '4', "delim2" : 'd', }, { None: '', "delim1" : '5', "delim2" : 'e', }, ])

        self.assertEqual(list(Generate("(?P<delim>\d)", "This1is2a3test", leading_delimiter=True)), [ { None : "This", }, { None : "is", "delim" : '1', }, { None : "a", "delim" : '2', }, { None : "test", "delim" : '3', }, ])
        self.assertEqual(list(Generate("(?P<delim>\d)", "0This1is2a3test", leading_delimiter=True)), [ { None : "This", "delim" : '0', }, { None : "is", "delim" : '1', }, { None : "a", "delim" : '2', }, { None : "test", "delim" : '3', }, ])
        self.assertEqual(list(Generate("(?P<delim>\d)", "This1is2a3test4", leading_delimiter=True)), [ { None : "This", }, { None : "is", "delim" : '1', }, { None : "a", "delim" : '2', }, { None : "test", "delim" : '3', }, { None : '', "delim" : '4', }, ])
        self.assertEqual(list(Generate("(?P<delim>\d)", "This1is2a3test45", leading_delimiter=True)), [ { None : "This", }, { None : "is", "delim" : '1', }, { None : "a", "delim" : '2', }, { None : "test", "delim" : '3', }, { None : '', "delim" : '4', }, { None : '', "delim" : '5', }, ])
        self.assertEqual(list(Generate("(?P<delim1>\d)_(?P<delim2>[a-z])_", "This1_a_is2_b_a3_c_test", leading_delimiter=True)), [ { None : "This", }, { None : "is", "delim1" : '1', "delim2" : 'a', }, { None : "a", "delim1" : '2', "delim2" : 'b', }, { None : "test", "delim1" : '3', "delim2" : 'c', }, ])
        self.assertEqual(list(Generate("(?P<delim1>\d)_(?P<delim2>[a-z])_", "0_z_This1_a_is2_b_a3_c_test", leading_delimiter=True)), [ { None : "This", "delim1" : '0', "delim2" : 'z', }, { None : "is", "delim1" : '1', "delim2" : 'a', }, { None : "a", "delim1" : '2', "delim2" : 'b', }, { None : "test", "delim1" : '3', "delim2" : 'c', }, ])
        self.assertEqual(list(Generate("(?P<delim1>\d)_(?P<delim2>[a-z])_", "This1_a_is2_b_a3_c_test4_d_", leading_delimiter=True)), [ { None : "This", }, { None : "is", "delim1" : '1', "delim2" : 'a', }, { None : "a", "delim1" : '2', "delim2" : 'b', }, { None : "test", "delim1" : '3', "delim2" : 'c', }, { None : '', "delim1" : '4', "delim2" : 'd', }, ])
        self.assertEqual(list(Generate("(?P<delim1>\d)_(?P<delim2>[a-z])_", "This1_a_is2_b_a3_c_test4_d_5_e_", leading_delimiter=True)), [ { None : "This", }, { None : "is", "delim1" : '1', "delim2" : 'a', }, { None : "a", "delim1" : '2', "delim2" : 'b', }, { None : "test", "delim1" : '3', "delim2" : 'c', }, { None: '', "delim1" : '4', "delim2" : 'd', }, { None : '', "delim1" : '5', "delim2" : 'e', }, ])

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
