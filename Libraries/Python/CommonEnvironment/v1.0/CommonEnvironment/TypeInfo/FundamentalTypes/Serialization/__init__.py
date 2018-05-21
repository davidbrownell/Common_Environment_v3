# ----------------------------------------------------------------------
# |  
# |  __init__.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-24 21:35:07
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Serialization object."""

import os
import sys

from CommonEnvironment.Interface import Interface, abstractmethod

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class Serialization(Interface):

    # ----------------------------------------------------------------------
    @classmethod
    def SerializeItems(cls, type_info, item_or_items, **custom_args):
        """Serializes one or items."""

        type_info.ValidateArity(item_or_items)

        if type_info.Arity.IsOptional and item_or_items is None:
            return None
        elif type_info.Arity.IsCollection:
            return [ cls.SerializeItem(type_info, item, **custom_args) for item in item_or_items ]

        return cls.SerializeItem(type_info, item_or_items, **custom_args)

    # ----------------------------------------------------------------------
    @classmethod
    def DeserializeItems(cls, type_info, item_or_items, **custom_args):
        """Deserializes one or more items."""

        type_info.ValidateArity(item_or_items)

        if type_info.Arity.IsOptional and item_or_items is None:
            return None
        elif type_info.Arity.IsCollection:
            return [ cls.DeserializeItems(type_info, item, **custom_args) for item in item_or_items ]

        return cls.DeserializeItem(type_info, item_or_items, **custom_args)

    # ----------------------------------------------------------------------
    @classmethod
    def SerializeItem(cls, type_info, item, **custom_args):
        """Serializes an individual item."""
        type_info.ValidateItem(item)
        return cls._SerializeItemImpl(type_info, item, **custom_args)

    # ----------------------------------------------------------------------
    @classmethod
    def DeserializeItem(cls, type_info, item, **custom_args):
        """Deserializes an individual item."""
        item = cls._DeserializeItemImpl(type_info, item, **custom_args)

        type_info.ValidateItem(item)
        return item

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _SerializeItemImpl(type_info, item):
        raise Exception("Abstract method")

    # ----------------------------------------------------------------------
    @staticmethod
    @abstractmethod
    def _DeserializeItemImpl(type_info, item):
        raise Exception("Abstract method")
