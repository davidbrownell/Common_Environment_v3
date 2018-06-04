# ----------------------------------------------------------------------
# |  
# |  Mercurial.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-04 13:37:56
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Hook functionality for Mercurial"""

import datetime
import json
import os
import sys
import textwrap
import time

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

try:
    import mercurial 

    mercurial.demandimport.disable()
except:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from RepositoryBootstrap import GetFundamentalRepository as _GetFundamentalRepository
sys.path.pop(0)

_fundamental_root                           = _GetFundamentalRepository()

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def PreTxnCommit(ui, repo, node, parent1, parent2, *args, **kwargs):
    """Called prior to a commit being finalized"""

    is_debug = _IsDebug(ui)

    if is_debug:
        ui.write(textwrap.dedent(
            """\
            # ----------------------------------------------------------------------
            PreTxnCommit

            Repo root:                      {}
            node:                           {}
            parent 1:                       {}
            parent 2:                       {}
            args:                           {}
            kwargs:                         {}

            # ----------------------------------------------------------------------
            """).format( repo.root, 
                         node,
                         parent1,
                         parent2,
                         args,
                         kwargs,
                       ))

    return _Impl( ui,
                  "Commit",
                  _GetChangeInfo(repo, repo[node]),
                  is_debug,
                )

# ----------------------------------------------------------------------
def PreOutgoing(ui, repo, source, *args, **kwargs):
    """Called prior to the beginning of a push"""

    # Only process pushes
    if source != "push":
        return 0

    is_debug = _IsDebug(ui)

    if is_debug:
        ui.write(textwrap.dedent(
            """\
            # ----------------------------------------------------------------------
            PreOutgoing

            Repo root:                      {}
            args:                           {}
            kwargs:                         {}

            # ----------------------------------------------------------------------
            """).format( repo.root,
                         args,
                         kwargs,
                       ))

    data = {}

    if "url" in kwargs:
        data["url"] = kwargs["url"]

    return _Impl( ui,
                  "Push",
                  data,
                  is_debug,
                )

# ----------------------------------------------------------------------
def PreTxnChangeGroup(ui, repo, source, node, node_last=None, *args, **kwargs):
    """Called after a pull has been downloaded but before it has been applied locally"""

    if source != "serve":
        return 0

    is_debug = _IsDebug(ui)

    if is_debug:
        ui.write(textwrap.dedent(
            """\
            # ----------------------------------------------------------------------
            PreTxnChangeGroup

            Repo root:                      {}
            node:                           {}
            node_last:                      {}
            args:                           {}
            kwargs:                         {}

            # ----------------------------------------------------------------------
            """).format( repo.root,
                         node,
                         node_last,
                         args,
                         kwargs,
                       ))

    changes = []
    queue = [ node, ]
    visited = set()

    while queue:
        node = queue.pop()
        ctx = repo[node]

        changes.append(_GetChangeInfo(repo, ctx))
        visited.add(node)

        for child in ctx.children():
            if child not in visited:
                queue.append(child)

    changes.sort(key=lambda c: c["date"])

    return _Impl( ui,
                  "Pull",
                  { "changes" : changes,
                  },
                  is_debug,
                )

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _IsDebug(ui):
    return ui.config("ui", "debug", default='').strip().lower() == "true"

# ----------------------------------------------------------------------
def _GetChangeInfo(repo, ctx):
    # ----------------------------------------------------------------------
    def TransformFilename(filename):
        return os.path.join(repo.root, filename).replace('/', os.path.sep)

    # ----------------------------------------------------------------------

    parents = ctx.parents()
    if not parents:
        parents = [ None, ]

    status = repo.status(parents[0], ctx)

    t, tz = ctx.date()
    t = time.gmtime(t - tz)
    t = datetime.datetime(*t[:6])

    return { "id" : ctx.hex(),
             "author" : ctx.user(),
             "date" : t.isoformat(),
             "description" : ctx.description(),
             "branch" : ctx.branch(),
             "added" : [ TransformFilename(filename) for filename in status.added ],
             "modified" : [ TransformFilename(filename) for filename in status.modified ],
             "removed" : [ TransformFilename(filename) for filename in status.removed ],
           }

# ----------------------------------------------------------------------
def _Impl(ui, verb, json_content, is_debug):
    # Imports here can be tricky
    try:
        sys.path.insert(0, _fundamental_root)

        from RepositoryBootstrap import Constants
        from RepositoryBootstrap.Impl import CommonEnvironmentImports
        
        del sys.path[0]
    except:
        import traceback

        ui.write(traceback.format_exc())
        raise

    shell = CommonEnvironmentImports.CurrentShell
    
    # Get the configuration to use during environment activation
    output_stream = CommonEnvironmentImports.StreamDecorator(ui)
    
    output_stream.write('\n')
    output_stream.write("Getting configurations...")
    with output_stream.DoneManager() as dm:
        activation_root = os.getcwd()

        # Is the repo a tool repo?
        bootstrap_filename = os.path.join(activation_root, Constants.GENERATED_DIRECTORY_NAME, shell.CategoryName, Constants.GENERATED_BOOTSTRAP_JSON_FILENAME)
        if os.path.isfile(bootstrap_filename):
            with open(bootstrap_filename) as f:
                bootstrap_data = json.load(f)

            if bootstrap_data["is_tool_repo"]:
                # Set the root to the fundamental repo
                activation_root = _fundamental_root

        activation_script = os.path.join(activation_root, shell.CreateScriptName(Constants.ACTIVATE_ENVIRONMENT_NAME))
        if not os.path.isfile(activation_script):
            return 0

        result, output = CommonEnvironmentImports.Process.Execute("{} ListConfigurations json".format(activation_script))
        assert result == 0, output
        
        data = json.loads(output)
        
        configurations = list(data.keys())
        if not configurations:
            configurations = [ "None", ]

    # Process the configurations
    output_stream.write("Processing configurations...")
    with output_stream.DoneManager( suffix='\n',
                                  ) as dm:
        display_sentinel = "Display?!__"
        
        json_filename = shell.CreateTempFilename(".json")

        with open(json_filename, 'w') as f:
            json.dump(json_content, f)

        terminate = False

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

            for index, configuration in enumerate(configurations):
                dm.stream.write("Configuration '{}' ({} of {})...".format( configuration if configuration != "None" else "<default>",
                                                                           index + 1,
                                                                           len(configurations),
                                                                         ))
                with dm.stream.DoneManager() as this_dm:
                    if terminate:
                        continue

                    result_filename = shell.CreateTempFilename()

                    # ----------------------------------------------------------------------
                    def RemoveResultFilename():
                        if os.path.isfile(result_filename):
                            os.remove(result_filename)

                    # ----------------------------------------------------------------------

                    with CommonEnvironmentImports.CallOnExit(RemoveResultFilename):
                        commands = [ shell.Commands.EchoOff(),
                                     shell.Commands.Raw('cd "{}"'.format(os.path.dirname(activation_script))),
                                     shell.Commands.Call("{} {} /fast".format(os.path.basename(activation_script), configuration if configuration != "None" else '')),
                                     shell.Commands.ExitOnError(-1),
                                     shell.Commands.Augment("PYTHONPATH", _fundamental_root, update_memory=False),
                                     shell.Commands.Raw('python -m RepositoryBootstrap.Impl.Hooks.HookScript "{verb}" "{sentinel}" "{json_filename}" "{result_filename}"{first}' \
                                                          .format( verb=verb,
                                                                   sentinel=display_sentinel,
                                                                   json_filename=json_filename,
                                                                   result_filename=result_filename,
                                                                   first=" /first" if index == 0 else '',
                                                                 )),
                                     shell.Commands.ExitOnError(-1),
                                   ]

                        script_filename = shell.CreateTempFilename(shell.ScriptExtension)
                        with open(script_filename, 'w') as f:
                            f.write(shell.GenerateCommands(commands))

                        with CommonEnvironmentImports.CallOnExit(lambda: os.remove(script_filename)):
                            shell.MakeFileExecutable(script_filename)

                            content = []
                            
                            # ----------------------------------------------------------------------
                            def Display(value):
                                if value.startswith(display_sentinel):
                                    stipped_value = value.replace(display_sentinel, '')

                                    this_dm.stream.write(stipped_value)
                                    this_dm.stream.flush()

                                content.append(value)

                            # ----------------------------------------------------------------------

                            this_dm.result = CommonEnvironmentImports.Process.Execute( script_filename,
                                                                                       Display,
                                                                                       line_delimited_output=True,
                                                                                       environment=original_environment,
                                                                                     )

                            if is_debug:
                                this_dm.stream.write(''.join(content))

                            if this_dm.result == -1:
                                return this_dm.result

                            if not os.path.isfile(result_filename):
                                raise Exception("The filename '{}' should have been generated by 'RepositoryBootstrap.Impl.Hooks.HookImpl' but it doesn't exist.".format(result_filename))
                            
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
