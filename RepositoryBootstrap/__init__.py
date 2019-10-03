# ----------------------------------------------------------------------
# |
# |  __init__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-01 18:32:46
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-19.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Code helpful during the bootstrap process."""

import json
import os
import re
import sys

from collections import OrderedDict

# ----------------------------------------------------------------------
def GetFundamentalRepository():
    """Returns the location of the fundamental repository."""

    # Try to get the value from the environment
    env_var = os.getenv("DEVELOPMENT_ENVIRONMENT_FUNDAMENTAL")
    if env_var:
        return env_var

    # Try to get the value relative to the working dir
    potential_generated_dir = os.path.join(os.getcwd(), "Generated")
    if os.path.isdir(potential_generated_dir):
        # Get the bootstrap data file
        # ----------------------------------------------------------------------
        def GetBootstrapData():
            for root, dirs, filenames in os.walk(potential_generated_dir):
                for filename in filenames:
                    if filename == "EnvironmentBootstrap.data":
                        return os.path.join(root, filename)

            return None

        # ----------------------------------------------------------------------

        bootstrap_filename = GetBootstrapData()
        if bootstrap_filename is not None:
            fundamental_root = None

            for line in open(bootstrap_filename).readlines():
                if line.startswith("fundamental_repo="):
                    fundamental_root = line[len("fundamental_repo=") :].strip()
                    break

            if fundamental_root:
                fundamental_root = os.path.realpath(
                    os.path.join(os.getcwd(), fundamental_root),
                )
                if os.path.isdir(fundamental_root):
                    return fundamental_root

    # Try to get the value relative to this file
    potential_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
    if os.path.isdir(potential_dir) and os.path.isdir(
        os.path.join(potential_dir, "Generated"),
    ):
        return potential_dir

    raise Exception("The fundamental repository could not be found")


# ----------------------------------------------------------------------
_GetRepositoryInfo_regex                    = None


def GetRepositoryInfo(
    repo_root,
    raise_on_error=True,
):
    """Returns that name and unique id of the repository as the specified root."""

    from RepositoryBootstrap import Constants
    from RepositoryBootstrap.Impl import CommonEnvironmentImports

    global _GetRepositoryInfo_regex

    if _GetRepositoryInfo_regex is None:
        _GetRepositoryInfo_regex = CommonEnvironmentImports.RegularExpression.TemplateStringToRegex(
            Constants.REPOSITORY_ID_CONTENT_TEMPLATE,
        )

    filename = os.path.join(repo_root, Constants.REPOSITORY_ID_FILENAME)
    if os.path.isfile(filename):
        match = _GetRepositoryInfo_regex.match(open(filename).read())
        if not match:
            if raise_on_error:
                raise Exception(
                    "The content in '{}' appears to be corrupt.".format(filename),
                )

            return None

        name = match.group("name")
        unique_id = match.group("id").upper()

    else:
        if raise_on_error:
            raise Exception(
                "Unable to find repository information for '{}'".format(repo_root),
            )

        return None

    return name, unique_id

# ----------------------------------------------------------------------
def GetRepoMapFromSetup(
    repository_root,
    max_repo_search_depth=None,
    required_ancestor_dir=None,
):
    """\
    Returns a repository map generated by calling a Setup file's List method. Note that this method
    is expensive, as it invokes external processes and walks the local file system (potentially exhaustively
    if dependency repositories aren't found.

    Activated environments should call GetPrioritizedRepositories.
    """

    from RepositoryBootstrap import Constants
    from RepositoryBootstrap.Impl import CommonEnvironmentImports

    result, output = CommonEnvironmentImports.Process.Execute(
        "{} List /recurse /json /decorate{}{}".format(
            os.path.join(
                repository_root,
                CommonEnvironmentImports.CurrentShell.CreateScriptName(
                    Constants.SETUP_ENVIRONMENT_NAME,
                ),
            ),
            ""
            if not max_repo_search_depth
            else ' "/search_depth={}"'.format(max_repo_search_depth),
            ""
            if not required_ancestor_dir
            else ' "/required_ancestor_dir={}"'.format(required_ancestor_dir),
        ),
    )
    if result != 0:
        raise Exception(
            "Unable to invoke the repository's list functionality:\n\n{}\n".format(output),
        )

    match = re.search(
        r"//--//--//--//--//--//--//--//--//--//--//--//--//--//--//--//\s+(?P<content>.+?)\s+//--//--//--//--//--//--//--//--//--//--//--//--//--//--//--//",
        output,
        re.DOTALL | re.MULTILINE,
    )
    if not match:
        raise Exception("Unable to extract content from:\n\n{}\n".format(output))

    match = match.group("content")

    try:
        content = json.loads(
            match,
            object_pairs_hook=OrderedDict,
        )
    except:
        raise Exception("The JSON content is not valid:\n\n{}\n".format(match))

    # Convert the items with special None placeholders back to None

    # ----------------------------------------------------------------------
    class Value(object):
        # ----------------------------------------------------------------------
        def __init__(self, json_item):
            self.Name                       = json_item["name"]
            self.Id                         = json_item["id"]
            self.Root                       = json_item["root"]
            self.CloneUri                   = json_item["clone_uri"]
            self.Priority                   = json_item["priority"]
            self.Configurations             = json_item["configurations"]
            self.Dependencies               = OrderedDict(
                [
                    (None if k == "<None>" else k, [tuple(item) for item in v])
                    for k,
                    v in six.iteritems(json_item["dependencies"])
                ],
            )
            self.Dependents                 = OrderedDict(
                [
                    (None if k == "<None>" else k, [tuple(item) for item in v])
                    for k,
                    v in six.iteritems(json_item["dependents"])
                ],
            )

        # ----------------------------------------------------------------------
        def __repr__(self):
            return CommonEnvironmentImports.CommonEnvironment.ObjectReprImpl(self)

    # ----------------------------------------------------------------------

    return OrderedDict([(item["id"], Value(item)) for item in content])

# ----------------------------------------------------------------------
def GetPrioritizedRepositories():
    """Returns the prioritized repositories for the currently activated environment"""
    from RepositoryBootstrap.Impl.ActivationData import ActivationData

    return ActivationData.Load(None, None, False).PrioritizedRepositories


# ----------------------------------------------------------------------

# This file may be invoked by our included version of python; if so, all imports
# will work as expected. However, this file may be invoked by a frozen executable.
# In those cases, go through a bit more work to ensure that these imports work as
# expected.
_updated_path                               = False

while True:
    try:
        import enum
        import inflect
        import six
        import wrapt

        # If here, everything was found and all is good
        break

    except ImportError:
        if _updated_path:
            raise

        _updated_path                       = True

        # If here, we are in a frozen environment. Hard-code an import path to
        # a known python location relative to the fundamental dir; this implies
        # that the environment has been at least setup.
        #
        # It doesn't matter which version of python we use, as they should be
        # a part of all of them.

        fundamental_repo                    = GetFundamentalRepository()

        python_root                         = os.path.join(fundamental_repo, "Tools", "Python", "v2.7.14")
        assert os.path.isdir(python_root), python_root

        import platform

        platform_name                       = platform.system().lower()

        if platform_name == "windows":
            python_name                     = "python.exe"
            binary_dir_to_lib_dir_func      = lambda binary_dir: os.path.join(
                binary_dir,
                "Lib",
                "site-packages",
            )
        elif platform_name == "linux":
            python_name                     = "python"
            binary_dir_to_lib_dir_func      = lambda binary_dir: os.path.join(
                binary_dir,
                "..",
                "lib",
                "python2.7",
                "site-packages",
            )
        else:
            raise Exception(platform_name)

        # ----------------------------------------------------------------------
        def ApplyLibDir():
            for root, dirs, filenames in os.walk(python_root):
                for filename in filenames:
                    if filename == python_name:
                        lib_dir = binary_dir_to_lib_dir_func(root)

                        sys.path.insert(0, lib_dir)
                        return

        # ----------------------------------------------------------------------

        ApplyLibDir()

        del fundamental_repo

if _updated_path:
    del sys.path[0]

# ----------------------------------------------------------------------
# |
# |  Public Methods
# |
# ----------------------------------------------------------------------
@wrapt.decorator
def MixinRepository(wrapped, instance, args, kwargs):
    """
    Signals that a repository is a mixin repository (a repository that
    contains items that help in the development process but doesn't contain
    primitives used by other dependent repositories). Mixin repositories
    must be activated on top of other repositories and make not may any
    assumptions about the state of the repository on which they are activated.
    """
    return wrapped(*args, **kwargs)
