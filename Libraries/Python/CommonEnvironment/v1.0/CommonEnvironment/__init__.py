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
import textwrap

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
def Describe(
    item,
    output_stream=sys.stdout,
    unique_id=None,
    include_class_info=True,
    include_id=True,
    include_methods=False,
    include_private=False,
    max_recursion_depth=None,
    describe_stack=None,
    **custom_display_funcs # Callable[[Any], Optional[str]]
):
    """Writes formatted information about the provided item to the provided output stream."""

    if unique_id is None:
        unique_id = (id(item), type(item))
    if max_recursion_depth is None:
        max_recursion_depth = sys.maxsize
    if describe_stack is None:
        describe_stack = set()

    if unique_id in describe_stack:
        # Display this value in a way that is similar to what is done inline so that normalization
        # functions normalize this value too.
        output_stream.write("The item '<<<id>>> : {} {}' has already been described.\n".format(id(item), type(item)))
        return

    describe_stack.add(unique_id)

    try:
        # ----------------------------------------------------------------------
        def OutputDict(item, indentation_str, max_recursion_depth):
            if not item:
                output_stream.write("-- empty dict --\n")
                return

            if max_recursion_depth == 0:
                output_stream.write("-- recursion is disabled: dict with {} item(s) --\n".format(len(item)))
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
                result = None

                if key in custom_display_funcs:
                    func = custom_display_funcs[key]
                    if func is None:
                        continue

                    result = func(item[key])
                    if result is None:
                        continue

                    result = "{}\n".format(result)

                output_stream.write(
                    "{0}{1:<{2}} : ".format(
                        indentation_str if index else "",
                        key_name,
                        max_length,
                    ),
                )

                if result:
                    output_stream.write(result)
                else:
                    DisplayImpl(item[key], item_indentation_str, max_recursion_depth - 1)

        # ----------------------------------------------------------------------
        def OutputList(item, indentation_str, max_recursion_depth):
            if not item:
                output_stream.write("-- empty list --\n")
                return

            if max_recursion_depth == 0:
                output_stream.write("-- recursion is disabled: list with {} item(s) --\n".format(len(item)))
                return

            item_indentation_str = indentation_str + (" " * 5)

            for index, i in enumerate(item):
                output_stream.write(
                    "{0}{1:<5}".format(
                        indentation_str if index else "",
                        "{})".format(index),
                    ),
                )

                DisplayImpl(i, item_indentation_str, max_recursion_depth - 1)

        # ----------------------------------------------------------------------
        def TryDisplayCollection(item, indentation_str, max_recursion_depth):
            try:
                # Is the item iterable?
                potential_attribute_name = next(iter(item))
            except (TypeError, IndexError, StopIteration):
                # Not iterable
                return False

            try:
                # Is the item dict-like?
                ignore_me = item[potential_attribute_name]
                OutputDict(item, indentation_str, max_recursion_depth)
            except (TypeError, IndexError):
                # Not dict-like
                OutputList(item, indentation_str, max_recursion_depth)

            return True

        # ----------------------------------------------------------------------
        def TryGetCustomContent(item, indentation_str, max_recursion_depth):
            # Attempt to lever common display methods
            for potential_display_method_name in ["ToString", "to_string"]:
                potential_func = getattr(item, potential_display_method_name, None)
                if potential_func is None:
                    continue

                for potential_args in [
                    {
                        "include_class_info" : include_class_info,
                        "include_id" : include_id,
                        "include_methods" : include_methods,
                        "include_private" : include_private,
                        "max_recursion_depth" : max_recursion_depth,
                        "describe_stack" : describe_stack,
                    },
                    {
                        "max_recursion_depth" : max_recursion_depth,
                        "describe_stack" : describe_stack,
                    },
                    {},
                ]:
                    try:
                        potential_result = potential_func(**potential_args)
                        if potential_result is not None:
                            return potential_result

                    except TypeError:
                        pass

            return None

        # ----------------------------------------------------------------------
        def DisplayImpl(item, indentation_str, max_recursion_depth):
            if isinstance(item, six.string_types):
                output_stream.write(
                    "{}\n".format(
                        "{}\n".format(indentation_str).join(item.split("\n")),
                    ),
                )
            elif isinstance(item, dict):
                OutputDict(item, indentation_str, max_recursion_depth)
            elif isinstance(item, list):
                OutputList(item, indentation_str, max_recursion_depth)
            elif not TryDisplayCollection(item, indentation_str, max_recursion_depth):
                is_primitive_type = isinstance(item, (bool, complex, float, int, six.string_types))

                if max_recursion_depth == 0 and not is_primitive_type:
                    output_stream.write("-- recursion is disabled: complex element --\n")
                    return

                content = TryGetCustomContent(item, indentation_str, max_recursion_depth)
                if content is None:
                    content = str(item)

                content = content.strip()

                if "<class" not in content:
                    if include_class_info:
                        if content.count("\n") > 1:
                            content = "{}\n{}".format(type(item), content)
                        else:
                            content += " {}".format(type(item))

                output_stream.write(
                    "{}\n".format(
                        "\n{}".format(indentation_str).join(content.split("\n")),
                    ),
                )

        # ----------------------------------------------------------------------

        DisplayImpl(item, "", max_recursion_depth)
        output_stream.write("\n\n")

    finally:
        describe_stack.remove(unique_id)


