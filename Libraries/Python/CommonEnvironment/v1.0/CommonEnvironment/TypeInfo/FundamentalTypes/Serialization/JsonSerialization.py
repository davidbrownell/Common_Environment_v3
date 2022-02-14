# ----------------------------------------------------------------------
# |  
# |  JsonSerialization.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-28 21:56:06
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018-22.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the JsonSerialization type"""

import os

import six

import CommonEnvironment
from CommonEnvironment.TypeInfo.FundamentalTypes.All import BoolTypeInfo, \
                                                            FloatTypeInfo, \
                                                            IntTypeInfo

from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class JsonSerialization(StringSerialization):
    """Serialization of JSON (or JSON-like) types."""

    # ----------------------------------------------------------------------
    @classmethod
    def _SerializeItemImpl(cls, type_info, item, **custom_kwargs):
        # No need to convert those types that JSON supports natively
        if not isinstance(item, six.string_types) and isinstance(type_info, (BoolTypeInfo, FloatTypeInfo, IntTypeInfo)):
            return item

        return super(JsonSerialization, cls)._SerializeItemImpl(type_info, item, **custom_kwargs)

    # ----------------------------------------------------------------------
    @classmethod
    def _DeserializeItemImpl(cls, type_info, item, **custom_kwargs):
        # No need to convert those types that JSON supports natively
        if not isinstance(item, six.string_types) and isinstance(type_info, (BoolTypeInfo, FloatTypeInfo, IntTypeInfo)):
            return item

        return super(JsonSerialization, cls)._DeserializeItemImpl(type_info, item, **custom_kwargs)
