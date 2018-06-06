# ----------------------------------------------------------------------
# |  
# |  StringSerialization_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-26 22:06:18
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
# """Unit test for StringSerialization.py"""

import datetime
import os
import re
import sys
import unittest
import uuid

from CommonEnvironment.TypeInfo.FundamentalTypes.All import *
from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import RegularExpressionVisitor, \
                                                                                          StringSerialization, \
                                                                                          ValidationException

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class RegularExpressionVisitorSuite(unittest.TestCase):
    
    # ----------------------------------------------------------------------
    def test_Standard(self):
        # ----------------------------------------------------------------------
        def Test(method, to_match, regex_index=0):
            if not isinstance(to_match, list):
                to_match = [ to_match, ]

            regex_string = method()[regex_index]
            
            if isinstance(regex_string, tuple):
                regex_string, regex_options = regex_string
            else:
                regex_options = 0

            regex = re.compile("^{}$".format(regex_string), regex_options)

            for index, query in enumerate(to_match):
                self.assertTrue(regex.match(query), "{} did not match {} ({})".format(query, regex_string, index))

        # ----------------------------------------------------------------------

        Test(lambda: RegularExpressionVisitor.OnBool(None), [ "True", "T", "t", "Yes", "yes", "Y", "y", "1", "False", "false", "F", "f", "No", "no", "N", "n", "0", ])
        Test(lambda: RegularExpressionVisitor.OnDateTime(None), [ "2018-04-26 22:29:00", "2018-04-26T22:29:00", "2018-04-26T22:29:00Z", "2018-04-26T22:29:00+08:00", "2018-04-26T22:29:00-10:34", ])
        Test(lambda: RegularExpressionVisitor.OnDate(None), [ "2018-04-26", "2018/04/26", "2018.04.26", ], regex_index=0)
        Test(lambda: RegularExpressionVisitor.OnDate(None), [ "04-26-2018", "04/26/2018", "04.26.2018", ], regex_index=1)
        Test(lambda: RegularExpressionVisitor.OnDate(None), [ "18-04-26", "18/04/26", "18.04.26", ], regex_index=2)
        Test(lambda: RegularExpressionVisitor.OnDate(None), [ "04-26-18", "04/26/18", "04.26.18", ], regex_index=3)
        Test(lambda: RegularExpressionVisitor.OnDirectory(None), "anything")
        Test(lambda: RegularExpressionVisitor.OnDuration(None), [ "1.0:00:00.0", "1:0:00:00.0", "1.00:00:00", "1:00:00.0", "23:22:21", "23:22:21.20", ])
        Test(lambda: RegularExpressionVisitor.OnEnum(EnumTypeInfo([ "one", "two", ])), [ "one", "two", ])
        Test(lambda: RegularExpressionVisitor.OnFilename(None), "anything")
        Test(lambda: RegularExpressionVisitor.OnFloat(FloatTypeInfo()), [ "0.0", "10.2", "-3.14", ])
        Test(lambda: RegularExpressionVisitor.OnGuid(None), "{54465641-ADF2-43B1-98EB-66BBD208622C}", regex_index=0)
        Test(lambda: RegularExpressionVisitor.OnGuid(None), "54465641-ADF2-43B1-98EB-66BBD208622C", regex_index=1)
        Test(lambda: RegularExpressionVisitor.OnGuid(None), "{54465641ADF243B198EB66BBD208622C}", regex_index=2)
        Test(lambda: RegularExpressionVisitor.OnGuid(None), "54465641ADF243B198EB66BBD208622C", regex_index=3)
        Test(lambda: RegularExpressionVisitor.OnInt(IntTypeInfo()), [ "-10", "10", "0", "20", ])
        Test(lambda: RegularExpressionVisitor.OnString(StringTypeInfo()), [ "test", "again", "and another", ])
        Test(lambda: RegularExpressionVisitor.OnTime(None), [ "11:22:33", "11:22:33.44", "11:22:33", ])
        Test(lambda: RegularExpressionVisitor.OnUri(None), "http://one.two.three")

    # ----------------------------------------------------------------------
    def test_Float(self):
        self.assertFalse(re.match("^{}$".format(RegularExpressionVisitor.OnFloat(FloatTypeInfo(min=0))[0]), "-3.0"))
        self.assertFalse(re.match("^{}$".format(RegularExpressionVisitor.OnFloat(FloatTypeInfo(max=0))[0]), "3.0"))
        self.assertFalse(re.match("^{}$".format(RegularExpressionVisitor.OnFloat(FloatTypeInfo(min=0, max=10))[0]), "130.01234"))

    # ----------------------------------------------------------------------
    def test_Int(self):
        self.assertFalse(re.match("^{}$".format(RegularExpressionVisitor.OnInt(IntTypeInfo(min=0))[0]), "-3"))
        self.assertFalse(re.match("^{}$".format(RegularExpressionVisitor.OnInt(IntTypeInfo(max=0))[0]), "3"))
        self.assertFalse(re.match("^{}$".format(RegularExpressionVisitor.OnInt(IntTypeInfo(min=0, max=9))[0]), "130"))

    # ----------------------------------------------------------------------
    def test_String(self):
        regex = re.compile("^{}$".format(RegularExpressionVisitor.OnString(StringTypeInfo(min_length=2))[0]))
        self.assertTrue(regex.match("123"))
        self.assertTrue(regex.match("12"))
        self.assertFalse(regex.match("1"))

        regex = re.compile("^{}$".format(RegularExpressionVisitor.OnString(StringTypeInfo(max_length=2))[0]))
        self.assertTrue(regex.match("12"))
        self.assertFalse(regex.match("123"))

        regex = re.compile("^{}$".format(RegularExpressionVisitor.OnString(StringTypeInfo(min_length=2, max_length=3))[0]))
        self.assertTrue(regex.match("123"))
        self.assertTrue(regex.match("12"))
        self.assertFalse(regex.match("1234"))
        self.assertFalse(regex.match("1"))

        regex = re.compile("^{}$".format(RegularExpressionVisitor.OnString(StringTypeInfo(validation_expression=".est"))[0]))
        self.assertTrue(regex.match("test"))
        self.assertTrue(regex.match("Test"))
        self.assertTrue(regex.match("jest"))
        self.assertFalse(regex.match("tEst"))

