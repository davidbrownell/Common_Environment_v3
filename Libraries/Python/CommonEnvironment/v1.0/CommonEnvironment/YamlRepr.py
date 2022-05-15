# ----------------------------------------------------------------------
# |
# |  YamlRepr.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2021-08-25 19:20:03
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2021-22
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Functionality to output yaml content during for __repr__-style implementations"""

import io
import os
import re
import sys
import textwrap

from collections import OrderedDict
from typing import Any, Callable, Optional, Set, TextIO, Tuple

import six

import CommonEnvironment
from CommonEnvironment import StringHelpers

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------


# ----------------------------------------------------------------------
def Describe(
    item: Any,
    output_stream: TextIO=sys.stdout,
    *,
    include_class_info: Optional[bool]=None,            # False
    include_id: Optional[bool]=None,                    # False
    include_methods: Optional[bool]=None,               # False
    include_private: Optional[bool]=None,               # False
    indentation_level: Optional[int]=None,              # 2
    scrub_results: Optional[bool]=None,                 # False
    item_stack: Any=None,                               # <impl detail>
    max_recursion_depth: Optional[int]=None,            # sys.maxint
    unique_id__: Any=None,                              # <impl detail>
    **custom_display_funcs: Callable[[Any], Optional[Any]],
) -> None:
    """Writes formatted yaml about the provided item to the given output stream"""

    include_class_info_value = include_class_info if include_class_info is not None else False
    indentation_level_value = indentation_level if indentation_level is not None else 2
    max_recursion_depth_value = max_recursion_depth if max_recursion_depth is not None else sys.maxsize

    if item_stack is None:
        item_stack = set()
    if unique_id__ is None:
        unique_id__ = (type(item), id(item))

    if unique_id__ in item_stack:
        # Don't rely on yaml's reference functionality, as we are creating yaml-like content
        # for display purposes and not actual yaml.
        output_stream.write(
            '''"The item '<<<id>>> : {} {}' has already been described.\n"'''.format(
                id(item),
                type(item),
            ),
        )
        return

    item_stack.add(unique_id__)

    try:
        # ----------------------------------------------------------------------
        def IsPrimitiveType(
            item: Any,
        ) -> bool:
            return item is None or isinstance(item, (bool, complex, float, int, six.string_types))

        # ----------------------------------------------------------------------
        def OutputDict(
            item: Any,
            indentation: int,
            max_recursion_depth: int,
        ) -> None:
            if not item:
                output_stream.write("{}\n")
                return

            if max_recursion_depth == 0:
                output_stream.write(
                    '"-- recursion is disabled: dict with {} item(s) --"\n'.format(
                        len(item),
                    ),
                )
                return

            if hasattr(item, "_asdict"):
                item = item._asdict()

            output_stream.write("\n")

            indentation_str = " " * indentation

            for key, value in item.items():
                if not isinstance(key, six.string_types):
                    key = str(key)

                display_value = None

                if indentation == 0 and key in custom_display_funcs:
                    func = custom_display_funcs[key]
                    if func is None:
                        continue

                    display_value = func(value)
                    if display_value is None:
                        continue

                if display_value is None:
                    display_value = value

                output_stream.write("{}{}: ".format(indentation_str, key))
                DisplayImpl(display_value, indentation + indentation_level_value, max_recursion_depth - 1)

        # ----------------------------------------------------------------------
        def OutputIterable(
            item: Any,
            indentation: int,
            max_recursion_depth: int,
            type_name: str,
        ) -> None:
            if not item:
                output_stream.write("[]\n")
                return

            if max_recursion_depth == 0:
                output_stream.write(
                    '"-- recursion is disabled: {} with {} item(s) --"\n'.format(
                        type_name,
                        len(item),
                    ),
                )
                return

            output_stream.write("\n")

            indentation_str = " " * indentation

            for i in item:
                output_stream.write("{}- ".format(indentation_str))
                DisplayImpl(i, indentation + 2, max_recursion_depth - 1)

        # ----------------------------------------------------------------------
        def TryDisplayAsCollection(
            item: Any,
            indentation: int,
            max_recursion_depth: int,
        ) -> bool:
            try:
                # Is the item iterable
                potential_attribute_name = next(iter(item))
            except (TypeError, IndexError, StopIteration):
                # Not iterable
                return False

            try:
                if not isinstance(item, tuple):
                    # Is the item dict-like
                    ignore_me = item[potential_attribute_name]
                    OutputDict(item, indentation, max_recursion_depth)

                    return True

            except (TypeError, IndexError):
                # Not dict-like
                pass

            OutputIterable(
                item,
                indentation,
                max_recursion_depth,
                "tuple" if isinstance(item, tuple) else "list",
            )

            return True

        # ----------------------------------------------------------------------
        def GetCustomContent(
            item: Any,
            max_recursion_depth: int,
        ) -> Tuple[str, bool]:
            # Attempt to leverage common display methods
            for potential_display_method_name, is_yaml in [
                ("ToYamlString", True),
                ("to_yaml_string", True),
                ("ToString", False),
                ("to_string", False),
            ]:
                potential_func = getattr(item, potential_display_method_name, None)
                if potential_func is None:
                    continue

                for potential_args in [
                    {
                        "include_class_info" : include_class_info,
                        "include_id" : include_id,
                        "include_methods" : include_methods,
                        "include_private" : include_private,
                        "indentation_level" : indentation_level,
                        "scrub_results" : scrub_results,
                        "item_stack" : item_stack,
                        "max_recursion_depth" : max_recursion_depth,
                    },
                    {},
                ]:
                    try:
                        potential_result = potential_func(**potential_args)
                        if potential_result is not None:
                            return (potential_result, is_yaml)

                    except TypeError:
                        pass

            return (str(item), False)

        # ----------------------------------------------------------------------
        def DisplayImpl(
            item: Any,
            indentation: int,
            max_recursion_depth: int,
        ) -> None:
            if isinstance(item, six.string_types):
                item = item.replace("\\", "\\\\")

                if any(c == "\n" for c in item):
                    output_stream.write(
                        "|-\n{}\n".format(
                            StringHelpers.LeftJustify(
                                item,
                                indentation,
                                skip_first_line=False,
                            ),
                        ),
                    )
                else:
                    output_stream.write('"{}"\n'.format(item.replace('"', '\\"')))

            elif isinstance(item, dict):
                OutputDict(item, indentation, max_recursion_depth)

            elif isinstance(item, (list, tuple)):
                OutputIterable(
                    item,
                    indentation,
                    max_recursion_depth,
                    type_name="tuple" if isinstance(item, tuple) else "list",
                )

            else:
                if TryDisplayAsCollection(item, indentation, max_recursion_depth):
                    return

                is_primitive_type = IsPrimitiveType(item)

                if max_recursion_depth == 0 and not is_primitive_type:
                    output_stream.write(
                        '''"-- recursion is disabled: complex element '{}' --"\n'''.format(
                            type(item),
                        ),
                    )
                    return

                if is_primitive_type:
                    # Convert some python types into yaml friendly types
                    value = None

                    if not include_class_info:
                        if item is None:
                            value = "null"
                        elif item is True:
                            value = "true"
                        elif item is False:
                            value = "false"

                    if value is None:
                        value = str(item)

                    content = "{}\n".format(value)
                    is_yaml = True
                else:
                    content, is_yaml = GetCustomContent(item, max_recursion_depth)

                if include_class_info_value and "<class" not in content:
                    content = content.rstrip()

                    if content.count("\n") > 1:
                        content = "# {}\n{}\n".format(type(item), content)
                    else:
                        content = "{} # {}\n".format(content, type(item))

                if is_yaml:
                    if not content.endswith("\n"):
                        content += "\n"

                    output_stream.write(StringHelpers.LeftJustify(content, indentation))
                else:
                    DisplayImpl(content, indentation, max_recursion_depth)

        # ----------------------------------------------------------------------

        DisplayImpl(item, 0, max_recursion_depth_value)
        output_stream.write("\n\n")

    finally:
        item_stack.remove(unique_id__)


# ----------------------------------------------------------------------
class ObjectReprImplBase(object):
    """\
    Implements __repr__ and DisplayAsYaml functionality for the parent class
    and its entire class hierarchy.

    Example:
        class MyObject(CommonEnvironment.ObjectReprImplBase):
            pass

        print(str(MyObject()))
    """

    # ----------------------------------------------------------------------
    def __init__(
        self,
        *,
        # In May 2022, I found a bug where we weren't respecting 'include_class_info' for root-level
        # objects. However, a lot of code dependens on this behavior, so I am introducing a new flag
        # to control this specific scenario and maintaining backwards compatibility. If writing this
        # code from scratch, this flag would not exist and everything would work according to
        # 'include_class_info'.
        include_root_class_info: bool=True,
        include_class_info: Optional[bool]=None,        # See `Describe` for default value
        include_id: Optional[bool]=None,                # See `Describe` for default value
        include_methods: Optional[bool]=None,           # See `Describe` for default value
        include_private: Optional[bool]=None,           # See `Describe` for default value
        indentation_level: Optional[int]=None,          # See `Describe` for default value
        scrub_results: Optional[bool]=None,             # See `Describe` for default value
        max_recursion_depth: Optional[int]=None,        # See `Describe` for default value
        **custom_display_funcs: Optional[Callable[[Any], Optional[Any]]],
    ):
        d = {
            "include_root_class_info": include_root_class_info,
            "include_class_info" : include_class_info,
            "include_id" : include_id,
            "include_methods" : include_methods,
            "include_private" : include_private,
            "indentation_level" : indentation_level,
            "scrub_results" : scrub_results,
        }

        # Note that this code may be invoked from a frozen dataclass, so we
        # need to take special create when assigning attributes.
        object.__setattr__(self, "__object_repr_impl_args", d)
        object.__setattr__(self, "__max_recursion_depth", max_recursion_depth)
        object.__setattr__(self, "__custom_display_funcs", custom_display_funcs)

    # ----------------------------------------------------------------------
    def __repr__(self):
        self._AutoInit()

        return self.ToYamlString(
            max_recursion_depth=getattr(self, "__max_recursion_depth"),
        )

    # ----------------------------------------------------------------------
    def ToYamlString(
        self,
        *,
        include_root_class_info: Optional[bool]=None,
        include_class_info: Optional[bool]=None,        # See `Describe` for default value
        include_id: Optional[bool]=None,                # See `Describe` for default value
        include_methods: Optional[bool]=None,           # See `Describe` for default value
        include_private: Optional[bool]=None,           # See `Describe` for default value
        indentation_level: Optional[int]=None,          # See `Describe` for default value
        scrub_results: Optional[bool]=None,             # See `Describe` for default value
        item_stack: Optional[Set[int]]=None,            # See `Describe` for default value
        max_recursion_depth: Optional[int]=None,        # See `Describe` for default value
    ) -> str:
        self._AutoInit()

        args = getattr(self, "__object_repr_impl_args")

        if include_root_class_info is None:
            include_root_class_info = args["include_root_class_info"]
        if include_class_info is None:
            include_class_info = args["include_class_info"]
        if include_id is None:
            include_id = args["include_id"]
        if include_methods is None:
            include_methods = args["include_methods"]
        if include_private is None:
            include_private = args["include_private"]
        if indentation_level is None:
            indentation_level = args["indentation_level"]
        if scrub_results is None:
            scrub_results = args["scrub_results"]
        if max_recursion_depth is None:
            max_recursion_depth = getattr(self, "__max_recursion_depth")

        # Convert the object into a dictionary that we can pass to Describe
        d = OrderedDict()

        if include_id:
            d["<<<id>>>"] = id(self)

        for key in dir(self):
            if key.startswith("__"):
                continue

            if key.startswith("_") and not include_private:
                continue

            try:
                value = getattr(self, key)
            except Exception as ex:
                value = str(ex)

            if callable(value):
                if include_methods:
                    value = "callable"
                else:
                    continue

            d[key] = value

        sink = io.StringIO()

        Describe(
            d,
            sink,
            include_class_info=include_class_info,
            include_id=include_id,
            include_methods=include_methods,
            include_private=include_private,
            indentation_level=indentation_level,
            scrub_results=scrub_results,
            item_stack=item_stack,
            max_recursion_depth=max_recursion_depth,
            unique_id__=(type(self), id(self)),
            **getattr(self, "__custom_display_funcs"),
        )

        # Strip trailing whitespace
        result = sink.getvalue().rstrip()
        result = "\n".join([line.rstrip() for line in result.split("\n")])

        if result.startswith("\n"):
            result = result.lstrip()

        # Custom types must always display the type
        result = textwrap.dedent(
            """\
            {}{}
            """,
        ).format(
            "# {}\n".format(type(self)) if include_root_class_info else "",
            result,
        )

        if scrub_results:
            # ----------------------------------------------------------------------
            def Sub(match):
                return "{} : __scrubbed_id__ {}".format(
                    match.group("prefix"),
                    match.group("suffix"),
                )

            # ----------------------------------------------------------------------

            result = re.sub(
                r"(?P<prefix>\<\<\<id\>\>\>\s*?): (?P<id>\d+) (?P<suffix>[^\n]*?)",
                Sub,
                result,
            )

        return result

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    def _AutoInit(self):
        if not hasattr(self, "__object_repr_impl_args"):
            ObjectReprImplBase.__init__(self)
