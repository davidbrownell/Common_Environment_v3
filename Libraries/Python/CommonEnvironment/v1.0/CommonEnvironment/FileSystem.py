# ----------------------------------------------------------------------
# |  
# |  FileSystem.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-03 15:54:54
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Utilities helpful when working with the file system."""

import os
import sys
import time

import six

from CommonEnvironment.Shell.All import CurrentShell

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
CODE_EXCLUDE_DIR_NAMES                      = [ "Generated",
                                                "__pycache__",
                                                ".hg",                      # Mercurial
                                                ".git",                     # Git
                                                ".svn",                     # Subversion
                                                "$tf",                      # Team Foundation
                                              ]

CODE_EXCLUDE_FILE_EXTENSIONS                = [ # Python
                                                ".pyc",
                                                ".pyo",
                                              ]

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def GetCommonPath(*items):
    """Returns a path that is common to all of the provided items."""

    if not items:
        return ''

    if CurrentShell.HasCaseSensitiveFileSystem:
        # ----------------------------------------------------------------------
        def Equal(value1, value2):
            return value1 == value2

        # ----------------------------------------------------------------------

    else:
        # ----------------------------------------------------------------------
        def Equal(value1, value2):
            return value1.lower() == value2.lower()

        # ----------------------------------------------------------------------

    if len(items) == 1:
        result = items[0]

        if os.path.isfile(result):
            result = os.path.dirname(result)

        return AddTrailingSep(result)

    # Break the items into parts, as comparing by strings leads to strange corner cases
    # with partially matching paths.
    items = [ os.path.realpath(item).split(os.path.sep) for item in items ]

    path_index = 0
    while True:
        should_continue = True

        for item_index, item in enumerate(items):
            if path_index >= len(item):
                should_continue = False
                break

            if item_index != 0 and not Equal(items[item_index][path_index], items[item_index - 1][path_index]):
                should_continue = False
                break

        if not should_continue:
            break

        path_index += 1

    if path_index == 0:
        return ''

    return AddTrailingSep(os.path.sep.join(items[0][:path_index]))

# ----------------------------------------------------------------------
def GetRelativePath(starting_dir, dest):
    """Creates a relative path from the starting_dir to the dest."""

    assert starting_dir
    assert dest

    starting_dir = os.path.realpath(starting_dir).rstrip(os.path.sep)
    dest = os.path.realpath(dest).rstrip(os.path.sep)

    common_prefix = GetCommonPath(starting_dir, dest)
    if not common_prefix:
        return dest

    starting_dir = starting_dir[len(common_prefix):]
    dest = dest[len(common_prefix):]

    if not starting_dir:
        if not dest:
            return '.'

        return os.path.join(".", dest)

    seps = os.path.splitdrive(starting_dir)[1].count(os.path.sep) + 1
    
    return "{}{}".format((("..{}".format(os.path.sep)) * seps), dest)

# ----------------------------------------------------------------------
def TrimPath(fullpath, initial_path):
    """Removes the intial path from the fullpath"""

    if CurrentShell.HasCaseSensitiveFileSystem:
        decorator_func = lambda item: item
    else:
        decorator_func = lambda item: item.lower()

    if not decorator_func(fullpath).startswith(decorator_func(initial_path)):
        raise Exception("'{}' does not begin with '{}'".format(fullpath, iniitial_path))

    fullpath = fullpath[len(initial_path):]
    if fullpath.startswith(os.path.sep):
        fullpath = fullpath[len(os.path.sep):]

    return fullpath

# ----------------------------------------------------------------------
def AddTrailingSep(value):
    if not value.endswith(os.path.sep):
        value += os.path.sep

    return value

# ----------------------------------------------------------------------
def Normalize(path):
    """Normalizes a path, including ensuring case consistency."""

    path = os.path.normpath(path)
    
    if not CurrentShell.HasCaseSensitiveFileSystem:
        if os.path.exists(path) and CurrentShell.Name == "Windows":
            import win32api

            # <Module 'win32api' has not 'GetLongPathName' member, but source is unavailable. Consider adding this module to extension-pkg-whitelist if you want to perform analysis based on run-time introspection of living objects.> pylint: disable = I1101

            path = win32api.GetLongPathName(win32api.GetShortPathName(path))

        drive, suffix = os.path.splitdrive(path)
        path = "{}{}".format(drive.upper(), suffix)

    return path

# ----------------------------------------------------------------------
def GetSizeDisplay(num_bytes, suffix='B'):
    for unit in [ '', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', ]:
        if num_bytes < 1024.0:
            return "%3.1f %s%s" % (num_bytes, unit, suffix)

        num_bytes /= 1024.0

    return "%.1f %s%s" % (num_bytes, 'Yi', suffix)

# ----------------------------------------------------------------------
def MakeDirs(path):
    if not os.path.isdir(path):
        os.makedirs(path)

# ----------------------------------------------------------------------
def RemoveTree( path,
                optional_retry_iterations=5,
              ):
    """Removes a directory and its children in the most efficient way possible"""
    if not os.path.isdir(path):
        return False
    
    _RemoveImpl(CurrentShell.RemoveDir, path, optional_retry_iterations)
    return True

# ----------------------------------------------------------------------
def RemoveFile( path,
                optional_retry_iterations=5,
              ):
    """Removes a file in the most efficient way possible."""
    if not os.path.isfile(path):
        return False

    _RemoveImpl(os.remove, path, optional_retry_iterations)
    return True

# ----------------------------------------------------------------------
def WalkDirs( directory,

              include_dir_names=None,                   # e.g. "A_Single_Dir"
              exclude_dir_names=None,                   # e.g. "A_Single_Dir"

              include_dir_paths=None,                   # e.g. "C:\Foo\Bar"
              exclude_dir_paths=None,                   # e.g. "C:\Foo\Bar"

              traverse_include_dir_names=None,          # e.g. "A_Single_Dir"
              traverse_exclude_dir_names=None,          # e.g. "A_Single_Dir"

              traverse_include_dir_paths=None,          # e.g. "C:\Foo\Bar"
              traverse_exclude_dir_paths=None,          # e.g. "C:\Foo\Bar"

              recurse=True,
              include_generated=False,
            ):
    """
    Yields ( root, filenames ) on a (potentially) recursive search.
    
    All include/exclude values can be strings, callable, or regular expressions.
    """

    process_dir_name = _ProcessWalkArgs(include_dir_names, exclude_dir_names)
    process_dir_path = _ProcessWalkArgs(include_dir_paths, exclude_dir_paths)

    process_traverse_dir_name = _ProcessWalkArgs(traverse_include_dir_names, traverse_exclude_dir_names)
    process_traverse_dir_path = _ProcessWalkArgs(traverse_include_dir_paths, traverse_exclude_dir_paths)

    if include_generated:
        # ----------------------------------------------------------------------
        def IsValid(fullpath, directory):
            return ( process_traverse_dir_path(fullpath) and
                     process_traverse_dir_name(directory)
                   )

        # ----------------------------------------------------------------------
    else:
        # ----------------------------------------------------------------------
        def IsValid(fullpath, directory):
            return ( directory not in CODE_EXCLUDE_DIR_NAMES and
                     process_traverse_dir_path(fullpath) and
                     process_traverse_dir_name(directory)
                   )

        # ----------------------------------------------------------------------

    for root, dirs, filenames in os.walk(Normalize(directory)):
        try:
            root = str(root)
        except UnicodeEncodeError:
            continue

        root = os.path.realpath(root)

        # Ensure that the drive letter is uppercase
        drive, suffix = os.path.splitdrive(root)
        drive = drive.upper()

        root = "{}{}".format(drive, suffix)

        if process_dir_path(root) and process_dir_name(os.path.basename(root)):
            yield root, filenames

        index = 0
        while index < len(dirs):
            fullpath = os.path.join(root, dirs[index])

            if not IsValid(fullpath, dirs[index]):
                dirs.pop(index)
            else:
                index += 1

        if not recurse:
            dirs[:] = []

# ----------------------------------------------------------------------
def WalkFiles( directory,

               include_dir_names=None,                  # A_Single_Dir
               exclude_dir_names=None,                  # A_Single_Dir

               include_dir_paths=None,                  # C:\Foo\Bar
               exclude_dir_paths=None,                  # C:\Foo\Bar

               traverse_include_dir_names=None,         # A_Single_Dir
               traverse_exclude_dir_names=None,         # A_Single_Dir

               traverse_include_dir_paths=None,         # C:\Foo\Bar
               traverse_exclude_dir_paths=None,         # C:\Foo\Bar

               include_file_base_names=None,            # File where filename is File.ext
               exclude_file_base_names=None,            # File where filename is File.ext

               include_file_extensions=None,            # .py
               exclude_file_extensions=None,            # .py

               include_file_names=None,                 # File.ext
               exclude_file_names=None,                 # File.ext

               include_full_paths=None,                 # C:\Foo\Bar\File.ext
               exclude_full_paths=None,                 # C:\Foo\Bar\File.ext

               recurse=True,
               include_generated=False,
             ):
    """
    Yields <filename> on a (potentially) recursive search.
    
    All include/exclude values can be strings, callable, or regular expressions.
    """

    process_file_name = _ProcessWalkArgs(include_file_names, exclude_file_names)
    process_file_base_name = _ProcessWalkArgs(include_file_base_names, exclude_file_base_names)
    process_file_extension = _ProcessWalkArgs(include_file_extensions, exclude_file_extensions)
    process_full_path = _ProcessWalkArgs(include_full_paths, exclude_full_paths)

    for root, filenames in WalkDirs( directory,
                                     include_dir_names=include_dir_names,
                                     exclude_dir_names=exclude_dir_names,
                                     include_dir_paths=include_dir_paths,
                                     exclude_dir_paths=exclude_dir_paths,
                                     traverse_include_dir_names=traverse_include_dir_names,
                                     traverse_exclude_dir_names=traverse_exclude_dir_names,
                                     traverse_include_dir_paths=traverse_include_dir_paths,
                                     traverse_exclude_dir_paths=traverse_exclude_dir_paths,
                                     recurse=recurse,
                                     include_generated=include_generated,
                                   ):
        for filename in filenames:
            if not process_file_name(filename):
                continue

            base_name, ext = os.path.splitext(filename)

            if ( not process_file_extension(ext) or
                 not process_file_base_name(base_name)
               ):
                continue

            fullpath = os.path.join(root, filename)

            if not process_full_path(fullpath):
                continue

            yield fullpath

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _RemoveImpl( func,                      # def Func(path)
                 path,
                 optional_retry_iterations,
               ):
    assert os.path.exists(path), path

    # Rename the dir or item to a temporary one and then remove the renamed item.
    # This technique works around timing issues associated with quickly creating
    # a new item immediately after it has just been deleted.
    iteration = 0

    while True:
        potential_renamed_path = "{}_ToDelete{}".format(path, iteration)
        if not os.path.exists(potential_renamed_path):
            renamed_path = potential_renamed_path
            break

        iteration += 1

    # Invoke
    iteration = 0
    while True:
        try:
            os.rename(path, renamed_path)
            break
        except:
            if optional_retry_iterations is not None:
                # Handle temporary permission denied errors by retrying after a period of time
                time.sleep(iteration * 0.5 + 0.5)       # seconds

                iteration += 1
                if iteration < optional_retry_iterations:
                    continue

            raise

    func(renamed_path)

# ----------------------------------------------------------------------
def _ProcessWalkArgs(include_items, exclude_items):
    # ----------------------------------------------------------------------
    def Preprocess(items):
        if items is None:
            return []

        if isinstance(items, list):
            return items

        return [ items, ]

    # ----------------------------------------------------------------------
    def IsIn(value, items):
        for item in items:
            if isinstance(item, six.string_types) and item == value:
                return True

            elif callable(item):
                try:
                    if item(value):
                        return True
                except: 
                    pass

            elif hasattr(item, "match") and item.match(value):
                return True

        return False

    # ----------------------------------------------------------------------

    include_items = Preprocess(include_items)
    exclude_items = Preprocess(exclude_items)

    # ----------------------------------------------------------------------
    def Impl(value):
        if exclude_items and IsIn(value, exclude_items):
            return False

        if include_items and not IsIn(value, include_items):
            return False

        return True

    # ----------------------------------------------------------------------

    return Impl


# TODO: CopyTree
