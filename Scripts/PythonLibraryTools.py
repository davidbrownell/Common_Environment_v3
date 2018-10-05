# ----------------------------------------------------------------------
# |  
# |  PythonLibraryTools.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-13 08:40:40
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Tools that help when installing, moving, and detecting changes with Python libraries."""

import json
import os
import shutil
import sys
import textwrap

from collections import OrderedDict

import inflect as inflect_mod
import six

import CommonEnvironment
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import StringHelpers
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.SourceControlManagement.All import GetSCM

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

inflect                                     = inflect_mod.engine()

sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from RepositoryBootstrap import Constants as RepositoryBootstrapConstants
    from RepositoryBootstrap.Impl.ActivationActivity.PythonActivationActivity import EASY_INSTALL_PTH_FILENAME, \
                                                                                     SCRIPTS_DIR_NAME, \
                                                                                     WRAPPERS_FILENAME, \
                                                                                     PythonActivationActivity \
                                                                                     
# <Missing function docstring> pylint: disable = C0111
# <Too few public methods> pylint: disable = R0903
# <Too many braches> pylint: disable = R0912
# <Too many local variables> pylint: disable = R0914
# <Too many nested blocks> pylint: disable = R1702

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( output_stream=None,
                        )
def Display( output_stream=sys.stdout,
           ):
    """
    Displays library modifications with the current python installation. 
    
    Use Move to prepare the libraries for checkin based on the currently activated repository."""
    new_content = _NewLibraryContent.Create(_EnvironmentSettings())
    
    # ----------------------------------------------------------------------
    def Write(name, items, is_os_specific_func):
        cols = [ 40, 9, 120, ]
        template = "{name:<%d}  {type:<%d}  {fullpath:<%d}" % tuple(cols)

        output_stream.write(textwrap.dedent(
            """\
            {sep}
            {name}
            {sep}

              {header}
              {underline}
              {content}

            """).format( sep='=' * len(name),
                         name=name,
                         header=template.format( name="Name",
                                                 type="Type",
                                                 fullpath="Path",
                                               ),
                         underline=template.format(**{ k : v for k, v in zip( [ "name", "type", "fullpath", ],
                                                                              [ '-' * col for col in cols ],
                                                                            ) }),
                         content="No items" if not items else StringHelpers.LeftJustify( '\n'.join([ template.format( name="{}{}".format( os.path.basename(item),
                                                                                                                                          ' *' if is_os_specific_func(item) else '',
                                                                                                                                        ),
                                                                                                                      type="Directory" if os.path.isdir(item) else "File",
                                                                                                                      fullpath=item,
                                                                                                                    )
                                                                                                     for item in items
                                                                                                   ]),
                                                                                         2,
                                                                                       ),
                       ))

    # ----------------------------------------------------------------------
    def WriteExtensions(name, items):
        cols = [ 120, ]
        template = "{fullpath:<%d}" % tuple(cols)

        output_stream.write(textwrap.dedent(
            """\
            {sep}
            {name}
            {sep}

              {header}
              {underline}
              {content}

            """).format( sep='=' * len(name),
                         name=name,
                         header=template.format(fullpath="Path"),
                         underline=template.format(**{ k : v for k, v in zip( [ "fullpath", ],
                                                                              [ '-' * col for col in cols ],
                                                                            ) }),
                         content="No items" if not items else StringHelpers.LeftJustify( '\n'.join(items),
                                                                                         2,
                                                                                       ),
                       ))

    # ----------------------------------------------------------------------

    Write("Libraries", new_content.Libraries, new_content.HasOSSpecificLibraryExtensions)
    Write("Scripts", new_content.Scripts, lambda fullpath: os.path.splitext(_script_fullpath)[1] in [ ".pyd", ".so", CurrentShell.ScriptExtension, CurrentShell.ExecutableExtension, ])
    WriteExtensions("Library Extensions", new_content.LibraryExtensions)
    WriteExtensions("Script Extensions", new_content.ScriptExtensions)

# ----------------------------------------------------------------------
@CommandLine.EntryPoint( no_move=CommandLine.EntryPoint.Parameter("Displays actions that would be taken without making any changes"),
                         ignore_warnings=CommandLine.EntryPoint.Parameter("Continues if warnings were encountered"),
                       )
@CommandLine.Constraints( output_stream=None,
                        )
def Move( no_move=False,
          ignore_warnings=False,
          output_stream=sys.stdout,
        ):
    """Moves any new python libraries to the appropriate Libraries folder associated with the activated repository."""

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        if no_move:
            dm.stream.write("***** Output is for information only; nothing will be moved. *****\n\n")
            move_func = lambda *args, **kwargs: None
        else:
            # ----------------------------------------------------------------------
            def Impl(source_dir_or_filename, dest_dir):
                # shutil.move won't overwrite files, so use distutils (which will)
                if os.path.isdir(source_dir_or_filename):
                    import distutils.dir_util

                    distutils.dir_util.copy_tree(source_dir_or_filename, os.path.join(dest_dir, os.path.basename(source_dir_or_filename)))
                    FileSystem.RemoveTree(source_dir_or_filename)
                else:
                    FileSystem.MakeDirs(dest_dir)
                    shutil.move(source_dir_or_filename, dest_dir)
                
            # ----------------------------------------------------------------------

            move_func = Impl

        dm.stream.write("Calculating new library content...")
        with dm.stream.DoneManager():
            new_content = _NewLibraryContent.Create(_EnvironmentSettings())

        # Group libraries and distinfo bundles

        # ----------------------------------------------------------------------
        class PythonLibrary(object):
            def __init__(self, fullpath):
                self.Fullpath                           = fullpath
                self.metadata_path                      = None
                self.version                            = None
                self.scripts                            = []
                
        # ----------------------------------------------------------------------

        libraries = OrderedDict()

        dm.stream.write("Grouping libraries...")
        with dm.stream.DoneManager( done_suffix=lambda: "{} found".format(inflect.no("library", len(libraries))),
                                    suffix='\n',
                                  ) as this_dm:
            for library_path in new_content.Libraries:
                basename = os.path.basename(library_path)
                if ( not basename.endswith(".dist-info") and 
                     not basename.endswith(".egg-info")
                   ):
                    libraries[basename] = PythonLibrary(library_path)

            lowercase_map = { k.lower() : k for k in six.iterkeys(libraries) }

            # Extract library metadata
            for library_path in new_content.Libraries:
                if os.path.isfile(library_path):
                    continue

                basename = os.path.basename(library_path)

                if not ( basename.endswith(".dist-info") or
                         basename.endswith(".egg-info")
                       ):
                    continue

                index = basename.find('-')
                if index == -1:
                    this_dm.result = this_dm.result or 1
                    this_dm.stream.write("WARNING: The library name for '{}' could not be extracted.\n".format(library_path))

                    continue

                potential_name = basename[:index]

                potential_names = [ potential_name,
                                    "{}.py".format(potential_name),
                                  ]

                # Try to find the python library based on the potential names
                python_library = None

                for potential_name in potential_names:
                    python_library = libraries.get(potential_name, None)
                    if python_library is None:
                        library_key = lowercase_map.get(potential_name.lower(), None)
                        if library_key is not None:
                            python_library = libraries.get(library_key, None)

                    if python_library is not None:
                        break

                if python_library is None:
                    this_dm.result = this_dm.result or 1
                    this_dm.stream.write("WARNING: The library name '{}' was not found ({}).\n".format(potential_names[0], library_path)) 

                    continue

                if basename.endswith(".dist-info"):
                    python_library.metadata_path = library_path

                    version = None

                    if version is None:
                        metadata_filename = os.path.join(library_path, "metadata.json")
                        if os.path.isfile(metadata_filename):
                            with open(metadata_filename) as f:
                                data = json.load(f)

                            if "version" not in data:
                                this_dm.result = -1
                                this_dm.stream.write("ERROR: 'version' was not found in '{}'.\n".format(library_path))

                                continue

                            version = data["version"]

                    if version is None:
                        metadata_filename = os.path.join(library_path, "METADATA")
                        if os.path.isfile(metadata_filename):
                            for line in open(metadata_filename, encoding="utf8").readlines():
                                if line.startswith("Version:"):
                                    version = line[len("Version:"):].strip()
                                    break

                    if version is None:
                        this_dm.result = -1
                        this_dm.stream.write("ERROR: Metadata was not found for '{}'.\n".format(library_path))

                        continue

                    python_library.version = version

                elif basename.endswith(".egg-info"):
                    python_library.metadata_path = library_path

                    metadata_filename = os.path.join(library_path, "PKG-INFO")
                    if not os.path.isfile(metadata_filename):
                        this_dm.result = -1
                        this_dm.stream.write("ERROR: Metadata was not found for '{}'.\n".format(metadata_filename))

                        continue

                    version = None

                    for line in open(metadata_filename).readlines():
                        if line.startswith("Version:"):
                            version = line[len("Version:"):].strip()
                            break

                    if version is None:
                        this_dm.result = -1
                        this_dm.stream.write("ERROR: 'Version:' was not found in '{}'.\n".format(metadata_filename))

                        continue

                    python_library.version = version

                else:
                    assert False, basename

            # Eliminate all library info where we couldn't extract the version
            for library_name in list(six.iterkeys(libraries)):
                if libraries[library_name].version is None:
                    this_dm.result = this_dm.result or 1
                    this_dm.stream.write("WARNING: Version information was not found for '{}'.\n".format(library_name))

                    libraries.pop(library_name)

            # Associate scripts with the known library info
            for script_fullpath in new_content.Scripts:
                if os.path.isdir(script_fullpath):
                    this_dm.result = this_dm.result or 1
                    this_dm.stream.write("WARNING: '{}' is a directory and will not be processed.\n".format(script_fullpath))

                    continue

                script_name_lower = os.path.splitext(os.path.basename(script_fullpath))[0].lower()

                found = False

                for potential_library_name, potential_library_info in six.iteritems(libraries):
                    if potential_library_name.lower() in script_name_lower:
                        potential_library_info.scripts.append(script_fullpath)

                        found = True
                        break

                if not found:
                    this_dm.result = this_dm.result or 1
                    this_dm.stream.write("WARNING: The library for the script '{}' could not be found.\n".format(script_fullpath))

        if dm.result < 0:
            return dm.result

        if not ignore_warnings and dm.result > 0:
            dm.stream.write("\nWarnings were encountered. To continue execution even with warnings, specify 'ignore_warnings' on the command line.\n")
            return dm.result

        if not libraries:
            return

        dm.stream.write("Moving content...")
        with dm.stream.DoneManager( suffix='\n',
                                  ) as move_dm:
            # ----------------------------------------------------------------------
            def DestinationIsOSSpecific(dest_dir):
                if not os.path.isdir(dest_dir):
                    return False

                found_one = False

                for item in os.listdir(dest_dir):
                    fullpath = os.path.join(dest_dir, item)
                    if not os.path.isdir(fullpath):
                        return False

                    found_one = True

                return found_one

            # ----------------------------------------------------------------------

            python_version_dir = "python{}".format(os.getenv("DEVELOPMENT_ENVIRONMENT_PYTHON_VERSION").split('.')[0])

            display_template = "{0:<50} -> {1}\n"

            for index, (library_name, library_info) in enumerate(six.iteritems(libraries)):
                move_dm.stream.write("Processing '{}' ({} of {})...".format( library_name,
                                                                             index + 1,
                                                                             len(libraries),
                                                                           ))
                with move_dm.stream.DoneManager( suffix='\n',
                                               ) as this_dm:
                    try:
                        if library_name.endswith(".py"):
                            library_name = library_name[:-len(".py")]

                        dest_dir = os.path.join( os.getenv("DEVELOPMENT_ENVIRONMENT_REPOSITORY"), 
                                                 RepositoryBootstrapConstants.LIBRARIES_SUBDIR, 
                                                 PythonActivationActivity.Name, 
                                                 library_name, 
                                                 "v{}".format(library_info.version),
                                               )
                        
                        prev_dest_is_os_specific = DestinationIsOSSpecific(dest_dir) 
                        dest_is_os_specific = new_content.HasOSSpecificLibraryExtensions(library_info.Fullpath) or prev_dest_is_os_specific

                        if dest_is_os_specific:
                            if not prev_dest_is_os_specific:
                                raise Exception(textwrap.dedent(
                                                    """\
                                                    The existing directory '{}' is not specific to an operating system and python version, but the new content is. 
                                                    Please move the existing content to an operating system- and python version-specific directory and run this tool again.
                                                    
                                                        Example: {}
                                                    """).format( dest_dir,
                                                                 os.path.join(dest_dir, CurrentShell.CategoryName, "<python2|python3>"),
                                                               ))

                            dest_dir = os.path.join(dest_dir, CurrentShell.CategoryName, python_version_dir)

                        # Copy the library
                        library_dest_dir = dest_dir
                        this_dm.stream.write(display_template.format(os.path.basename(library_info.Fullpath), library_dest_dir))

                        move_func(library_info.Fullpath, library_dest_dir)

                        # Copy the metadata
                        assert library_info.metadata_path

                        metadata_dest_dir = dest_dir
                        this_dm.stream.write(display_template.format(os.path.basename(library_info.metadata_path), metadata_dest_dir))

                        move_func(library_info.metadata_path, metadata_dest_dir)

                        # Copy the scripts
                        scripts_dest_dir = os.path.join(dest_dir, SCRIPTS_DIR_NAME)

                        if not dest_is_os_specific and bool(next((script for script in library_info.scripts if os.path.splitext(script)[1] in [ CurrentShell.ScriptExtension, CurrentShell.ExecutableExtension, ]), None)):
                            scripts_dest_dir = os.path.join(scripts_dest_dir, CurrentShell.CategoryName)

                        for script in library_info.scripts:
                            this_dm.stream.write(display_template.format("{} [Script]".format(os.path.basename(script)), scripts_dest_dir))
                            
                            if not no_move:
                                if PythonActivationActivity.NormalizeScript(script) == PythonActivationActivity.NormalizeScriptResult_Modified:
                                    this_dm.stream.write("    ** The script '{}' was normalized.\n".format(script))

                            move_func(script, scripts_dest_dir)

                    except Exception as ex:
                        this_dm.result = -1
                        this_dm.stream.write("ERROR: {}\n".format(StringHelpers.LeftJustify( str(ex),
                                                                                             len("ERROR: "),
                                                                                           )))

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( lib_name=CommandLine.StringTypeInfo(),
                          pip_arg=CommandLine.StringTypeInfo(arity='*'),
                          output_stream=None,
                        )
def Install( lib_name,
             pip_arg=None,
             output_stream=sys.stdout,
           ):
    """
    A replacement for pip install. Will ensure that already installed python libraries are not modified in-place,
    but rather considered as new libraries for the currently activated repository.
    """

    pip_args = pip_arg; del pip_arg

    repo_root = os.getenv(RepositoryBootstrapConstants.DE_REPO_ROOT_NAME)

    scm = GetSCM(repo_root, raise_on_error=False)
    if not scm:
        output_stream.write("ERROR: No SCM is active for '{}'.\n".format(repo_root))
        return -1

    if scm.HasWorkingChanges(repo_root) or scm.HasUntrackedWorkingChanges(repo_root):
        output_stream.write("ERROR: Changes were detected in '{}'; please revert/shelve these changes and run this script again.\n".format(repo_root))
        return -1

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        pip_command_line = 'pip install "{}"{}'.format( lib_name,
                                                        '' if not pip_args else " {}".format(' '.join(pip_args)),
                                                      )

        dm.stream.write("\nDetecting libraries...")
        with dm.stream.DoneManager( suffix='\n',
                                  ) as this_dm:
            libraries = []

            # ----------------------------------------------------------------------
            def OnOutput(line):
                this_dm.stream.write(line)

                if not line.startswith("Installing collected packages: "):
                    return True

                line = line[len("Installing collected packages: "):]

                for library in line.split(','):
                    library = library.strip()
                    if library:
                        libraries.append(library)

                return False

            # ----------------------------------------------------------------------

            this_dm.result = Process.Execute( pip_command_line,
                                              OnOutput,
                                              line_delimited_output=True,
                                            )

            if libraries:
                this_dm.result = 0

            if this_dm.result != 0:
                return this_dm.result

        if not libraries:
            return dm.result

        dm.stream.write("Reverting local changes...")
        with dm.stream.DoneManager( suffix='\n',
                                  ) as this_dm:
            this_dm.result = scm.Clean(repo_root, no_prompt=True)[0]

            if this_dm.result != 0:
                return this_dm.result

        dm.stream.write("Reverting existing libraries...")
        with dm.stream.DoneManager( suffix='\n',
                                  ) as this_dm:
            python_lib_dir = os.path.join( os.getenv(RepositoryBootstrapConstants.DE_REPO_GENERATED_NAME), 
                                           PythonActivationActivity.Name, 
                                           _EnvironmentSettings().LibraryDir,
                                         )
            assert os.path.isdir(python_lib_dir), python_lib_dir

            library_items = {}

            for name in os.listdir(python_lib_dir):
                fullpath = os.path.join(python_lib_dir, name)

                if not os.path.isdir(fullpath):
                    continue

                library_items[name.lower()] = CurrentShell.IsSymLink(fullpath)

            # ----------------------------------------------------------------------
            def RemoveItem(name):
                name_lower = name.lower()

                if library_items[name_lower]:
                    this_dm.stream.write("Removing '{}' for upgrade.\n".format(name))
                    os.remove(os.path.join(python_lib_dir, name))
                else:
                    this_dm.stream.write("Removing temporary '{}'.\n".format(name))
                    FileSystem.RemoveTree(os.path.join(python_lib_dir, name))

                del library_items[name_lower]

            # ----------------------------------------------------------------------

            for library in libraries:
                potential_library_names = [ library, ]

                # Sometimes, a library's name will begin with a 'Py' but be saved in
                # the file system without the 'Py' prefix. Account for that scenario.
                if library.lower().startswith("py"):
                    potential_library_names.append(library[len("py"):])

                for potential_library_name in potential_library_names:
                    potential_library_name_lower = potential_library_name.lower()

                    if potential_library_name_lower not in library_items:
                        continue

                    RemoveItem(potential_library_name)

                    # Is there dist- or egg-info as well?
                    info_items = []

                    for item in six.iterkeys(library_items):
                        if ( item.startswith(potential_library_name_lower) and 
                             (item.endswith(".dist-info") or item.endswith(".egg-info"))
                           ):
                            info_items.append(item)

                    for info_item in info_items:
                        RemoveItem(info_item)

                    break

        dm.stream.write("Installing...")
        with dm.stream.DoneManager() as this_dm:
            this_dm.result = Process.Execute(pip_command_line, this_dm.stream)

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints( script_filename_or_dir=CommandLine.FilenameTypeInfo(match_any=True),
                          output_stream=None,
                        )
def Normalize( script_filename_or_dir,
               output_stream=sys.stdout,
             ):
    """Normalizes a script so that it can be run from any location."""

    with StreamDecorator(output_stream).DoneManager( line_prefix='',
                                                     prefix="\nResults: ",
                                                     suffix='\n',
                                                   ) as dm:
        if os.path.isfile(script_filename_or_dir):
            script_filenames = [ script_filename_or_dir, ]
        elif os.path.isdir(script_filename_or_dir):
            script_filenames = list(FileSystem.WalkFiles(script_filename_or_dir, recurse=False))
        else:
            assert False

        for index, script_filename in enumerate(script_filenames):
            nonlocals = CommonEnvironment.Nonlocals(result=None)

            dm.stream.write("Processing '{}' ({} of {})...".format( script_filename,
                                                                    index + 1,
                                                                    len(script_filenames),
                                                                  ))
            with dm.stream.DoneManager( done_suffix=lambda: PythonActivationActivity.NormalizeScriptResultStrings[nonlocals.result],
                                      ):
                nonlocals.result = PythonActivationActivity.NormalizeScript(script_filename)
        
        return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class _EnvironmentSettings(object):
    """Python settings based on the current environment."""

    # ----------------------------------------------------------------------
    def __init__(self):
        sub_dict = {}

        for suffix in [ "PYTHON_VERSION",
                        "PYTHON_VERSION_SHORT",
                      ]:
            sub_dict[suffix.lower()] = os.getenv("DEVELOPMENT_ENVIRONMENT_{}".format(suffix))

        generated_dir = os.path.join(os.getenv(RepositoryBootstrapConstants.DE_REPO_GENERATED_NAME), PythonActivationActivity.Name)
        assert os.path.isdir(generated_dir), generated_dir

        # ----------------------------------------------------------------------
        def Populate(dirs):
            if not dirs:
                return generated_dir

            dirs = [ d.format(**sub_dict) for d in dirs ]
            return os.path.join(generated_dir, *dirs)

        # ----------------------------------------------------------------------

        self.LibraryDir                     = Populate(PythonActivationActivity.LibrarySubdirs)
        self.ScriptDir                      = Populate(PythonActivationActivity.ScriptSubdirs)
        self.Binary                         = os.path.join(Populate(PythonActivationActivity.BinSubdirs), "python{}".format(PythonActivationActivity.BinExtension or ''))

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
class _NewLibraryContent(object):
    """New python content based on the current environment"""

    # ----------------------------------------------------------------------
    @classmethod
    def Create(cls, settings):
        # ----------------------------------------------------------------------
        def GetItems(directory, ignore_set):
            items = []

            assert os.path.isdir(directory), directory
            is_bin_dir = PythonActivationActivity.BinSubdirs and directory.endswith(os.path.join(*PythonActivationActivity.BinSubdirs))
            
            for item in os.listdir(directory):
                if item in ignore_set:
                    continue

                fullpath = os.path.join(directory, item)
                if not CurrentShell.IsSymLink(fullpath):
                    if ( CurrentShell.CategoryName == "Linux" and 
                         is_bin_dir and 
                         item.startswith("python")
                       ):
                        continue

                    items.append(fullpath)

            return items

        # ----------------------------------------------------------------------

        # Get the libraries
        new_libraries = GetItems(settings.LibraryDir, set([ "__pycache__", EASY_INSTALL_PTH_FILENAME, ]))

        # Ignore .pyc files (which may be here for python 2.7)
        new_libraries = [ item for item in new_libraries if not os.path.splitext(item)[1] == ".pyc" ]

        # Get os-specific library extensions 
        os_specific_extensions = [ ".pyd", ".so", CurrentShell.ScriptExtension, ]
        if CurrentShell.ExecutableExtension:
            os_specific_extensions.append(CurrentShell.ExecutableExtension)

        new_library_extensions = []

        for new_library in new_libraries:
            if not os.path.isdir(new_library):
                continue

            new_library_extensions += FileSystem.WalkFiles( new_library,
                                                            include_file_extensions=os_specific_extensions,
                                                          )

        script_ignore_items = set([ "__pycache__", WRAPPERS_FILENAME, ])

        # Create the script's wrappers file to get a list of all the script files that
        # should be ignored.
        potential_filename = os.path.join(settings.ScriptDir, WRAPPERS_FILENAME)
        if os.path.isfile(potential_filename):
            for name in [ line.strip() for line in open(potential_filename).readlines() if line.strip() ]:
                script_ignore_items.add(name)

        # Get the scripts
        new_scripts = GetItems(settings.ScriptDir, script_ignore_items)

        # Get os-specific script extensions
        new_script_extensions = [ item for item in new_scripts if os.path.splitext(item)[1] in os_specific_extensions ]

        return cls( new_libraries,
                    new_library_extensions,
                    new_scripts,
                    new_script_extensions,
                  )

    # ----------------------------------------------------------------------
    def __init__( self,
                  libraries,
                  library_extensions,
                  scripts,
                  script_extensions,
                ):
        self.Libraries                      = libraries
        self.LibraryExtensions              = library_extensions
        self.Scripts                        = scripts
        self.ScriptExtensions               = script_extensions

    # ----------------------------------------------------------------------
    def HasOSSpecificLibraryExtensions(self, library):
        assert library in self.Libraries, library

        for item in self.LibraryExtensions:
            if item.startswith(library):
                return True

        return False

    # ----------------------------------------------------------------------
    def __str__(self):
        return CommonEnvironment.ObjectStrImpl(self)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try: sys.exit(CommandLine.Main())
    except KeyboardInterrupt: pass
