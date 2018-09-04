# ----------------------------------------------------------------------
# |  
# |  CxFreezeCompiler.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-31 22:29:28
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Creates an executable for a python file"""

import os
import shutil
import sys
import textwrap

from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment import StringHelpers

from CommonEnvironment.CompilerImpl.Impl.DistutilsCompilerImpl import DistutilsCompilerImpl, \
                                                                      CreateCompileMethod, \
                                                                      CreateCleanMethod

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@staticderived
class Compiler(DistutilsCompilerImpl):

    # ----------------------------------------------------------------------
    # |  Public Properties
    Name                                    = DerivedProperty("CxFreezeCompiler")

    # ----------------------------------------------------------------------
    # |  Private Methods
    @classmethod
    @override
    def _GenerateScriptContent(cls, context):
        for attribute_name in [ "comments",
                                "company_name",
                                "internal_name",
                              ]:
            if context[attribute_name]:
                raise Exception("'{}' is not supported by this compiler".format(attribute_name))

        base = "Win32GUI" if CurrentShell.CategoryName == "Windows" and context["build_type"] == cls.BuildType_Windows else "None"
        icon_statement = "# No icon" if not context["icon_filename"] else '"icon" : r"{}",'.format(context["icon_filename"])
        copyright_statement = "# No copyright" if not context["copyright"] else '"copyright" : r"{}",'.format(context["copyright"])
        trademark_statement = "# No trademark" if not context["trademark"] else '"trademark" : r"{}",'.format(context["trademark"])

        executables = []

        for input_filename in context["inputs"]:
            executables.append(textwrap.dedent(
                """\
                Executable( r"{input}",
                            base={base},
                            {icon}
                            {copyright}
                            {trademark}
                          ),
                """).format( input=input_filename,
                             base=base,
                             icon=icon_statement,
                             copyright=copyright_statement,
                             trademark=trademark_statement,
                           ))

        return textwrap.dedent(
            """\
            import sys
            from cx_Freeze import setup, Executable

            {paths}

            setup( name="{name}",
                   version="{version}",
                   description="{description}",
                   options={{ "build_exe" : {{ "optimize" : {optimize},
                                               "packages" : [ {packages} ],
                                               {optional_excludes}
                                               {optional_includes}
                                            }},
                           }},
                   executables=[
                       {executables}
                   ],
                 )
            """).format( paths='\n'.join([ 'sys.path.append("{}")'.format(os.path.abspath(path).replace('\\', '\\\\')) for path in context["paths"] ]),
                         name=context["name"] or os.path.splitext(os.path.basename(context["inputs"][0]))[0],
                         version=context["version"] or "1.0.0.0",
                         description=context["file_description"],
                         optimize="0" if context["no_optimize"] else "2",
                         packages=', '.join([ '"{}"'.format(package) for package in context["packages"] ]),
                         optional_excludes="# No excludes" if not context["excludes"] else '"excludes" : [ {} ],'.format(', '.join([ 'r"{}"'.format(exclude) for exclude in context["excludes"] ])),
                         optional_includes="# No includes" if not context["includes"] else '"includes" : [ {} ],'.format(', '.join([ 'r"{}"'.format(include) for include in context["includes"] ])),
                         executables=StringHelpers.LeftJustify( ''.join(executables),
                                                                len("executables="),
                                                              ),
                       )

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _Compile(cls, context, script_filename, output_stream):
        command_line = 'python "{}" build_exe{}'.format( script_filename,
                                                         '' if not context["distutil_args"] else " {}".format(' '.join([ '"{}"'.format(arg) for arg in context["distutils_args"] ])),
                                                       )


        result = Process.Execute(command_line, output_stream)
        if result == 0:
            if os.path.isdir("build"):
                subdirs = os.listdir("build")
                assert len(subdirs) == 1, subdirs

                source_dir = os.path.join("build", subdirs[0])

                # Remove empty dirs
                to_remove = []

                for root, dirs, _ in os.walk(source_dir):
                    for dir in dirs:
                        fullpath = os.path.join(root, dir)

                        if os.path.isdir(fullpath) and not os.listdir(fullpath):
                            to_remove.append(fullpath)

                for dir in to_remove:
                    FileSystem.RemoveTree(dir)

                FileSystem.RemoveTree(context["output_dir"])
                shutil.move(source_dir, context["output_dir"])
                FileSystem.RemoveTree("build")

        return result

# ----------------------------------------------------------------------
Compile                                     = CreateCompileMethod(Compiler)
Clean                                       = CreateCleanMethod(Compiler)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
