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

from collections import defaultdict

import six
import toml

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import FileSystem
from CommonEnvironment.TypeInfo.FundamentalTypes.All import *

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# <Wrong Hanging Indentation> pylint: disable = C0330

# ----------------------------------------------------------------------
class Executor(object):
    """\
    Object that is capable of formatting source based on Black and
    one or more plugins.
    """

    TOML_FILENAME                           = "pyproject.toml"
    TOML_BLACK_AND_BROWN_SECTION_NAME       = "tool.blackandbrown"

    DEFAULT_BLACK_LINE_LENGTH               = 180

    # ----------------------------------------------------------------------
    def __init__(self, output_stream, *plugin_input_dirs, **plugin_args):
        plugins = []
        debug_plugin = None

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
                                filename,
                                ", ".join(["'{}'".format(pcn) for pcn in potential_class_names]),
                            )
                        )
                        continue

                    plugins.append(potential_class)

                    if debug_plugin is None and potential_class.Name == "Debug":
                        debug_plugin = potential_class

        plugins.sort(
            key=lambda plugin: (plugin.Priority, plugin.Name)
        )

        self._plugins                       = plugins
        self._plugin_args                   = plugin_args
        self._debug_plugin                  = debug_plugin

    # ----------------------------------------------------------------------
    @property
    def Plugins(self):
        return iter(self._plugins)

    # ----------------------------------------------------------------------
    def Format(
        self,
        input_filename_or_content,
        black_line_length=None,
        include_plugin_names=None,
        exclude_plugin_names=None,
        debug=False,
    ):
        """Formats the input file or content and returns the results"""
        
        plugin_args = self._plugin_args

        if os.path.isfile(input_filename_or_content):
            # Search all ancestor directories for toml files
            toml_filenames = []

            directory = os.path.dirname(input_filename_or_content)
            while True:
                potential_filename = os.path.join(directory, self.TOML_FILENAME)
                if os.path.isfile(potential_filename):
                    toml_filenames.append(potential_filename)

                parent_directory = os.path.dirname(directory)
                if parent_directory == directory:
                    break

                directory = parent_directory

            if toml_filenames:
                plugin_args = defaultdict(dict)

                toml_filenames.reverse()

                # ----------------------------------------------------------------------
                def GetTomlSection(data, section_name):
                    for part in section_name.split("."):
                        data = data.get(part, None)
                        if data is None:
                            return {}

                    return data

                # ----------------------------------------------------------------------

                for toml_filename in toml_filenames:
                    try:
                        with open(toml_filename) as f:
                            data = toml.load(f)

                        black_data = GetTomlSection(data, "tool.black")
                        if "line-length" in black_data:
                            black_line_length = black_data["line-length"]

                        black_and_brown_data = GetTomlSection(
                            data,
                            self.TOML_BLACK_AND_BROWN_SECTION_NAME,
                        )
                        for plugin_name, plugin_values in six.iteritems(black_and_brown_data):
                            for k, v in six.iteritems(plugin_values):
                                plugin_args[plugin_name][k] = v

                    except Exception as ex:
                        raise Exception(
                            "The toml file at '{}' is not valid ({})".format(toml_filename, str(ex))
                        )

                # Apply the provided args
                for plugin_name, plugin_values in six.iteritems(self._plugin_args):
                    for k, v in six.iteritems(plugin_values):
                        plugin_args[plugin_name][k] = v

            # Read the content
            input_filename_or_content = open(input_filename_or_content).read()

        input_content = input_filename_or_content
        del input_filename_or_content

        include_plugin_names = set(include_plugin_names or [])
        exclude_plugin_names = set(exclude_plugin_names or [])

        if debug:
            if include_plugin_names:
                include_plugin_names.add(self._debug_plugin.Name)
        else:
            exclude_plugin_names.add(self._debug_plugin.Name)

        if black_line_length is None:
            black_line_length = self.DEFAULT_BLACK_LINE_LENGTH

        plugins = [plugin for plugin in self.Plugins if plugin.Name not in exclude_plugin_names and (not include_plugin_names or plugin.Name in include_plugin_names)]

        # ----------------------------------------------------------------------
        def Preprocess(lines):
            for plugin in plugins:
                lines = plugin.PreprocessLines(lines)

            return lines

        # ----------------------------------------------------------------------
        def Postprocess(lines):
            for plugin in plugins:
                args = []
                kwargs = {}

                defaults = plugin_args.get(plugin.Name, None)
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

        formatted_content = Blackify(
            input_content,
            line_length=black_line_length,
            preprocess_lines_func=Preprocess,
            postprocess_lines_func=Postprocess,
        )

        return formatted_content, formatted_content != input_content

    # ----------------------------------------------------------------------
    def HasChanges(
        self,
        input_filename_or_content,
        black_line_length=None,
        include_plugin_names=None,
        exclude_plugin_names=None,
    ):
        """Returns True if the provided content will change with formatting and False if it will not"""

        return self.Format(
            input_filename_or_content,
            black_line_length=black_line_length,
            include_plugin_names=include_plugin_names,
            exclude_plugin_names=exclude_plugin_names,
        )[1]
