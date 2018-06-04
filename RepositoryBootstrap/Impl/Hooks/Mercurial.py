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

sys.path.insert(0, os.path.dirname(__file__))
import HookImpl
sys.path.pop(0)

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

    return HookImpl.Invoke( ui,
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

    return HookImpl.Invoke( ui,
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

    return HookImpl.Invoke( ui,
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

# BugBug # ----------------------------------------------------------------------
# BugBug def _Impl(ui, verb, json_content, is_debug):
# BugBug     # Imports here can be tricky
# BugBug     try:
# BugBug         sys.path.insert(0, _fundamental_root)
# BugBug 
# BugBug         from RepositoryBootstrap import Constants
# BugBug         from RepositoryBootstrap.Impl import CommonEnvironmentImports
# BugBug         
# BugBug         del sys.path[0]
# BugBug     except:
# BugBug         import traceback
# BugBug 
# BugBug         ui.write(traceback.format_exc())
# BugBug         raise
# BugBug 
# BugBug     shell = CommonEnvironmentImports.CurrentShell
# BugBug     
# BugBug     # Get the configuration to use during environment activation
# BugBug     output_stream = CommonEnvironmentImports.StreamDecorator(ui)
# BugBug     
# BugBug     output_stream.write('\n')
# BugBug     output_stream.write("Getting configurations...")
# BugBug     with output_stream.DoneManager() as dm:
# BugBug         activation_root = os.getcwd()
# BugBug 
# BugBug         # Is the repo a tool repo?
# BugBug         bootstrap_filename = os.path.join(activation_root, Constants.GENERATED_DIRECTORY_NAME, shell.CategoryName, Constants.GENERATED_BOOTSTRAP_JSON_FILENAME)
# BugBug         if os.path.isfile(bootstrap_filename):
# BugBug             with open(bootstrap_filename) as f:
# BugBug                 bootstrap_data = json.load(f)
# BugBug 
# BugBug             if bootstrap_data["is_tool_repo"]:
# BugBug                 # Set the root to the fundamental repo
# BugBug                 activation_root = _fundamental_root
# BugBug 
# BugBug         activation_script = os.path.join(activation_root, shell.CreateScriptName(Constants.ACTIVATE_ENVIRONMENT_NAME))
# BugBug         if not os.path.isfile(activation_script):
# BugBug             return 0
# BugBug 
# BugBug         result, output = CommonEnvironmentImports.Process.Execute("{} ListConfigurations json".format(activation_script))
# BugBug         assert result == 0, output
# BugBug         
# BugBug         data = json.loads(output)
# BugBug         
# BugBug         configurations = list(data.keys())
# BugBug         if not configurations:
# BugBug             configurations = [ "None", ]
# BugBug 
# BugBug     # Process the configurations
# BugBug     output_stream.write("Processing configurations...")
# BugBug     with output_stream.DoneManager( suffix='\n',
# BugBug                                   ) as dm:
# BugBug         display_sentinel = "Display?!__"
# BugBug         
# BugBug         json_filename = shell.CreateTempFilename(".json")
# BugBug 
# BugBug         with open(json_filename, 'w') as f:
# BugBug             json.dump(json_content, f)
# BugBug 
# BugBug         terminate = False
# BugBug 
# BugBug         with CommonEnvironmentImports.CallOnExit(lambda: os.remove(json_filename)):
# BugBug             original_environment = None
# BugBug 
# BugBug             if os.getenv(Constants.DE_REPO_GENERATED_NAME):
# BugBug                 # This code sucks because it is hard coding names and duplicating logic in Activate.py. However, importing
# BugBug                 # Activate here is causing problems as the Mercurial version of python is different enough from out
# BugBug                 # version that some imports don't work between python 2 and python 3.
# BugBug                 original_data_filename = os.path.join(os.getenv(Constants.DE_REPO_GENERATED_NAME), "EnvironmentActivation.OriginalEnvironment.json")
# BugBug                 assert os.path.isfile(original_data_filename), original_data_filename
# BugBug 
# BugBug                 with open(original_data_filename) as f:
# BugBug                     original_environment = json.load(f)
# BugBug 
# BugBug             for index, configuration in enumerate(configurations):
# BugBug                 dm.stream.write("Configuration '{}' ({} of {})...".format( configuration if configuration != "None" else "<default>",
# BugBug                                                                            index + 1,
# BugBug                                                                            len(configurations),
# BugBug                                                                          ))
# BugBug                 with dm.stream.DoneManager() as this_dm:
# BugBug                     if terminate:
# BugBug                         continue
# BugBug 
# BugBug                     result_filename = shell.CreateTempFilename()
# BugBug 
# BugBug                     # ----------------------------------------------------------------------
# BugBug                     def RemoveResultFilename():
# BugBug                         if os.path.isfile(result_filename):
# BugBug                             os.remove(result_filename)
# BugBug 
# BugBug                     # ----------------------------------------------------------------------
# BugBug 
# BugBug                     with CommonEnvironmentImports.CallOnExit(RemoveResultFilename):
# BugBug                         commands = [ shell.Commands.EchoOff(),
# BugBug                                      shell.Commands.Raw('cd "{}"'.format(os.path.dirname(activation_script))),
# BugBug                                      shell.Commands.Call("{} {} /fast".format(os.path.basename(activation_script), configuration if configuration != "None" else '')),
# BugBug                                      shell.Commands.ExitOnError(-1),
# BugBug                                      shell.Commands.Augment("PYTHONPATH", _fundamental_root, update_memory=False),
# BugBug                                      shell.Commands.Raw('python -m RepositoryBootstrap.Impl.Hooks.HookScript "{verb}" "{sentinel}" "{json_filename}" "{result_filename}"{first}' \
# BugBug                                                           .format( verb=verb,
# BugBug                                                                    sentinel=display_sentinel,
# BugBug                                                                    json_filename=json_filename,
# BugBug                                                                    result_filename=result_filename,
# BugBug                                                                    first=" /first" if index == 0 else '',
# BugBug                                                                  )),
# BugBug                                      shell.Commands.ExitOnError(-1),
# BugBug                                    ]
# BugBug 
# BugBug                         script_filename = shell.CreateTempFilename(shell.ScriptExtension)
# BugBug                         with open(script_filename, 'w') as f:
# BugBug                             f.write(shell.GenerateCommands(commands))
# BugBug 
# BugBug                         with CommonEnvironmentImports.CallOnExit(lambda: os.remove(script_filename)):
# BugBug                             shell.MakeFileExecutable(script_filename)
# BugBug 
# BugBug                             content = []
# BugBug                             
# BugBug                             # ----------------------------------------------------------------------
# BugBug                             def Display(value):
# BugBug                                 if value.startswith(display_sentinel):
# BugBug                                     stipped_value = value.replace(display_sentinel, '')
# BugBug 
# BugBug                                     this_dm.stream.write(stipped_value)
# BugBug                                     this_dm.stream.flush()
# BugBug 
# BugBug                                 content.append(value)
# BugBug 
# BugBug                             # ----------------------------------------------------------------------
# BugBug 
# BugBug                             this_dm.result = CommonEnvironmentImports.Process.Execute( script_filename,
# BugBug                                                                                        Display,
# BugBug                                                                                        line_delimited_output=True,
# BugBug                                                                                        environment=original_environment,
# BugBug                                                                                      )
# BugBug 
# BugBug                             if is_debug:
# BugBug                                 this_dm.stream.write(''.join(content))
# BugBug 
# BugBug                             if this_dm.result == -1:
# BugBug                                 return this_dm.result
# BugBug 
# BugBug                             if not os.path.isfile(result_filename):
# BugBug                                 raise Exception("The filename '{}' should have been generated by 'RepositoryBootstrap.Impl.Hooks.HookImpl' but it doesn't exist.".format(result_filename))
# BugBug                             
# BugBug                             with open(result_filename) as f:
# BugBug                                 result = int(f.read().strip())
# BugBug 
# BugBug                             if result == -1:
# BugBug                                 this_dm.result = result
# BugBug                                 return this_dm.result
# BugBug                             elif result == 1:
# BugBug                                 pass                    # 1 is returned if a configuration was used
# BugBug                             elif result == 0:
# BugBug                                 terminate = True        # 0 is returned if a configuration was not used 
# BugBug                             else:
# BugBug                                 assert False, result
# BugBug 
# BugBug     return 0