# ----------------------------------------------------------------------
class SerializationSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_Bool(self):
        self.assertEqual(StringSerialization.SerializeItem(BoolTypeInfo(), True), "True")
        self.assertEqual(StringSerialization.SerializeItem(BoolTypeInfo(), False), "False")

        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(BoolTypeInfo(), "this is not a bool"))

    # ----------------------------------------------------------------------
    def test_DateTime(self):
        self.assertEqual(StringSerialization.SerializeItem(DateTimeTypeInfo(), datetime.datetime(year=2018, month=4, day=28, hour=14, minute=46, second=12)), "2018-04-28 14:46:12")
        self.assertEqual(StringSerialization.SerializeItem(DateTimeTypeInfo(), datetime.datetime(year=2018, month=4, day=28, hour=14, minute=46, second=12), sep='T'), "2018-04-28T14:46:12")
        self.assertEqual(StringSerialization.SerializeItem(DateTimeTypeInfo(), datetime.datetime(year=2018, month=4, day=28, hour=14, minute=46, second=12, microsecond=3939)), "2018-04-28 14:46:12.003939")
        self.assertEqual(StringSerialization.SerializeItem(DateTimeTypeInfo(), datetime.datetime(year=2018, month=4, day=28, hour=14, minute=46, second=12, microsecond=3939), microseconds=False), "2018-04-28 14:46:12")

        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(DateTimeTypeInfo(), "this is not a datetime"))

    # ----------------------------------------------------------------------
    def test_Date(self):
        self.assertEqual(StringSerialization.SerializeItem(DateTypeInfo(), datetime.date(year=2018, month=4, day=28)), "2018-04-28")
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(DateTypeInfo(), "this is not a valid date"))

    # ----------------------------------------------------------------------
    def test_Directory(self):
        self.assertEqual(StringSerialization.SerializeItem(DirectoryTypeInfo(ensure_exists=False), os.path.join("foo", "bar")), "foo/bar")
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(DirectoryTypeInfo(), os.path.join("foo", "bar")))

    # ----------------------------------------------------------------------
    def test_Duration(self):
        self.assertEqual(StringSerialization.SerializeItem(DurationTypeInfo(), datetime.timedelta(hours=2)), "2:00:00")
        self.assertEqual(StringSerialization.SerializeItem(DurationTypeInfo(), datetime.timedelta(days=1, hours=2)), "1.02:00:00")
        self.assertEqual(StringSerialization.SerializeItem(DurationTypeInfo(), datetime.timedelta(days=1, hours=2), sep=':'), "1:02:00:00")
        self.assertEqual(StringSerialization.SerializeItem(DurationTypeInfo(), datetime.timedelta(days=1, hours=2, microseconds=3456)), "1.02:00:00.003456")

        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(DurationTypeInfo(), "this is not a valid duration"))
        
    # ----------------------------------------------------------------------
    def test_Enum(self):
        self.assertEqual(StringSerialization.SerializeItem(EnumTypeInfo([ "one", "two", ]), "one"), "one")
        self.assertEqual(StringSerialization.SerializeItem(EnumTypeInfo([ "one", "two", ]), "two"), "two")

        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(EnumTypeInfo([ "one", "two", ]), "three"))

    # ----------------------------------------------------------------------
    def test_Filename(self):
        self.assertEqual(StringSerialization.SerializeItem(FilenameTypeInfo(ensure_exists=False), os.path.join("foo", "bar")), "foo/bar")
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(FilenameTypeInfo(), os.path.join("foo", "bar")))

    # ----------------------------------------------------------------------
    def test_Float(self):
        self.assertEqual(StringSerialization.SerializeItem(FloatTypeInfo(), -10.5), "-10.5")
        self.assertEqual(StringSerialization.SerializeItem(FloatTypeInfo(), 10), "10")

        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(FloatTypeInfo(), "this is not a valid float"))
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(FloatTypeInfo(min=0), -10))
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(FloatTypeInfo(max=10), 20))

    # ----------------------------------------------------------------------
    def test_Guid(self):
        self.assertEqual(StringSerialization.SerializeItem(GuidTypeInfo(), uuid.UUID("363D3427-1871-40C5-83DF-3C9D5CE7B60D")), "363D3427-1871-40C5-83DF-3C9D5CE7B60D".lower())
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(GuidTypeInfo(), "this is not a valid guid"))

    # ----------------------------------------------------------------------
    def test_Int(self):
        self.assertEqual(StringSerialization.SerializeItem(IntTypeInfo(), 20), "20")
        self.assertEqual(StringSerialization.SerializeItem(IntTypeInfo(), -20), "-20")

        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(IntTypeInfo(), "this is not a valid int"))
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(IntTypeInfo(min=0), -10))
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(IntTypeInfo(max=10), 20))

    # ----------------------------------------------------------------------
    def test_String(self):
        self.assertEqual(StringSerialization.SerializeItem(StringTypeInfo(), "test"), "test")

        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(StringTypeInfo(), 10))
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(StringTypeInfo(min_length=2), "1"))
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(StringTypeInfo(max_length=2), "123"))
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(StringTypeInfo(validation_expression="test"), "TEST"))

    # ----------------------------------------------------------------------
    def test_Time(self):
        self.assertEqual(StringSerialization.SerializeItem(TimeTypeInfo(), datetime.time(hour=15, minute=15, second=12)), "15:15:12")
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(TimeTypeInfo(), "this is not a valid time"))

    # ----------------------------------------------------------------------
    def test_Uri(self):
        self.assertEqual(StringSerialization.SerializeItem(UriTypeInfo(), Uri.FromString("https://foo.bar.baz")), "https://foo.bar.baz")
        self.assertRaises(ValidationException, lambda: StringSerialization.SerializeItem(UriTypeInfo(), "this is not a valid uri"))

