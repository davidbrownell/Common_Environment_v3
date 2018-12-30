# ----------------------------------------------------------------------
# |
# |  __init__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-12-15 10:11:48
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Applies Black (https://github.com/ambv/black) followed by customizations by David BROWNell"""

import importlib
import itertools
import os
import sys

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import FileSystem
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class Executor(object):
    """\
    Object that is capable of formatting source based on Black and
    one or more plugins.
    """

    # ----------------------------------------------------------------------
    def __init__(self, output_stream, *plugin_input_dirs, **plugin_args):
        plugins = []

        for plugin_input_dir in itertools.chain(
            [os.path.join(_script_dir, "Plugins")],
            plugin_input_dirs,
        ):
            if not os.path.isdir(plugin_input_dir):
                raise Exception("'{}' is not a valid directory".format(plugin_input_dir))

            sys.path.insert(0, plugin_input_dir)
            with CallOnExit(lambda: sys.path.pop(0)):
                for filename in FileSystem.WalkFiles(
                    plugin_input_dir,
                    include_file_extensions=[".py"],
                    include_file_base_names=[lambda basename: basename.endswith("Plugin")],
                ):
                    plugin_name = os.path.splitext(os.path.basename(filename))[0]

                    mod = importlib.import_module(plugin_name)
                    if mod is None:
                        output_stream.write(
                            "WARNING: Unable to import the module at '{}'.\n".format(filename)
                        )
                        continue

                    potential_class = None
                    potential_class_names = [plugin_name, "Plugin"]

                    for potential_class_name in potential_class_names:
                        potential_class = getattr(mod, potential_class_name, None)
                        if potential_class is not None:
                            break

                    if potential_class is None:
                        output_stream.write(
                            "WARNING: The module at '{}' does not contain a supported class ({}).\n".format(
                                filename, ", ".join(
                                    ["'{}'".format(pcn) for pcn in potential_class_names]
                                )
                            )
                        )
                        continue

                    plugins.append(potential_class)

        plugins.sort(
            key=lambda plugin: (plugin.Priority, plugin.Name)
        )

        self._plugins                       = plugins
        self._plugin_args                   = plugin_args

    # ----------------------------------------------------------------------
    @property
    def Plugins(self):
        return iter(self._plugins)

    # ----------------------------------------------------------------------
    def Format(
        self,
        input_filename_or_content,
        black_line_length=180,
        include_plugin_names=None,
        exclude_plugin_names=None,
    ):
        """Formats the input file or content and returns the results"""

        assert black_line_length > 0, black_line_length

        if os.path.isfile(input_filename_or_content):
            input_filename_or_content = open(input_filename_or_content).read()

        input_content = input_filename_or_content
        del input_filename_or_content

        include_plugin_names = include_plugin_names or set()
        exclude_plugin_names = exclude_plugin_names or set()

        # ----------------------------------------------------------------------
        def Postprocess(lines):
            plugins = [plugin for plugin in self.Plugins if plugin.Name not in exclude_plugin_names and (not include_plugin_names or plugin.Name in include_plugin_names)]

            for plugin in plugins:
                args = []
                kwargs = {}

                defaults = self._plugin_args.get(plugin.Name, None)
                if defaults is not None:
                    if isinstance(defaults, (list, tuple)):
                        args = defaults
                    elif isinstance(defaults, dict):
                        kwargs = defaults
                    else:
                        assert False, defaults

                lines = plugin.Decorate(lines, *args, **kwargs)

            return lines

        # ----------------------------------------------------------------------

        # Importing here as black isn't supported by python2
        from black import format_str as Blackify

        return Blackify(
            input_content,
            line_length=black_line_length,
            postprocess_lines_func=Postprocess,
        )
