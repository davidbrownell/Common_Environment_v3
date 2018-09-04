# ----------------------------------------------------------------------
# |  
# |  __init___UnitTest.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-01 16:19:37
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Unit test for __init__.py."""

import os
import shutil
import sys
import unittest

from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.Shell import *
from CommonEnvironment.Shell.Commands import *

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class MyShell(Shell):
    Name                                    = DerivedProperty("MyShell")
    CategoryName                            = DerivedProperty("MyCategory")
    ScriptExtension                         = DerivedProperty(".AScriptExt")
    ExecutableExtension                     = DerivedProperty(".AExeExt")
    AllArgumentsScriptVariable              = DerivedProperty("_all_args_")
    HasCaseSensitiveFileSystem              = DerivedProperty(True)
    Architecture                            = DerivedProperty("987")
    UserDirectory                           = DerivedProperty("<user>")
    TempDirectory                           = DerivedProperty("<temp>")
    CompressionExtensions                   = DerivedProperty([ ".compressed", ])

    @override
    class CommandVisitor(object):
        @staticmethod
        @override
        def Accept(command):
            return command.Value if hasattr(command, "Value") else str(command)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def IsActive(platform_name):
        return True

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def RemoveDir(path):
        pass

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def DecorateEnvironmentVariable(var_name):
        return var_name

# ----------------------------------------------------------------------
class StandardSuite(unittest.TestCase):
    # ----------------------------------------------------------------------
    def test_GenerateCommands(self):
        self.assertEqual(MyShell.GenerateCommands([ Message("one"), Message("two"), ]), "one\ntwo")
        self.assertEqual(MyShell.GenerateCommands(Message("one")), "one")

    # ----------------------------------------------------------------------
    def test_EnumEnvironmentVariable(self):
        var_name = "{}_var".format(_script_name)

        self.assertTrue(var_name not in os.environ)

        values = [ "one", "two", "three", ]

        os.environ[var_name] = os.pathsep.join(values)
        
        self.assertEqual(list(MyShell.EnumEnvironmentVariable(var_name)), values)

    # ----------------------------------------------------------------------
    def test_CreateScriptName(self):
        self.assertEqual(MyShell.CreateScriptName("foo"), "foo.AScriptExt")

    # ----------------------------------------------------------------------
    def test_CreateExecutableName(self):
        self.assertEqual(MyShell.CreateExecutableName("bar"), "bar.AExeExt")

    # ----------------------------------------------------------------------
    def test_CreateTempFilename(self):
        self.assertNotEqual(MyShell.CreateTempFilename(), "")

    # ----------------------------------------------------------------------
    def test_CreateTempDirectory(self):
        directory = MyShell.CreateTempDirectory("-baz")
        self.assertTrue(os.path.isdir(directory))
        shutil.rmtree(directory)

    # ----------------------------------------------------------------------
    def test_MakeFileExecutable(self):
        filename = MyShell.CreateTempFilename(MyShell.ExecutableExtension)

        with open(filename, 'w') as f:
            f.write("Content")

        MyShell.MakeFileExecutable(filename)
        os.remove(filename)

    # ----------------------------------------------------------------------
    def test_CreateDataFilename(self):
        filename = MyShell.CreateDataFilename("MyApp")
        self.assertEqual(filename, os.path.join(MyShell.UserDirectory, "MyApp.bin"))

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(unittest.main(verbosity=2))
    except KeyboardInterrupt: pass