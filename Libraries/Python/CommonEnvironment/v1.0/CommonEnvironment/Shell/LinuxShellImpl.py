# ----------------------------------------------------------------------
# |
# |  LinuxShellImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-11 12:50:32
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains the LinuxShellImpl object"""

import os
import textwrap

from collections import OrderedDict

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.Shell import Shell
from CommonEnvironment.Shell.Commands import Set, Augment, ExitOnError
from CommonEnvironment.Shell.Commands.Visitor import Visitor

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


class LinuxShellImpl(Shell):
    """
    Implements common Linux functionality.

    There are many Linux variations out there; this object can be used as
    a base class when implementing those variations.
    """

    # ----------------------------------------------------------------------
    # |
    # |  Public Types
    # |
    # ----------------------------------------------------------------------
    @staticderived
    @override
    class CommandVisitor(Visitor):

        # <Parameters differ from overridden '<...>' method> pylint: disable = W0221

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnComment(command):
            return "# {}".format(command)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnMessage(command):
            output = []

            for line in command.Value.split("\n"):
                if not line.strip():
                    output.append('echo ""')
                else:
                    output.append('echo "{}"'.format(LinuxShellImpl._ProcessEscapedChars(line, OrderedDict([("$", r"\$"), ('"', r"\"")]))))
            return " && ".join(output)

        # ----------------------------------------------------------------------
        @classmethod
        @override
        def OnCall(cls, command):
            result = "source {}".format(command.CommandLine)
            if command.ExitOnError:
                result += "\n{}".format(cls.Accept(ExitOnError()))

            return result

        # ----------------------------------------------------------------------
        @classmethod
        @override
        def OnExecute(cls, command):
            result = command.CommandLine
            if command.ExitOnError:
                result += "\n{}".format(cls.Accept(ExitOnError()))

            return result

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSymbolicLink(
            command,
            no_dir_flag=False,
            no_relative_flag=False,
        ):
            print(
                "BugBug",
                textwrap.dedent(
                    """\
                    ln -{force_flag}{dir_flag}{relative_flag}s "{target}" "{link}"
                    """,
                ).format(
                    force_flag="" if not command.RemoveExisting else "f",
                    dir_flag="d" if (command.IsDir and not no_dir_flag) else "",
                    relative_flag="r" if (command.RelativePath and not no_relative_flag) else "",
                    target=command.Target,
                    link=command.LinkFilename,
                ),
            )

            return textwrap.dedent(
                """\
                ln -{force_flag}{dir_flag}{relative_flag}s "{target}" "{link}"
                """,
            ).format(
                force_flag="" if not command.RemoveExisting else "f",
                dir_flag="d" if (command.IsDir and not no_dir_flag) else "",
                relative_flag="r" if (command.RelativePath and not no_relative_flag) else "",
                target=command.Target,
                link=command.LinkFilename,
            )

        # ----------------------------------------------------------------------
        @classmethod
        @override
        def OnPath(cls, command):
            return cls.OnSet(Set("PATH", command.Values))

        # ----------------------------------------------------------------------
        @classmethod
        @override
        def OnAugmentPath(cls, command):
            return cls.OnAugment(command)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnSet(command):
            if command.Values is None:
                return "export {}=".format(command.Name)

            return "export {}={}".format(command.Name, os.pathsep.join(command.Values)) # <Class '<name>' has no '<attr>' member> pylint: disable = E1101

            # If here, we don't have a complete list of items

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnAugment(command):
            statements = []

            if command.IsSpaceDelimitedString:
                sep = " "
            else:
                sep = os.pathsep

            if command.AppendValues:
                add_statement_template = "${{{name}}}{sep}{value}"
            else:
                add_statement_template = "{value}{sep}${{{name}}}"

            statements = [
                '''[[ "{sep}${{{name}}}{sep}" != *"{sep}{value}{sep}"* ]] && export {name}="{add_statement}"'''.format(
                    name=command.Name,
                    value=value,
                    sep=sep,
                    add_statement=add_statement_template.format(
                        name=command.Name,
                        value=value,
                        sep=sep,
                    ),
                ) for value in command.Values
            ]

            return "\n".join(statements)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExit(command):
            return textwrap.dedent(
                """\
                {success}
                {error}
                return {return_code}
                """,
            ).format(
                success=textwrap.dedent(
                    """\
                    if [[ $? -eq 0 ]]
                    then
                        read -p "Press [Enter] to continue"
                    fi
                    """,
                ) if command.PauseOnSuccess else "",
                error=textwrap.dedent(
                    """\
                    if [[ $? -ne 0]]
                    then
                        read -p "Press [Enter] to continue"
                    fi
                    """,
                ) if command.PauseOnError else "",
                return_code=command.ReturnCode or 0,
            )

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnExitOnError(command):
            variable_name = "${}".format(command.VariableName) if command.VariableName else "$?"

            return textwrap.dedent(
                """\
                error_code={}
                if [[ $error_code -ne 0 ]]
                then
                    exit {}
                fi
                """,
            ).format(variable_name, command.ReturnCode or "$error_code")

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnRaw(command):
            return command.Value

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnEchoOff(command):
            return ""

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCommandPrompt(command):
            return r'PS1="({}) `id -nu`@`hostname -s`:\w$ "'.format(command.Prompt)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnDelete(command):
            if command.IsDir:
                return 'rm -Rfd "{}"'.format(command.FilenameOrDirectory)

            return 'rm "{}"'.format(command.FilenameOrDirectory)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnCopy(command):
            return 'cp "{source}" "{dest}"'.format(
                source=command.Source,
                dest=command.Dest,
            )

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnMove(command):
            return 'mv "{source}" "{dest}"'.format(
                source=command.Source,
                dest=command.Dest,
            )

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPersistError(command):
            return "{}=$?".format(command.VariableName)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPushDirectory(command):
            directory = command.Directory

            if directory is None:
                directory = """$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"""

            return 'pushd "{}" > /dev/null'.format(directory)

        # ----------------------------------------------------------------------
        @staticmethod
        @override
        def OnPopDirectory(command):
            return "popd > /dev/null"

    # ----------------------------------------------------------------------
    # |
    # |  Public Properties
    # |
    # ----------------------------------------------------------------------
    CategoryName                            = DerivedProperty("Linux")
    ScriptExtension                         = DerivedProperty(".sh")
    ExecutableExtension                     = DerivedProperty("")
    CompressionExtensions                   = DerivedProperty([".tgz", ".tar", "gz"])
    AllArgumentsScriptVariable              = DerivedProperty('"$@"')
    HasCaseSensitiveFileSystem              = DerivedProperty(True)
    Architecture                            = DerivedProperty("x64")                   # I don't know of a reliable, cross-distro way to detect architecture
    UserDirectory                           = DerivedProperty(os.path.expanduser("~"))
    TempDirectory                           = DerivedProperty("/tmp")

    # ----------------------------------------------------------------------
    # |
    # |  Public Methods
    # |
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def IsActive(cls, platform_name):
        # <Class '<name>' has no '<attr>' member> pylint: disable = E1101
        return cls.Name.lower() in platform_name

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def RemoveDir(path):
        if os.path.isdir(path):
            os.system('rm -Rfd "{}"'.format(path))

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def DecorateEnvironmentVariable(var_name):
        return "\\${}".format(var_name)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def UpdateOwnership(
        filename_or_directory,
        recursive=True,
    ):
        if hasattr(os, "geteuid") and os.geteuid() == 0 and not any(var for var in ["SUDO_UID", "SUDO_GID"] if var not in os.environ):
            os.system(
                'chown {recursive} {user}:{group} "{input}"'.format(
                    recursive="--recursive" if recursive and os.path.isdir(filename_or_directory) else "",
                    user=os.environ["SUDO_UID"],
                    group=os.environ["SUDO_GID"],
                    input=filename_or_directory,
                ),
            )

    # ----------------------------------------------------------------------
    # |
    # |  Private Methods
    # |
    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GeneratePrefixCommand():
        return "#!/bin/bash"

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _GenerateSuffixCommand():
        return
