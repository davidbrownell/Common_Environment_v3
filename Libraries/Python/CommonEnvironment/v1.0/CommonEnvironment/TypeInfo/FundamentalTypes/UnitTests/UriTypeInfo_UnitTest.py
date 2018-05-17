# ----------------------------------------------------------------------
# |  
# |  UriTypeInfo_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 13:08:18
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for UriTypeInfo.py."""

import os
import sys
import unittest

from CommonEnvironment.TypeInfo.FundamentalTypes.UriTypeInfo import Uri, UriTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class UriSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_FromString(self):
        # ----------------------------------------------------------------------
        def Test(value, scheme, host, path, query, credentials, port):
            uri = Uri.FromString(value)
            self.assertEqual(uri.Scheme, scheme)
            self.assertEqual(uri.Host, host)
            self.assertEqual(uri.Path, path)
            self.assertEqual(uri.Query, query)
            self.assertEqual(uri.Credentials, credentials)
            self.assertEqual(uri.Port, port)

        # ----------------------------------------------------------------------

        Test("http://foo.bar.com", "http", "foo.bar.com", None, {}, None, None)
        Test("https://foo.bar.com:80", "https", "foo.bar.com", None, {}, None, 80)
        Test("http://username:password@foo.bar.com/", "http", "foo.bar.com", "/", {}, ("username", "password"), None)
        Test("http://foo.bar.com/p1/p2", "http", "foo.bar.com", "/p1/p2", {}, None, None)
        Test("http://foo.bar.com/p1/p2?foo=bar&baz=biz", "http", "foo.bar.com", "/p1/p2", { "foo" : [ "bar", ], "baz" : [ "biz", ], }, None, None)

    # ----------------------------------------------------------------------
    def test_ToString(self):
        self.assertEqual(Uri("https", "foo.bar.com", None).ToString(), "https://foo.bar.com")
        self.assertEqual(Uri("https", "foo.bar.com", "/").ToString(), "https://foo.bar.com/")
        self.assertEqual(Uri("https", "foo.bar.com", None, port=80).ToString(), "https://foo.bar.com:80")
        self.assertEqual(Uri("https", "foo.bar.com", None, credentials=("username", "p@ssword:\\")).ToString(), "https://username:p%40ssword%3A%5C@foo.bar.com")
        self.assertEqual(Uri("https", "foo.bar.com", None, query={ "foo" : "b@r", }).ToString(), "https://foo.bar.com?foo=b%40r")
        self.assertEqual(Uri("https", "foo.bar.com", "p1/p2", query={ "foo" : "b@r", }).ToString(), "https://foo.bar.com/p1/p2?foo=b%40r")

    # ----------------------------------------------------------------------
    def test_ConstructErrors(self):
        self.assertRaises(Exception, lambda: Uri("", "foo.bar.com", "/"))
        self.assertRaises(Exception, lambda: Uri("http", "", "/"))

# ----------------------------------------------------------------------
class UriTypeInfoSuite(unittest.TestCase):

    # ----------------------------------------------------------------------
    def test_Standard(self):
        self.assertEqual(UriTypeInfo.Desc, "Uri")
        self.assertEqual(UriTypeInfo.ConstraintsDesc, '')
        self.assertEqual(UriTypeInfo.ExpectedType, Uri)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass
