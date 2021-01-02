# ----------------------------------------------------------------------
# |
# |  HookImpl.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-06-04 07:58:48
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-21.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Implements functionality common to all hooks"""

import json
import os
import sys

from collections import OrderedDict

# ----------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from RepositoryBootstrap import GetFundamentalRepository as _GetFundamentalRepository
sys.path.pop(0)

# ----------------------------------------------------------------------
def Invoke(repo_root, output_stream, method, json_content, is_debug):
    fundamental_root = _GetFundamentalRepository()

    # Imports here can be tricky
    try:
        sys.path.insert(0, fundamental_root)

        from RepositoryBootstrap import Constants
        from RepositoryBootstrap.Impl import CommonEnvironmentImports
        from RepositoryBootstrap.Impl.EnvironmentBootstrap import EnvironmentBootstrap

        sys.path.pop(0)
    except:
        import traceback

        output_stream.write(traceback.format_exc())
        raise

    output_stream = CommonEnvironmentImports.StreamDecorator(output_stream)

    output_stream.write("Getting configurations...")
    with output_stream.DoneManager() as dm:
        # Is this a mixin repo?
        activation_root = repo_root

        # ----------------------------------------------------------------------
        def GetBootstrapFilename():
            for root, dirs, filenames in os.walk(os.path.join(repo_root, Constants.GENERATED_DIRECTORY_NAME, CommonEnvironmentImports.CurrentShell.CategoryName)):
                for filename in filenames:
                    if filename == Constants.GENERATED_BOOTSTRAP_JSON_FILENAME:
                        return os.path.join(root, filename)

            return None

        # ----------------------------------------------------------------------

        bootstrap_filename = GetBootstrapFilename()
        if bootstrap_filename is not None:
            with open(bootstrap_filename) as f:
                bootstrap_data = json.load(f)

            if bootstrap_data["is_mixin_repo"]:
                activation_root = fundamental_root

        activation_script = os.path.join(activation_root, CommonEnvironmentImports.CurrentShell.CreateScriptName(Constants.ACTIVATE_ENVIRONMENT_NAME))
        if not os.path.isfile(activation_script):
            output_stream.write("ERROR: The filename '{}' was not found.\n".format(activation_script))
            return -1

        result, output = CommonEnvironmentImports.Process.Execute("{} ListConfigurations json".format(activation_script))
        assert result == 0, output

        data = json.loads(output, object_pairs_hook=OrderedDict)

        configurations = list(data.keys())
        if not configurations:
            configurations = [ None, ]

    # Process the configurations
    output_stream.write("Processing configurations...")
    with output_stream.DoneManager( suffix='\n',
                                  ) as dm:
        display_sentinel = "Display?!__"

        json_filename = CommonEnvironmentImports.CurrentShell.CreateTempFilename(".json")
        with open(json_filename, 'w') as f:
            json.dump(json_content, f)

        with CommonEnvironmentImports.CallOnExit(lambda: os.remove(json_filename)):
            original_environment = None

            if os.getenv(Constants.DE_REPO_GENERATED_NAME):
                # This code sucks because it is hard coding names and duplicating logic in Activate.py. However, importing
                # Activate here is causing problems as the Mercurial version of python is different enough from out
                # version that some imports don't work between python 2 and python 3.
                original_data_filename = os.path.join(os.getenv(Constants.DE_REPO_GENERATED_NAME), "EnvironmentActivation.OriginalEnvironment.json")
                assert os.path.isfile(original_data_filename), original_data_filename

                with open(original_data_filename) as f:
                    original_environment = json.load(f)


            terminate = False

            for index, configuration in enumerate(configurations):
                dm.stream.write("Configuration '{}' ({} of {})...".format( configuration if configuration else "<default>",
                                                                           index + 1,
                                                                           len(configurations),
                                                                         ))
                with dm.stream.DoneManager() as this_dm:
                    if terminate:
                        continue

                    result_filename = CommonEnvironmentImports.CurrentShell.CreateTempFilename()

                    # ----------------------------------------------------------------------
                    def RemoveResultFilename():
                        if os.path.isfile(result_filename):
                            os.remove(result_filename)

                    # ----------------------------------------------------------------------

                    with CommonEnvironmentImports.CallOnExit(RemoveResultFilename):
                        # We are potentially operating in a limited environment. Rather than
                        # attempting to invoke hook functionality here, activate an environment
                        # and run the functionality there.
                        commands = [ CommonEnvironmentImports.CurrentShell.Commands.EchoOff(),
                                     CommonEnvironmentImports.CurrentShell.Commands.Raw('cd "{}"'.format(os.path.dirname(activation_script))),
                                     CommonEnvironmentImports.CurrentShell.Commands.Call("{} {} /fast".format(os.path.basename(activation_script), configuration if configuration else '')),
                                     CommonEnvironmentImports.CurrentShell.Commands.ExitOnError(-1),
                                     CommonEnvironmentImports.CurrentShell.Commands.Augment("PYTHONPATH", fundamental_root),
                                     CommonEnvironmentImports.CurrentShell.Commands.PushDirectory(repo_root),
                                     CommonEnvironmentImports.CurrentShell.Commands.Raw('python -m RepositoryBootstrap.Impl.Hooks.HookScript "{method}" "{sentinel}" "{json_filename}" "{result_filename}"{first}' \
                                                                                            .format( method=method,
                                                                                                     sentinel=display_sentinel,
                                                                                                     json_filename=json_filename,
                                                                                                     result_filename=result_filename,
                                                                                                     first=" /first" if index == 0 else '',
                                                                                                   )),
                                     CommonEnvironmentImports.CurrentShell.Commands.ExitOnError(-1),
                                   ]

                        script_filename = CommonEnvironmentImports.CurrentShell.CreateTempFilename(CommonEnvironmentImports.CurrentShell.ScriptExtension)
                        with open(script_filename, 'w') as f:
                            f.write(CommonEnvironmentImports.CurrentShell.GenerateCommands(commands))

                        with CommonEnvironmentImports.CallOnExit(lambda: os.remove(script_filename)):
                            CommonEnvironmentImports.CurrentShell.MakeFileExecutable(script_filename)

                            content = []

                            # ----------------------------------------------------------------------
                            def Display(value):
                                if value.startswith(display_sentinel):
                                    stripped_value = value.replace(display_sentinel, '')

                                    this_dm.stream.write(stripped_value)
                                    this_dm.stream.flush()

                                content.append(value)

                            # ----------------------------------------------------------------------

                            this_dm.result = CommonEnvironmentImports.Process.Execute( script_filename,
                                                                                       Display,
                                                                                       line_delimited_output=True,
                                                                                       environment=original_environment,
                                                                                     )

                            if is_debug or this_dm.result == -1 or not os.path.isfile(result_filename):
                                this_dm.stream.write(''.join(content))

                                if this_dm.result == -1:
                                    return this_dm.result

                                if not os.path.isfile(result_filename):
                                    raise Exception("The filename '{}' should have been generated by 'RepositoryBootstrap.Impl.Hooks.HookScript' but it doesn't exist ({}).".format(result_filename, method))

                            with open(result_filename) as f:
                                result = int(f.read().strip())

                            if result == -1:
                                this_dm.result = result
                                return this_dm.result
                            elif result == 1:
                                pass                    # 1 is returned if a configuration was used
                            elif result == 0:
                                terminate = True        # 0 is returned if a configuration was not used
                            else:
                                assert False, result

    return 0
