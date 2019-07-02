# ----------------------------------------------------------------------
# |
# |  PythonFormatter.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-06-22 11:38:13
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

import black                                            # <unable to import> pylint: disable = E0401
from blib2to3.pygram import token as python_tokens
import six
import toml

import CommonEnvironment
from CommonEnvironment import FileSystem
from CommonEnvironment.FormatterImpl import FormatterImpl                   # <unable to import> pylint: disable = E0401
from CommonEnvironment import Interface
from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo

from PythonFormatterImpl.Tokenizer import BlackTokenizer

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
@Interface.staticderived
class Formatter(FormatterImpl):
    """
    Python code formatter that relies on black for the heavy lifting.

    Modifications to the code are implemented in terms of plugins, where
    the plugins are executed in the following order:

        1) Plugin.PreprocessTokens
        2) Plugin.PreprocessBlocks
        3) **black**
        4) Plugin.DecorateTokens
        5) Plugin.DecorateBlocks
        6) Plugin.PostprocessTokens
        7) Plugin.PostprocessBlocks

    """

    TOML_FILENAME                           = "pyproject.toml"
    TOML_SECTION_NAME                       = "tool.pythonformatter"

    DEFAULT_BLACK_LINE_LENGTH               = 90

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
    @classmethod
    @Interface.override
    def Format(
        cls,
        filename_or_content,
        black_line_length=None,
        include_plugin_names=None,
        exclude_plugin_names=None,
        debug=False,
        *plugin_input_dirs,
        **plugin_args
    ):
        # Get the file's contents
        if FileSystem.IsFilename(filename_or_content):
            this_black_line_length, plugin_args = cls._AugmentPluginArgs(
                filename_or_content,
                plugin_args,
            )
            if black_line_length is None:
                black_line_length = this_black_line_length

            with open(filename_or_content) as f:
                filename_or_content = f.read()

        if black_line_length is None:
            black_line_length = cls.DEFAULT_BLACK_LINE_LENGTH

        content = filename_or_content
        del filename_or_content

        # Load the plugins
        plugins = cls._CreatePlugins(
            include_plugin_names or set(),
            exclude_plugin_names or set(),
            debug,
            plugin_input_dirs,
            plugin_args,
        )

        # Process the content

        # ----------------------------------------------------------------------
        def ProcessTokensImpl(tokenizer, plugin_method_name, recurse_count):

            # ----------------------------------------------------------------------
            def ProcessTokens(tokenizer):
                return ProcessTokensImpl(tokenizer, plugin_method_name, recurse_count + 1)

            # ----------------------------------------------------------------------

            for plugin in plugins:
                getattr(plugin, plugin_method_name)(
                    tokenizer,
                    ProcessTokens,
                    recurse_count,
                )
                if tokenizer.HasModifications():
                    tokenizer = tokenizer.Commit()

            return tokenizer

        # ----------------------------------------------------------------------
        def ProcessImpl(black_lines, plugin_method_prefix):
            # Process the tokens
            method_name = "{}Tokens".format(plugin_method_prefix)

            tokenizer = ProcessTokensImpl(BlackTokenizer(black_lines), method_name, 0)
            black_lines = tokenizer.ToBlackLines()

            # Process the blocks
            method_name = "{}Blocks".format(plugin_method_prefix)

            blocks = []
            create_new_block = True

            for line in black_lines:
                if not line.leaves:
                    create_new_block = True
                    continue

                if line.leaves[0].prefix.startswith("\n"):
                    create_new_block = True

                if create_new_block:
                    blocks.append([])
                    create_new_block = False

                blocks[-1].append(line)

                if line.leaves[-1].type == python_tokens.COLON:
                    create_new_block = True

            for plugin in plugins:
                getattr(plugin, method_name)(blocks)

            # Process the lines
            method_name = "{}Lines".format(plugin_method_prefix)

            for plugin in plugins:
                black_lines = getattr(plugin, method_name)(black_lines)

            return black_lines

        # ----------------------------------------------------------------------
        def Preprocess(lines):
            return ProcessImpl(lines, "Preprocess")

        # ----------------------------------------------------------------------
        def Postprocess(lines):
            lines = ProcessImpl(lines, "Decorate")
            lines = ProcessImpl(lines, "Postprocess")

            return lines

        # ----------------------------------------------------------------------

        formatted_content = black.format_str(
            content,
            line_length=black_line_length,
            preprocess_lines_func=Preprocess,
            postprocess_lines_func=Postprocess,
        )

        return formatted_content, formatted_content != content

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @classmethod
    def _AugmentPluginArgs(cls, filename, plugin_args):
        black_line_length = None

        # Search all ancestor directories for toml files
        toml_filenames = []

        directory = os.path.dirname(filename)
        while True:
            potential_filename = os.path.join(directory, cls.TOML_FILENAME)
            if os.path.isfile(potential_filename):
                toml_filenames.append(potential_filename)

            parent_directory = os.path.dirname(directory)
            if parent_directory == directory:
                break

            directory = parent_directory

        if toml_filenames:
            toml_filenames.reverse()

            # ----------------------------------------------------------------------
            def GetTomlSection(data, section_name):
                for part in section_name.split("."):
                    data = data.get(part, None)
                    if data is None:
                        return {}

                return data

            # ----------------------------------------------------------------------

            these_plugin_args = defaultdict(dict)

            for toml_filename in toml_filenames:
                try:
                    with open(toml_filename) as f:
                        data = toml.load(f)

                    black_data = GetTomlSection(data, "tool.black")
                    if "line-length" in black_data:
                        black_line_length = black_data["line-length"]

                    python_formatter_data = GetTomlSection(data, cls.TOML_SECTION_NAME)
                    for plugin_name, plugin_values in six.iteritems(
                        python_formatter_data,
                    ):
                        for k, v in six.iteritems(plugin_values):
                            these_plugin_args[plugin_name][k] = v

                except Exception as ex:
                    raise Exception(
                        "The toml file at '{}' is not valid ({})".format(
                            toml_filename,
                            str(ex),
                        ),
                    )

            # Apply the provided args. Use `these_plugin_args` as the result to
            # take advantage of the defaultdict.
            for plugin_name, plugin_values in six.iteritems(plugin_args):
                for k, v in six.iteritems(plugin_values):
                    these_plugin_args[plugin_name][k] = v

            plugin_args = these_plugin_args

        return black_line_length, plugin_args

    # ----------------------------------------------------------------------
    @classmethod
    def _CreatePlugins(
        cls,
        include_plugin_names,
        exclude_plugin_names,
        debug,
        plugin_input_dirs,
        plugin_args,
    ):
        if not debug:
            exclude_plugin_names.add("Debug")

        # Get the plugins
        plugins = []

        for plugin in cls._GetPlugins(
            os.path.join(_script_dir, "PythonFormatterImpl"),
            sort=False,
            *plugin_input_dirs
        ):
            args = []
            kwargs = {}

            defaults = plugin_args.get(plugin.Name, None)
            if defaults is not None:
                if (
                    isinstance(defaults, tuple)
                    and len(defaults) == 2
                    and isinstance(defaults[0], (list, tuple))
                    and isinstance(defaults[1], dict)
                ):
                    args, kwargs = defaults
                elif isinstance(defaults, (list, tuple)):
                    args = defaults
                elif isinstance(defaults, dict):
                    kwargs = defaults
                else:
                    assert False, defaults

            plugin = plugin(*args, **kwargs)

            if plugin.Name in exclude_plugin_names:
                continue

            if include_plugin_names and plugin.Name not in include_plugin_names:
                continue

            plugins.append(plugin)

        # Ensure that the plugins are executed in priority order
        plugins.sort(
            key=lambda plugin: (plugin.Priority, plugin.Name),
        )

        return plugins
