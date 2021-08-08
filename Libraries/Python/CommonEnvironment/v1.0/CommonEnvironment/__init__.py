# ----------------------------------------------------------------------
# |
# |  __init__.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-20 19:28:09
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2018-21.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |
# ----------------------------------------------------------------------
"""Contains types and methods that are fundamental"""

import os
import re
import sys

from collections import OrderedDict

import six

# ----------------------------------------------------------------------
# |
# |  Public Types
# |
# ----------------------------------------------------------------------
class Nonlocals(object):
    """
    Python 2.7 compatible replacement for the nonlocal keyword.

    Example:
        nonlocals = Nonlocals(x=10, y=20)

        def Foo():
            nonlocals.x = 30
            nonlocals.y = 40

        Foo()

        # nonlocals.x == 30
        # nonlocals.y == 40
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

# ----------------------------------------------------------------------
# |
# |  Public Methods
# |
# ----------------------------------------------------------------------
def Get(
    items,
    functor,                                # def Func(item) -> bool
    extractor=None,                         # def Func(item) -> Any
):
    """\
    Returns an item in an iterable list if it matches the criteria encapsulated within functor.

    This is similar to `next`, without the need to worry about `StopIteration` if no
    matching items are found.
    """

    for item in items:
        if functor(item):
            return extractor(item) if extractor else item

    return None


# ----------------------------------------------------------------------
def ThisFullpath():
    """Returns the filename of the caller, taking into account symlinks and frozen executables."""

    if "python" not in sys.executable.lower():
        return sys.executable

    import inspect

    if sys.version_info[0] == 2:
        frame = inspect.stack()[1][0]
        filename = inspect.getframeinfo(frame).filename
    else:
        filename = os.path.realpath(os.path.abspath(inspect.stack()[1].filename))

        # WSL manages to screw up this path value
        if filename.startswith("/mnt/"):
            index = filename.find(":")
            if index != -1:
                # Recreate the path based on the information detected
                filename = "/mnt/{}/{}".format(
                    filename[filename.rfind("/", 0, index) + 1:index].lower(),
                    filename[index + 1:].replace("\\", "/"),
                )

    assert os.path.exists(filename), filename

    if os.path.islink(filename):
        filename = os.readlink(filename)

    return filename


# ----------------------------------------------------------------------
# Global used to prevent infinite recursion loops for types that reference ancestors in its type
# heierarchy. This functionality cannot be a parameter of this function, as this functionality may
# be invoked from __repr__ methods (which do not take arguments).
_describe_stack                             = set()

def Describe(
    item,
    output_stream=sys.stdout,
    unique_id=None,
    include_class_info=True,
    include_id=True,
    include_methods=False,
    include_private=False,
    recurse=True,
    **custom_display_funcs # Callable[[Any], Optional[str]]
):
    """Writes formatted information about the provided item to the provided output stream."""

    if unique_id is None:
        unique_id = (id(item), type(item))

    if unique_id in _describe_stack:
        # Display this value in a way that is similar to what is done inline so that normalization
        # functions normalize this value too.
        output_stream.write("The item '<<<id>>> : {} {}' has already been described.\n".format(id(item), type(item)))
        return

    _describe_stack.add(unique_id)

    try:
        # ----------------------------------------------------------------------
        def OutputDict(item, indentation_str, recurse_ctr):
            if not item:
                output_stream.write("-- empty dict --\n")
                return

            if not recurse and recurse_ctr != 0:
                output_stream.write("-- dict with {} item(s) --\n".format(len(item)))
                return

            if hasattr(item, "_asdict"):
                item = item._asdict()

            keys = OrderedDict(
                [
                    (key, key if isinstance(key, six.string_types) else str(key))
                    for key in item.keys()
                ],
            )

            max_length = 0
            for key in six.itervalues(keys):
                max_length = max(max_length, len(key))

            item_indentation_str = indentation_str + (" " * (max_length + len(" : ")))

            for index, (key, key_name) in enumerate(six.iteritems(keys)):
                output_stream.write(
                    "{0}{1:<{2}} : ".format(
                        indentation_str if index else "",
                        key_name,
                        max_length,
                    ),
                )

                if key in custom_display_funcs:
                    result = custom_display_funcs[key](item[key])

                    if result is not None:
                        output_stream.write("{}".format(result))

                    output_stream.write("\n")

                else:
                    DisplayImpl(item[key], item_indentation_str, recurse_ctr + 1)

        # ----------------------------------------------------------------------
        def OutputList(item, indentation_str, recurse_ctr):
            if not item:
                output_stream.write("-- empty list --\n")
                return

            if not recurse and recurse_ctr != 0:
                output_stream.write("-- list with {} item(s) --\n".format(len(item)))
                return

            item_indentation_str = indentation_str + (" " * 5)

            for index, i in enumerate(item):
                output_stream.write(
                    "{0}{1:<5}".format(
                        indentation_str if index else "",
                        "{})".format(index),
                    ),
                )

                DisplayImpl(i, item_indentation_str, recurse_ctr + 1)

        # ----------------------------------------------------------------------
        def TryDisplay(item, indentation_str, recurse_ctr):
            try:
                # Is the item iterable?
                potential_attribute_name = next(iter(item))
            except (TypeError, IndexError, StopIteration):
                # Not iterable
                return False

            try:
                # Is the item dict-like?
                ignore_me = item[potential_attribute_name]
                OutputDict(item, indentation_str, recurse_ctr)
            except (TypeError, IndexError):
                # Not dict-like
                OutputList(item, indentation_str, recurse_ctr)

            return True

        # ----------------------------------------------------------------------
        def DisplayImpl(item, indentation_str, recurse_ctr):
            if isinstance(item, six.string_types):
                output_stream.write(
                    "{}\n".format(
                        "{}\n".format(indentation_str).join(item.split("\n")),
                    ),
                )
            elif isinstance(item, dict):
                OutputDict(item, indentation_str, recurse_ctr)
            elif isinstance(item, list):
                OutputList(item, indentation_str, recurse_ctr)
            elif not TryDisplay(item, indentation_str, recurse_ctr):
                if (
                    not recurse
                    and recurse_ctr != 0
                    and not isinstance(
                        item,
                        (
                            bool,
                            complex,
                            float,
                            int,
                            six.string_types,
                        ),
                    )
                ):
                    output_stream.write("-- recursion is disabled --\n")
                    return

                content = str(item).strip()

                if include_class_info and "<class" not in content:
                    content += "{}{}".format(
                        "\n" if content.count("\n") > 1 else " ",
                        type(item),
                    )

                if " object at " in content:
                    if not include_id:
                        content = str(type(item)).strip()

                    content += "\n\n{}".format(
                        ObjectReprImpl(
                            item,
                            include_class_info=include_class_info,
                            include_id=include_id,
                            include_methods=include_methods,
                            include_private=include_private,
                            recurse=recurse or recurse_ctr == 0,
                            **custom_display_funcs
                        ),
                    )

                output_stream.write(
                    "{}\n".format(
                        "\n{}".format(indentation_str).join(content.split("\n")),
                    ),
                )

        # ----------------------------------------------------------------------

        DisplayImpl(item, "", 0)
        output_stream.write("\n\n")

    finally:
        _describe_stack.remove(unique_id)


# ----------------------------------------------------------------------
def ObjectReprImpl(
    obj,
    include_class_info=True,
    include_id=True,
    include_methods=False,
    include_private=False,
    scrub_results=False,
    recurse=True,
    **custom_display_funcs # Callable[[Any], Optional[str]]
):
    """\
    Implementation of an object's __repr__ method.

    Example:
        def __repr__(self):
            return CommonEnvironment.ObjectReprImpl(self)
    """

    # Convert the object into a dictionary that we can pass to Describe.
    d = OrderedDict()

    if include_id:
        d["<<<id>>>"] = id(obj)

    for key in dir(obj):
        if key.startswith("__"):
            continue

        if key.startswith("_") and not include_private:
            continue

        value = getattr(obj, key)

        if callable(value):
            if include_methods:
                value = "callable"
            else:
                continue

        d[key] = value

    # Describe the object
    sink = six.moves.StringIO()

    Describe(
        d,
        sink,
        unique_id=(type(obj), id(obj)),
        include_class_info=include_class_info,
        include_id=include_id,
        include_methods=include_methods,
        include_private=include_private,
        recurse=recurse,
        **custom_display_funcs
    )

    result = "{}\n".format(sink.getvalue().rstrip())

    if include_class_info:
        result = "{}\n{}".format(type(obj), result)

    if scrub_results:
        result = NormalizeObjectReprOutput(result)

    return result


# ----------------------------------------------------------------------
def NormalizeObjectReprOutput(output):
    """\
    Remove id specific information from the __repr__ output of an object so
    that it can be compared with another object.
    """

    # ----------------------------------------------------------------------
    def Sub(match):
        return "{} : __scrubbed_id__ {}".format(
            match.group("prefix"),
            match.group("suffix"),
        )

    # ----------------------------------------------------------------------

    return re.sub(
        r"(?P<prefix>\<\<\<id\>\>\>\s*?) : (?P<id>\d+) (?P<suffix>[^\n]*?)",
        Sub,
        output,
    )