# ----------------------------------------------------------------------
class DeserializationSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_Bool(self):
        self.assertTrue(StringSerialization.DeserializeItem(BoolTypeInfo(), "true"))
        self.assertTrue(StringSerialization.DeserializeItem(BoolTypeInfo(), "t"))
        self.assertTrue(StringSerialization.DeserializeItem(BoolTypeInfo(), "yes"))
        self.assertTrue(StringSerialization.DeserializeItem(BoolTypeInfo(), "y"))
        self.assertTrue(StringSerialization.DeserializeItem(BoolTypeInfo(), "1"))

        self.assertFalse(StringSerialization.DeserializeItem(BoolTypeInfo(), "false"))
        self.assertFalse(StringSerialization.DeserializeItem(BoolTypeInfo(), "f"))
        self.assertFalse(StringSerialization.DeserializeItem(BoolTypeInfo(), "no"))
        self.assertFalse(StringSerialization.DeserializeItem(BoolTypeInfo(), "n"))
        self.assertFalse(StringSerialization.DeserializeItem(BoolTypeInfo(), "0"))

        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(BoolTypeInfo(), "not_valid"))

    # ----------------------------------------------------------------------
    def test_DateTime(self):
        self.assertEqual(StringSerialization.DeserializeItem(DateTimeTypeInfo(), "2018-04-28 10:05:00"), datetime.datetime(year=2018, month=4, day=28, hour=10, minute=5, second=0))
        self.assertEqual(StringSerialization.DeserializeItem(DateTimeTypeInfo(), "2018-04-28T10:05:00"), datetime.datetime(year=2018, month=4, day=28, hour=10, minute=5, second=0))
        self.assertEqual(StringSerialization.DeserializeItem(DateTimeTypeInfo(), "1528171793"), datetime.datetime(2018, 6, 5, 4, 9, 53))
        self.assertEqual(StringSerialization.DeserializeItem(DateTimeTypeInfo(), "@1528171793 -0700"), datetime.datetime(2018, 6, 5, 11, 9, 53))
        self.assertEqual(StringSerialization.DeserializeItem(DateTimeTypeInfo(), "@1528171793 +0700"), datetime.datetime(2018, 6, 4, 21, 9, 53))
        self.assertEqual(StringSerialization.DeserializeItem(DateTimeTypeInfo(), "@1528171793 0700"), datetime.datetime(2018, 6, 4, 21, 9, 53))
        
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(DateTimeTypeInfo(), "not a valid datetime"))

    # ----------------------------------------------------------------------
    def test_Date(self):
        self.assertEqual(StringSerialization.DeserializeItem(DateTypeInfo(), "2018-04-28"), datetime.date(year=2018, month=4, day=28))
        self.assertEqual(StringSerialization.DeserializeItem(DateTypeInfo(), "04-28-2018"), datetime.date(year=2018, month=4, day=28))
        self.assertEqual(StringSerialization.DeserializeItem(DateTypeInfo(), "18-04-28"), datetime.date(year=2018, month=4, day=28))
        self.assertEqual(StringSerialization.DeserializeItem(DateTypeInfo(), "04-28-18"), datetime.date(year=2018, month=4, day=28))

        self.assertEqual(StringSerialization.DeserializeItem(DateTypeInfo(), "2018.04.28"), datetime.date(year=2018, month=4, day=28))
        self.assertEqual(StringSerialization.DeserializeItem(DateTypeInfo(), "04.28.2018"), datetime.date(year=2018, month=4, day=28))
        self.assertEqual(StringSerialization.DeserializeItem(DateTypeInfo(), "18.04.28"), datetime.date(year=2018, month=4, day=28))
        self.assertEqual(StringSerialization.DeserializeItem(DateTypeInfo(), "04.28.18"), datetime.date(year=2018, month=4, day=28))

        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(DateTimeTypeInfo(), "2018-04.28"))

    # ----------------------------------------------------------------------
    def test_Directory(self):
        self.assertEqual(StringSerialization.DeserializeItem(DirectoryTypeInfo(ensure_exists=False), "foo/bar"), os.path.realpath(os.path.normpath(os.path.join("foo", "bar"))))
        self.assertEqual(StringSerialization.DeserializeItem(DirectoryTypeInfo(ensure_exists=False), "foo/bar", normalize=False), os.path.join("foo", "bar"))

        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(DirectoryTypeInfo(), ''))

    # ----------------------------------------------------------------------
    def test_Duration(self):
        self.assertEqual(StringSerialization.DeserializeItem(DurationTypeInfo(), "1.02:03:04"), datetime.timedelta(days=1, hours=2, minutes=3, seconds=4))
        self.assertEqual(StringSerialization.DeserializeItem(DurationTypeInfo(), "1:02:03:04"), datetime.timedelta(days=1, hours=2, minutes=3, seconds=4))
        self.assertEqual(StringSerialization.DeserializeItem(DurationTypeInfo(), "02:03:04"), datetime.timedelta(hours=2, minutes=3, seconds=4))
        self.assertEqual(StringSerialization.DeserializeItem(DurationTypeInfo(), "1.02:03:04.5"), datetime.timedelta(days=1, hours=2, minutes=3, seconds=4, microseconds=5))
        self.assertEqual(StringSerialization.DeserializeItem(DurationTypeInfo(), "1:02:03:04.5"), datetime.timedelta(days=1, hours=2, minutes=3, seconds=4, microseconds=5))
        self.assertEqual(StringSerialization.DeserializeItem(DurationTypeInfo(), "02:03:04.5"), datetime.timedelta(hours=2, minutes=3, seconds=4, microseconds=5))

        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(DurationTypeInfo(), "not a valid duration"))

    # ----------------------------------------------------------------------
    def test_Enum(self):
        self.assertEqual(StringSerialization.DeserializeItem(EnumTypeInfo([ "one", "two", ]), "one"), "one")
        self.assertEqual(StringSerialization.DeserializeItem(EnumTypeInfo([ "one", "two", ]), "two"), "two")

        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(EnumTypeInfo([ "one", "two", ]), "three"))

    # ----------------------------------------------------------------------
    def test_Filename(self):
        self.assertEqual(StringSerialization.DeserializeItem(FilenameTypeInfo(ensure_exists=False), "foo/bar"), os.path.realpath(os.path.normpath(os.path.join("foo", "bar"))))
        self.assertEqual(StringSerialization.DeserializeItem(FilenameTypeInfo(ensure_exists=False), "foo/bar", normalize=False), os.path.join("foo", "bar"))

        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(DirectoryTypeInfo(), ''))

    # ----------------------------------------------------------------------
    def test_Float(self):
        self.assertEqual(StringSerialization.DeserializeItem(FloatTypeInfo(), "10.5"), 10.5)
        self.assertEqual(StringSerialization.DeserializeItem(FloatTypeInfo(), "10"), 10.0)
        self.assertEqual(StringSerialization.DeserializeItem(FloatTypeInfo(), "-10.5"), -10.5)

        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(FloatTypeInfo(), "not a valid float"))
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(FloatTypeInfo(min=0), "-10.5"))
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(FloatTypeInfo(max=10), "100.5"))

    # ----------------------------------------------------------------------
    def test_Guid(self):
        self.assertEqual(StringSerialization.DeserializeItem(GuidTypeInfo(), "{9A3A5A9A-0755-4FAC-9019-176C609665C5}"), uuid.UUID("9A3A5A9A-0755-4FAC-9019-176C609665C5"))
        self.assertEqual(StringSerialization.DeserializeItem(GuidTypeInfo(), "9A3A5A9A-0755-4FAC-9019-176C609665C5"), uuid.UUID("9A3A5A9A-0755-4FAC-9019-176C609665C5"))
        self.assertEqual(StringSerialization.DeserializeItem(GuidTypeInfo(), "{9A3A5A9A07554FAC9019176C609665C5}"), uuid.UUID("9A3A5A9A-0755-4FAC-9019-176C609665C5"))
        self.assertEqual(StringSerialization.DeserializeItem(GuidTypeInfo(), "9A3A5A9A07554FAC9019176C609665C5"), uuid.UUID("9A3A5A9A-0755-4FAC-9019-176C609665C5"))

        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(GuidTypeInfo(), "not a valid guid"))

    # ----------------------------------------------------------------------
    def test_Int(self):
        self.assertEqual(StringSerialization.DeserializeItem(IntTypeInfo(), "10"), 10)
        self.assertEqual(StringSerialization.DeserializeItem(IntTypeInfo(), "-10"), -10)

        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(IntTypeInfo(), "not a valid int"))
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(IntTypeInfo(min=0), "-10"))
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(IntTypeInfo(max=10), "100"))

    # ----------------------------------------------------------------------
    def test_String(self):
        self.assertEqual(StringSerialization.DeserializeItem(StringTypeInfo(), "foo"), "foo")
        
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(StringTypeInfo(), ""))
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(StringTypeInfo(min_length=2), "1"))
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(StringTypeInfo(max_length=2), "123"))
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(StringTypeInfo(validation_expression="test"), "not test"))

    # ----------------------------------------------------------------------
    def test_Time(self):
        self.assertEqual(StringSerialization.DeserializeItem(TimeTypeInfo(), "10:15:01"), datetime.time(hour=10, minute=15, second=1))
        self.assertEqual(StringSerialization.DeserializeItem(TimeTypeInfo(), "10:15:01.678"), datetime.time(hour=10, minute=15, second=1, microsecond=678000))
        
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(TimeTypeInfo(), "not a valid time"))
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(TimeTypeInfo(), "10:15:01+10:30"))
        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(TimeTypeInfo(), "10:15:01-03:13"))

    # ----------------------------------------------------------------------
    def test_Uri(self):
        self.assertEqual(StringSerialization.DeserializeItem(UriTypeInfo(), "https://foo.bar.baz"), Uri.FromString("https://foo.bar.baz"))

        self.assertRaises(ValidationException, lambda: StringSerialization.DeserializeItem(UriTypeInfo(), "not a valid uri"))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass