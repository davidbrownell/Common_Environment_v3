# ----------------------------------------------------------------------
# |
# |  AcquireBinaries.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-09-11 07:38:33
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Methods that help during setup and activate to acquire/download/unzip/install binaries."""

import hashlib
import json
import os
import shutil
import sys
import textwrap

import inflect as inflect_mod
import six
import tqdm

import CommonEnvironment
from CommonEnvironment import Nonlocals
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import CommandLine
from CommonEnvironment import FileSystem
from CommonEnvironment import Process
from CommonEnvironment.Shell.All import CurrentShell
from CommonEnvironment.StreamDecorator import StreamDecorator
from CommonEnvironment import StringHelpers
from CommonEnvironment import TaskPool

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
with CallOnExit(lambda: sys.path.pop(0)):
    from RepositoryBootstrap import Constants
    from RepositoryBootstrap.Impl.EnvironmentBootstrap import EnvironmentBootstrap

# ----------------------------------------------------------------------
inflect                                     = inflect_mod.engine()

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints(
    uri=CommandLine.UriTypeInfo(),
    output_filename=CommandLine.FilenameTypeInfo(
        ensure_exists=False,
    ),
    expected_sha256=CommandLine.StringTypeInfo(
        validation_expression="[A-Fa-f0-9]{64}",
        arity="?",
    ),
    output_stream=None,
)
def Download(
    uri,
    output_filename,
    expected_sha256=None,
    output_stream=sys.stdout,
):
    uri = uri.ToString()
    output_stream = StreamDecorator(output_stream)

    with output_stream.SingleLineDoneManager("Downloading '{}'...".format(uri)) as dm:
        temp_filename = CurrentShell.CreateTempFilename()

        nonlocals = Nonlocals(
            progress_bar=None,
            current=0,
        )

        # ----------------------------------------------------------------------
        def Callback(count, block_size, total_size):
            if nonlocals.progress_bar is None:
                nonlocals.progress_bar = tqdm.tqdm(
                    total=total_size,
                    desc="Downloading",
                    unit=" bytes",
                    file=dm.stream,
                    mininterval=0.5,
                    leave=False,
                    ncols=120,
                )
            else:
                assert count, block_size

                current = min(count * block_size, total_size)
                assert current >= nonlocals.current

                nonlocals.progress_bar.update(current - nonlocals.current)
                nonlocals.current = current

        # ----------------------------------------------------------------------

        six.moves.urllib.request.urlretrieve(
            uri,
            temp_filename,
            reporthook=Callback,
        )

        if nonlocals.progress_bar is not None:
            nonlocals.progress_bar.close()

    if expected_sha256:
        result = _CalculateHash(temp_filename, expected_sha256, output_stream)
        if result != 0:
            return result

    FileSystem.MakeDirs(os.path.dirname(output_filename))
    shutil.move(temp_filename, output_filename)

    return 0


# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints(
    name=CommandLine.StringTypeInfo(),
    uri=CommandLine.UriTypeInfo(),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
    ),
    unique_id=CommandLine.StringTypeInfo(
        arity="?",
    ),
    output_stream=None,
)
def Install(
    name,
    uri,
    output_dir,
    unique_id=None,
    unique_id_is_hash=False,
    no_output_dir_decoration=False,
    output_stream=sys.stdout,
):
    """Installs binaries to the specified output directory"""

    if unique_id_is_hash and unique_id is None:
        raise CommandLine.UsageException(
            "An unique id must be provided when 'unique_id_is_hash' is set.",
        )

    if not no_output_dir_decoration:
        output_dir = _AugmentOutputDir(output_dir)

    output_stream.write("Processing '{}'...".format(name))
    with StreamDecorator(output_stream).DoneManager(
        suffix="\n",
    ) as dm:
        if not _PreviousInstallation.Exists(output_dir):
            prev_installation = None
        else:
            try:
                prev_installation = _PreviousInstallation.Load(output_dir)
            except Exception as ex:
                dm.stream.write(
                    "WARNING: {}\n".format(
                        StringHelpers.LeftJustify(str(ex), len("WARNING: ")),
                    ),
                )
                dm.result = 1

                prev_installation = None

        if prev_installation is not None:
            if prev_installation.UniqueId == unique_id:
                dm.stream.write(
                    textwrap.dedent(
                        """\
                        The content already exists and will not be overwritten. Please delete the directory
                        if this content is not valid or needs to be reacquired.

                            {}
                        """,
                    ).format(output_dir),
                )

                return dm.result

            dm.result = _CleanImpl(
                output_dir,
                prev_installation.OriginalFileNames,
                dm.stream,
            )
            if dm.result < 0:
                return dm.result

        if uri.Scheme == "file":
            filename = uri.ToFilename()
            FilenameCleanup = lambda: None

        else:
            filename = CurrentShell.CreateTempFilename(".zip")
            FilenameCleanup = lambda: FileSystem.RemoveFile(filename)

            dm.result = Download(
                uri,
                filename,
                output_stream=dm.stream,
            )

            if dm.result != 0:
                return dm.result

        uri = uri.ToString()

        with CallOnExit(FilenameCleanup):
            assert os.path.isfile(filename), filename

            if unique_id_is_hash:
                dm.result = _CalculateHash(filename, unique_id, dm.stream)
                if dm.result != 0:
                    return dm.result

            temp_directory = "{}_tmp".format(output_dir)

            FileSystem.RemoveTree(temp_directory)
            FileSystem.MakeDirs(temp_directory)

            # Extract the content to a temporary folder
            dm.stream.write("Extracting content...")
            with dm.stream.DoneManager() as extract_dm:
                command_line = '7za x -y "{}"'.format(filename)
                sink = six.moves.StringIO()

                previous_dir = os.getcwd()
                os.chdir(temp_directory)

                with CallOnExit(lambda: os.chdir(previous_dir)):
                    extract_dm.result = Process.Execute(command_line, sink)
                    if extract_dm.result != 0:
                        extract_dm.stream.write(sink.getvalue())
                        return extract_dm.result

                # On Linux, we may have extracted a single tar ball. If so, extract this too.
                items = os.listdir(temp_directory)
                if len(items) == 1 and (
                    os.path.splitext(items[0])[1] == ".tar"
                    or os.path.splitext(os.path.splitext(uri)[0])[1] == ".tar"
                ):
                    tarball_temp_directory = CurrentShell.CreateTempDirectory()

                    with CallOnExit(lambda: FileSystem.RemoveTree(temp_directory)):
                        extract_dm.stream.write("Extracting tarball...")
                        with extract_dm.stream.DoneManager() as tarball_dm:
                            command_line = 'tar -xf "{}"'.format(
                                os.path.join(temp_directory, items[0]),
                            )
                            sink = six.moves.StringIO()

                            tarball_previous_dir = os.getcwd()
                            os.chdir(tarball_temp_directory)

                            with CallOnExit(lambda: os.chdir(tarball_previous_dir)):
                                tarball_dm.result = Process.Execute(command_line, sink)
                                if tarball_dm.result != 0:
                                    tarball_dm.stream.write(sink.getvalue())
                                    return tarball_dm.result

                    temp_directory = tarball_temp_directory

            with CallOnExit(lambda: FileSystem.RemoveTree(temp_directory)):
                content_directory = temp_directory

                # If the content directory has a single item and that item is a directory, drill
                # in and copy the contents rather than the directory itself.
                items = os.listdir(temp_directory)
                if len(items) == 1:
                    potential_dir = os.path.join(temp_directory, items[0])
                    if os.path.isdir(potential_dir):
                        content_directory = potential_dir

                # Get a list of the original items
                FileSystem.MakeDirs(output_dir)
                original_items = list(os.listdir(output_dir))

                # Write the metadata
                _PreviousInstallation(unique_id, original_items).Save(content_directory)

                # Move items
                dm.stream.write("Finalizing content...")
                with dm.stream.DoneManager() as final_dm:
                    for item in os.listdir(content_directory):
                        src = os.path.join(content_directory, item)
                        dst = os.path.join(output_dir, item)

                        if os.path.exists(dst):
                            final_dm.stream.write(
                                "ERROR: '{}' already exists at the destination ('{}').\n".format(
                                    src,
                                    dst,
                                ),
                            )
                            final_dm.result = -1

                            continue

                        shutil.move(src, dst)

                    if final_dm.result != 0:
                        return final_dm.result

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints(
    output_dir=CommandLine.DirectoryTypeInfo(),
    output_stream=None,
)
def Clean(
    output_dir,
    output_stream=sys.stdout,
):
    output_dir = _AugmentOutputDir(output_dir)

    with StreamDecorator(output_stream).DoneManager(
        line_prefix="",
        prefix="\nResults: ",
        suffix="\n",
    ) as dm:
        if not _PreviousInstallation.Exists(output_dir):
            dm.stream.write(
                "ERROR: '{}' is not a directory that was populated by AcquireBinaries.\n".format(
                    output_dir,
                ),
            )
            dm.result = -1

            return dm.result

        try:
            prev_installation = _PreviousInstallation.Load(output_dir)
        except Exception as ex:
            dm.stream.write(
                "ERROR: {}.\n".format(StringHelpers.LeftJustify(str(ex), len("ERROR: "))),
            )
            dm.result = -1

            return dm.result

        dm.result = _CleanImpl(output_dir, prev_installation.OriginalFileNames, dm.stream)
        if dm.result != 0:
            return dm.result

        return dm.result

# ----------------------------------------------------------------------
@CommandLine.EntryPoint
@CommandLine.Constraints(
    app_name=CommandLine.StringTypeInfo(),
    output_dir=CommandLine.DirectoryTypeInfo(
        ensure_exists=False,
    ),
    unique_id=CommandLine.StringTypeInfo(),
    output_stream=None,
)
def Verify(
    app_name,
    output_dir,
    unique_id,
    output_stream=sys.stdout,
):
    """Verifies that the unique_id associated with a previously installed output directory matches the expected value."""

    output_dir = _AugmentOutputDir(output_dir)

    output_stream.write("Verifying '{}'...".format(app_name))
    with StreamDecorator(output_stream).DoneManager() as dm:
        if not _PreviousInstallation.Exists(output_dir):
            dm.stream.write(
                "ERROR: The output directory '{}' associated with the application '{}' does not exist.\n".format(
                    output_dir,
                    app_name,
                ),
            )
            dm.result = -1

            return dm.result

        previous_installation = _PreviousInstallation.Load(output_dir)
        if previous_installation.UniqueId != unique_id:
            sys.path.insert(0, os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL"))
            with CallOnExit(lambda: sys.path.pop(0)):
                from RepositoryBootstrap import Constants

            dm.stream.write(
                textwrap.dedent(
                    """\
                    ERROR: The installation of '{}' at '{}' is not the expected version ('{}' != '{}').
                           Please run '{}' for this repository to update the installation.
                    """,
                ).format(
                    app_name,
                    output_dir,
                    previous_installation.UniqueId,
                    unique_id,
                    CurrentShell.CreateScriptName(Constants.SETUP_ENVIRONMENT_NAME),
                ),
            )
            dm.result = -1

            return dm.result

        return dm.result

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
def _CalculateHash(filename, sha256hash, output_stream):
    output_stream.write("Validating content...")
    with output_stream.DoneManager() as dm:
        hash = hashlib.sha256()

        with open(filename, "rb") as f:
            while True:
                block = f.read(4096)
                if not block:
                    break

                hash.update(block)

        hash = hash.hexdigest().lower()

        sha256hash = sha256hash.lower()

        if hash != sha256hash:
            dm.stream.write(
                "ERROR: The hash values do not match (actual: {}, expected: {})\n".format(
                    hash,
                    sha256hash,
                ),
            )

            dm.result = -1

        return dm.result


# ----------------------------------------------------------------------
def _CleanImpl(output_dir, original_filenames, output_stream):
    output_stream.write("Cleaning previous content...")
    with output_stream.DoneManager() as dm:
        # Get the items to remove
        paths_to_remove = []

        dm.stream.write("Calculating items to remove...")
        with dm.stream.DoneManager(
            done_suffix=lambda: inflect.no("item", len(paths_to_remove)),
        ) as calculate_dm:
            for item in os.listdir(output_dir):
                if item not in original_filenames:
                    paths_to_remove.append(os.path.join(output_dir, item))

        if not paths_to_remove:
            return dm.result

        with dm.stream.SingleLineDoneManager("Removing items...") as this_dm:
            this_dm.result = TaskPool.Execute(
                [
                    TaskPool.Task(
                        path_to_remove,
                        (
                            lambda path_to_remove=path_to_remove: 0
                            if FileSystem.RemoveItem(path_to_remove)
                            else -1
                        ),
                    ) for path_to_remove in paths_to_remove
                ],
                this_dm.stream,
                progress_bar=True,
                num_concurrent_tasks=1,
            )
        return dm.result


# ----------------------------------------------------------------------
def _AugmentOutputDir(output_dir):
    # Augment the path if we are looking at a tool installation
    path_parts = output_dir.split(os.path.sep)

    try:
        tools_index = path_parts.index(Constants.TOOLS_SUBDIR)
    except ValueError:
        return output_dir

    potential_root_dir = os.path.sep.join(path_parts[:tools_index])
    if os.path.isdir(potential_root_dir) and os.path.isfile(
        os.path.join(
            potential_root_dir,
            Constants.SETUP_ENVIRONMENT_CUSTOMIZATION_FILENAME,
        ),
    ):
        # If here, the input dir was pointing to a tools dir off of a repository
        # root. Augment the path with the environment dir.
        output_dir = EnvironmentBootstrap.GetEnvironmentDir(output_dir)

    return output_dir


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
class _PreviousInstallation(object):

    UNIQUE_ID_FILENAME                      = "__AcquireBinariesMetadata__.json"

    # ----------------------------------------------------------------------
    @classmethod
    def Exists(cls, output_dir):
        potential_filename = os.path.join(output_dir, cls.UNIQUE_ID_FILENAME)
        return os.path.isfile(potential_filename)

    # ----------------------------------------------------------------------
    @classmethod
    def Load(cls, output_dir):
        potential_filename = os.path.join(output_dir, cls.UNIQUE_ID_FILENAME)
        if not os.path.isfile(potential_filename):
            raise Exception("The file '{}' does not exist".format(potential_filename))

        try:
            with open(potential_filename) as f:
                content = json.load(f)

            unique_id = content["unique_id"]
            original_filenames = content["original_filenames"]

        except:
            raise Exception(
                "The content in '{}' appears to be corrupt".format(potential_filename),
            )

        return cls(unique_id, original_filenames)

    # ----------------------------------------------------------------------
    def __init__(
        self,
        unique_id,
        original_files=None,                # List of basenames that existed in the output dir before a binary was installed;
                                            # All files other than these will be deleted before applying a new version of the                                    # binary.
    ):
        self.UniqueId                       = unique_id
        self.OriginalFileNames              = original_files or []

    # ----------------------------------------------------------------------
    def Save(self, output_dir):
        data = {"unique_id": self.UniqueId, "original_filenames": self.OriginalFileNames}

        with open(os.path.join(output_dir, self.UNIQUE_ID_FILENAME), "w") as f:
            json.dump(data, f)


# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
if __name__ == "__main__":
    try:
        sys.exit(CommandLine.Main())
    except KeyboardInterrupt:
        pass