# ----------------------------------------------------------------------
# This function should not be used directly and remains here for legacy support.
# New code should prefer to base their class on ObjectReplImplBase.
def ObjectReprImpl(
    obj,
    include_class_info=True,
    include_id=True,
    include_methods=False,
    include_private=False,
    scrub_results=False,
    max_recursion_depth=None, # Optional[int]
    describe_stack=None,
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
        max_recursion_depth=max_recursion_depth,
        describe_stack=describe_stack,
        **custom_display_funcs
    )

    # Custom types must always display the type
    result = textwrap.dedent(
        """\
        {}
        {}
        """,
    ).format(
        type(obj),
        sink.getvalue().rstrip(),
    )

    if scrub_results:
        result = NormalizeObjectReprOutput(result)

    return result


# ----------------------------------------------------------------------
class ObjectReplImplBase(object):
    """\
    Implements __repr__ and ToString functionality for the parent class and its
    entire class hierarchy.

    Example:
        class MyObject(CommandLine.ObjectReplImplBase):
            pass

        print(str(MyObject()))
    """

    # ----------------------------------------------------------------------
    def __init__(
        self,
        include_class_info=True,
        include_id=False,
        include_methods=False,
        include_private=False,
        max_recursion_depth=None,
        **custom_display_funcs
    ):
        d = {
            "include_class_info" : include_class_info,
            "include_id" : include_id,
            "include_methods" : include_methods,
            "include_private" : include_private,
        }

        for k, v in six.iteritems(custom_display_funcs):
            assert k not in d, k
            d[k] = v

        self._object_repr_impl_args         = d
        self._max_recursion_depth           = max_recursion_depth

    # ----------------------------------------------------------------------
    def __repr__(self):
        return self.ToString(
            max_recursion_depth=self._max_recursion_depth,
        )

        # There is something special about __repr__ in that it cannot
        # forward directly to ToString. Therefore, we have to make what
        # is basically the same call to ObjectReprImpl in both __repr__
        # and ToString.
        self._AutoInit()

        return ObjectReprImpl(
            self,
            max_recursion_depth=self._max_recursion_depth,
            **self._object_repr_impl_args
        )

    # ----------------------------------------------------------------------
    def ToString(
        self,
        max_recursion_depth=None, # Optional[int]
        describe_stack=None,
    ):
        self._AutoInit()

        if max_recursion_depth is None:
            max_recursion_depth = self._max_recursion_depth
        elif self._max_recursion_depth is not None:
            max_recursion_depth = min(max_recursion_depth, self._max_recursion_depth)

        return ObjectReprImpl(
            self,
            describe_stack=describe_stack,
            max_recursion_depth=max_recursion_depth,
            **self._object_repr_impl_args
        )

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _AutoInit(self):
        if not hasattr(self, "_object_repr_impl_args"):
            ObjectReplImplBase.__init__(self)


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
