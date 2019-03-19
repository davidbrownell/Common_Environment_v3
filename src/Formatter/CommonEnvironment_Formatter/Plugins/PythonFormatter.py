# ----------------------------------------------------------------------
# |
# |  PythonFormatter.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-03-11 09:45:46
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the Formatter object"""

import os

from collections import defaultdict

import six
import toml

import CommonEnvironment
from CommonEnvironment import FileSystem
from CommonEnvironment.FormatterImpl import FormatterImpl
from CommonEnvironment import Interface
from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Formatter(FormatterImpl):

    TOML_FILENAME                           = "pyproject.toml"
    TOML_SECTION_NAME                       = "tool.pythonformatter"

    DEFAULT_BLACK_LINE_LENGTH               = 180

    # ----------------------------------------------------------------------
    # |  Properties
    Name                                    = Interface.DerivedProperty("Python")
    Description                             = Interface.DerivedProperty(
        "Formats Python code using Black (https://github.com/ambv/black) plus enhancements",
    )
    InputTypeInfo                           = Interface.DerivedProperty(
        FilenameTypeInfo(
            validation_expression=r".+\.py",
        ),
    )

    # ----------------------------------------------------------------------
    # |  Methods
    _is_initialized                         = False

    @classmethod
    def __clsinit__(cls, *plugin_input_dirs):
        if cls._is_initialized:
            return

        plugins = cls._GetPlugins(
            os.path.join(_script_dir, "PythonFormatterImpl"),
            *plugin_input_dirs
        )

        debug_plugin = None
        for potential_plugin in plugins:
            if potential_plugin.Name == "Debug":
                debug_plugin = potential_plugin
                break

        cls._plugins = plugins
        cls._debug_plugin = debug_plugin

        cls._is_initialized = True

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.override
    def Format(
        cls,
        filename_or_content,
        black_line_length=None,
        include_plugin_names=None,
        exclude_plugin_names=None,
        debug=False,
        hint_filename=None,
        *plugin_input_dirs,
        **plugin_args
    ):
        cls.__clsinit__(*plugin_input_dirs)

        if FileSystem.IsFilename(filename_or_content):
            # Search all ancestor directories for toml files
            toml_filenames = []

            directory = os.path.dirname(filename_or_content)
            while True:
                potential_filename = os.path.join(directory, cls.TOML_FILENAME)
                if os.path.isfile(potential_filename):
                    toml_filenames.append(potential_filename)

                parent_directory = os.path.dirname(directory)
                if parent_directory == directory:
                    break

                directory = parent_directory

            if toml_filenames:
                these_plugin_args = defaultdict(dict)

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

                        python_formatter_data = GetTomlSection(data, cls.TOML_SECTION_NAME)

                        for plugin_name, plugin_values in six.iteritems(python_formatter_data):
                            for k, v in six.iteritems(plugin_values):
                                these_plugin_args[plugin_name][k] = v

                    except Exception as ex:
                        raise Exception(
                            "The toml file at '{}' is not valid ({})".format(toml_filename, str(ex)),
                        )

                # Apply the provided args. Use these_plugin_args to take advantage of
                # the defaultdict.
                for plugin_name, plugin_values in six.iteritems(plugin_args):
                    for k, v in six.iteritems(plugin_values):
                        these_plugin_args[plugin_name][k] = v

                plugin_args = these_plugin_args

            # Read the content
            with open(filename_or_content) as f:
                filename_or_content = f.read()

        input_content = filename_or_content
        del filename_or_content

        include_plugin_names = set(include_plugin_names or [])
        exclude_plugin_names = set(exclude_plugin_names or [])

        if debug:
            if include_plugin_names:
                include_plugin_names.add(cls._debug_plugin.Name)
        else:
            exclude_plugin_names.add(cls._debug_plugin.Name)

        if black_line_length is None:
            black_line_length = cls.DEFAULT_BLACK_LINE_LENGTH

        plugins = [plugin for plugin in cls._plugins if plugin.Name not in exclude_plugin_names and (not include_plugin_names or plugin.Name in include_plugin_names)]

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

            for plugin in plugins:
                lines = plugin.PostprocessLines(lines)

            return lines

        # ----------------------------------------------------------------------

        # Importing here as black isn't supported by python2
        from black import format_str as Blackify        # <unable to import> pylint: disable = E0401

        formatted_content = Blackify(
            input_content,
            line_length=black_line_length,
            preprocess_lines_func=Preprocess,
            postprocess_lines_func=Postprocess,
        )

        return formatted_content, formatted_content != input_content
