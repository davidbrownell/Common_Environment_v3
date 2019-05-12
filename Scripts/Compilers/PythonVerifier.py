# ----------------------------------------------------------------------
# |  
# |  PythonVerifier.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-19 22:39:08
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Verifies Python source code using PyLint"""

import os
import re
import sys
import textwrap

import inflect as inflect_mod
import six

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.StreamDecorator import StreamDecorator

from CommonEnvironment.CompilerImpl import Verifier as VerifierMod
from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
@staticderived
class Verifier(VerifierMod.Verifier):
    """Verifies Python source code using PyLint"""

    # ----------------------------------------------------------------------
    # |  
    # |  Public Properties
    # |  
    # ----------------------------------------------------------------------
    Name                                    = DerivedProperty("PyLint")
    Description                             = DerivedProperty("Statically analyzes Python source code, reporting common mistakes and errors.")
    InputTypeInfo                           = DerivedProperty(FilenameTypeInfo(validation_expression=r".+?\.py"))

    DEFAULT_PASSING_SCORE                   = 9.0

    # Environment variable name of a custom PyLint configuration file. A default
    # configuration file will be used if this environment variable isn't defined.
    CONFIGURATION_ENVIRONMENT_VAR_NAME      = "DEVELOPMENT_ENVIRONMENT_PYTHON_VERIFIER_CONFIGURATION"

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def ItemToTestName(item_name, test_type_name):
        dirname, basename = os.path.split(item_name)
        name, ext = os.path.splitext(basename)

        if name.endswith("Impl"):
            return None

        if name == "__init__" and ext == ".py" and os.path.getsize(item_name) == 0:
            return None

        return os.path.join(dirname, test_type_name, "{}_{}{}".format( name,
                                                                       inflect.singular_noun(test_type_name) or test_type_name,
                                                                       ext,
                                                                     ))

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def TestToItemName(test_filename):
        dirname, basename = os.path.split(test_filename)

        match = re.match( r"^(?P<name>.+)_(?P<test_type>[^_\.]+Test)(?P<ext>\..+)$",
                          basename,
                        )
        if not match:
            raise Exception("'{}' is not a recognized test name".format(test_filename))

        name = "{}{}".format(match.group("name"), match.group("ext"))
        test_type = match.group("test_type")

        if dirname and os.path.basename(dirname) == inflect.plural(test_type):
            dirname = os.path.dirname(dirname)

        filename = os.path.join(dirname, name)
        if not os.path.isfile(filename):
            # Is this a module name?
            potential_module_name = os.path.join(os.path.dirname(filename), "__init__.py")
            if os.path.isfile(potential_module_name):
                filename = potential_module_name
            
        return filename

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def IsSupportedTestItem(item):
        return os.path.basename(item) not in ["__init__.py", "Build.py"]

    # ----------------------------------------------------------------------
    # |  
    # |  Private Methods
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _GetOptionalMetadata(cls):
        return [ ( "passing_score", None ),
               ] + super(Verifier, cls)._GetOptionalMetadata()

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _CreateContext(cls, metadata):
        if metadata["passing_score"] is None:
            metadata["passing_score"] = cls.DEFAULT_PASSING_SCORE
            metadata["explicit_passing_score"] = False
        else:
            metadata["explicit_passing_score"] = True

        return super(Verifier, cls)._CreateContext(metadata)

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def _InvokeImpl( cls,
                     invoke_reason,
                     context,
                     status_stream,
                     verbose_stream,
                     verbose,
                   ):
        # If the file is being invoked as a test file, measure the file under test
        # rather than the test itself.
        filename = context["input"]

        try:
            filename = cls.TestToItemName(filename)
        except:
            pass

        assert os.path.isfile(filename), filename

        if os.path.basename(filename) == "__init__.py" and os.path.getsize(filename) == 0:
            return 0

        # Create the lint file
        configuration_file = os.getenv(cls.CONFIGURATION_ENVIRONMENT_VAR_NAME) or os.path.join(_script_dir, "PythonVerifier.default_configuration")
        assert os.path.isfile(configuration_file), configuration_file

        # Write the python script that invokes the linter
        temp_filename = CurrentShell.CreateTempFilename(".py")
        with open(temp_filename, 'w') as f:
            f.write(textwrap.dedent(
                """\
                import sys

                from pylint import lint

                lint.Run([ r"--rcfile={config}",
                           r"--msg-template={{path}}({{line}}): [{{msg_id}}] {{msg}}",
                           r"{filename}",
                         ])
                """).format( config=configuration_file,
                             filename=filename,
                           ))

        with CallOnExit(lambda: FileSystem.RemoveFile(temp_filename)):
            # Run the generated file
            command_line = 'python "{}"'.format(temp_filename)

            sink = six.moves.StringIO()
            output_stream = StreamDecorator([ sink, verbose_stream, ])

            regex_sink = six.moves.StringIO()
            Process.Execute(command_line, StreamDecorator([ regex_sink, output_stream, ]))
            regex_sink = regex_sink.getvalue()

            result = 0

            # Extract the results
            match = re.search( r"Your code has been rated at (?P<score>[-\d\.]+)/(?P<max>[\d\.]+)", 
                               regex_sink,
                               re.MULTILINE,
                             )

            if not match:
                result = -1
            else:
                score = float(match.group("score"))
                max_score = float(match.group("max"))
                assert max_score != 0.0

                # Don't measure scores for files in Impl directories
                is_impl_file = os.path.basename(filename).endswith("Impl")

                if is_impl_file and not context["explicit_passing_score"]:
                    passing_score = None
                else:
                    passing_score = context["passing_score"]

                output_stream.write(textwrap.dedent(
                    """\
                    Score:                  {score} (out of {max_score})
                    Passing Score:          {passing_score}{explicit}

                    """).format( score=score,
                                 max_score=max_score,
                                 passing_score=passing_score,
                                 explicit=" (explicitly provided)" if context["explicit_passing_score"] else '',
                               ))

                if passing_score is not None and score < passing_score:
                    result = -1

            if result != 0 and not verbose:
                status_stream.write(sink.getvalue())

            return result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( input=CommandLine.FilenameTypeInfo(match_any=True, arity='+'),
                          passing_score=CommandLine.FloatTypeInfo(min=0.0, max=10.0, arity='?'),
                          output_stream=None,
                        )
def CommandLineVerify( input,                          # <Redefinig built-in type> pylint: disable = W0622
            passing_score=None,
            output_stream=sys.stdout,
            verbose=False,
          ):
    """Verifies the given python input"""

    inputs = input; del input

    return VerifierMod.CommandLineVerify( Verifier,
                                          inputs,
                                          StreamDecorator(output_stream),
                                          verbose,
                                          passing_score=passing_score,
                                        )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
