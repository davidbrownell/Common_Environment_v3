# ----------------------------------------------------------------------
# |  
# |  FileSystem_UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-03 21:35:13
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for FileSystem.py."""

import os
import sys
import unittest

from CommonEnvironment.FileSystem import *
from CommonEnvironment.Shell.All import CurrentShell

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class StandardSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_GetCommonPath(self):
        self.assertEqual( GetCommonPath( os.path.join("one", "two", "three"),
                                         os.path.join("one", "two", "th"),
                                       ), 
                          "{}{}".format( os.path.realpath(os.path.join("one", "two")),
                                         os.path.sep,
                                       ),
                        )
        self.assertEqual( GetCommonPath( os.path.join("one", "two", "three"),
                                         os.path.join("one", "two", "3"),
                                       ), 
                          "{}{}".format( os.path.realpath(os.path.join("one", "two")),
                                         os.path.sep,
                                       ),
                        )
        self.assertEqual(GetCommonPath(), '')
        self.assertEqual(GetCommonPath(_script_fullpath), "{}{}".format(_script_dir, os.path.sep))
        self.assertEqual(GetCommonPath(_script_dir), "{}{}".format(_script_dir, os.path.sep))

        if not CurrentShell.HasCaseSensitiveFileSystem:
            self.assertEqual( GetCommonPath( os.path.join("one", "two", "trhee"),
                                             os.path.join("one", "TWO", "3"),
                                           ),
                              "{}{}".format( os.path.realpath(os.path.join("one", "two")),
                                             os.path.sep,
                                           ),
                            )
            self.assertEqual( GetCommonPath( os.path.join("one", "TWO", "trhee"),
                                             os.path.join("one", "two", "3"),
                                           ),
                              "{}{}".format( os.path.realpath(os.path.join("one", "TWO")),
                                             os.path.sep,
                                           ),
                            )

    # ----------------------------------------------------------------------
    def test_GetRelativePath(self):
        self.assertEqual( GetRelativePath( os.path.join("one", "two", "three"),
                                           os.path.join("one", "two", "three", "four"),
                                         ),
                          os.path.join(".", "four"),
                        )

        self.assertEqual( GetRelativePath( os.path.join("one", "two"),
                                           os.path.join("one", "two", "three", "four"),
                                         ),
                          os.path.join(".", "three", "four"),
                        )

        self.assertEqual( GetRelativePath( os.path.join("one", "two", "other"),
                                           os.path.join("one", "two", "three", "four"),
                                         ),
                          os.path.join("..", "three", "four"),
                        )

        self.assertEqual( GetRelativePath( os.path.join("one", "two", "other1", "other2"),
                                           os.path.join("one", "two", "three", "four"),
                                         ),
                          os.path.join("..", "..", "three", "four"),
                        )
        self.assertEqual( GetRelativePath( os.path.join("one", "2"),
                                           os.path.join("one", "two", "three", "four"),
                                         ),
                          os.path.join("..", "two", "three", "four"),
                        )

        self.assertEqual( GetRelativePath( os.path.join("1", "2"),
                                           os.path.join("one", "two", "three", "four"),
                                         ),
                          os.path.join("..", "..", "one", "two", "three", "four"),
                        )

        self.assertEqual( GetRelativePath( os.path.join("one", "two"),
                                           os.path.join("one", "two"),
                                         ),
                          ".",
                        )

    # ----------------------------------------------------------------------
    def test_AddTrailingSep(self):
        self.assertEqual(AddTrailingSep("foo"), "foo{}".format(os.path.sep))
        self.assertEqual(AddTrailingSep("foo{}".format(os.path.sep)), "foo{}".format(os.path.sep))

    # ----------------------------------------------------------------------
    def test_GetSizeDisplay(self):
        self.assertEqual(GetSizeDisplay(1000), "1000.0 B")
        self.assertEqual(GetSizeDisplay(10000), "9.8 KB")
        self.assertEqual(GetSizeDisplay(100000), "97.7 KB")
        self.assertEqual(GetSizeDisplay(1000000), "976.6 KB")
        self.assertEqual(GetSizeDisplay(10000000), "9.5 MB")
        self.assertEqual(GetSizeDisplay(100000000), "95.4 MB")
        self.assertEqual(GetSizeDisplay(1000000000), "953.7 MB")
        self.assertEqual(GetSizeDisplay(10000000000), "9.3 GB")
        self.assertEqual(GetSizeDisplay(100000000000000000), "88.8 PB")
        self.assertEqual(GetSizeDisplay(1000000000000000000000), "867.4 EB")
        self.assertEqual(GetSizeDisplay(10000000000000000000000000), "8.3 YiB")
        self.assertEqual(GetSizeDisplay(1000000000000000000000000000000), "827180.6 YiB")

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass