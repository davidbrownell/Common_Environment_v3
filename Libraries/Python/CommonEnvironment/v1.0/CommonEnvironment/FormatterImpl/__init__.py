# ----------------------------------------------------------------------
# |
# |  __init__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-03-11 09:40:51
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains for FormatterImpl object"""

import importlib
import itertools
import os
import sys

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import FileSystem
from CommonEnvironment import Interface

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class FormatterImpl(Interface.Interface):
    """\
    Abstract base class for formatters (automated functionality able to format 
    source code according to an established coding standard).
    """

    # ----------------------------------------------------------------------
    # |  Properties
    @Interface.abstractproperty
    def Name(self):
        """Name of the formatter"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def Description(self):
        """Description of the formatter"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    @Interface.abstractproperty
    def InputTypeInfo(self):
        """Type information for required input types"""
        raise Exception("Abstract property")

    # ----------------------------------------------------------------------
    # |  Methods
    @staticmethod
    @Interface.abstractmethod
    def Format(filename_or_content, *plugin_input_dirs, **plugin_args):
        """Formats the given input"""
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @classmethod
    @Interface.extensionmethod
    def HasChanges(cls, filename_or_content, *plugin_input_dirs, **plugin_args):
        """Return True if the content would be changed by formatting if applied"""

        return cls.Format(filename_or_content, *plugin_input_dirs, **plugin_args)[1]

    # ----------------------------------------------------------------------
    # |  Protected Methods
    @staticmethod
    def _GetPlugins(local_plugin_dir, *plugin_input_dirs):
        plugins = []

        for plugin_input_dir in itertools.chain([local_plugin_dir], plugin_input_dirs):
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
                        raise Exception("Unable to import the module at '{}'".format(filename))

                    potential_class = None
                    potential_class_names = [plugin_name, "Plugin"]

                    for potential_class_name in potential_class_names:
                        potential_class = getattr(mod, potential_class_name, None)
                        if potential_class is not None:
                            break

                    if potential_class is None:
                        raise Exception(
                            "The module at '{}' does not contain a supported class ({})".format(
                                filename,
                                ", ".join(["'{}'".format(pcn) for pcn in potential_class_names]),
                            ),
                        )

                    plugins.append(potential_class)

        plugins.sort(
            key=lambda plugin: (plugin.Priority, plugin.Name),
        )

        return plugins
