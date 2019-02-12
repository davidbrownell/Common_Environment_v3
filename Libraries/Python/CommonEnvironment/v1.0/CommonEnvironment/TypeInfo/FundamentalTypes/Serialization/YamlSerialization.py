# ----------------------------------------------------------------------
# |  
# |  YamlSerialization.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-11 20:32:06
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2019.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the YamlSerialization type"""

import os

import six

import CommonEnvironment
from CommonEnvironment.TypeInfo.FundamentalTypes.All import BoolTypeInfo, \
                                                            DateTypeInfo, \
                                                            DateTimeTypeInfo, \
                                                            DurationTypeInfo, \
                                                            FloatTypeInfo, \
                                                            IntTypeInfo, \
                                                            TimeTypeInfo

from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath = CommonEnvironment.ThisFullpath()
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class YamlSerialization(StringSerialization):
    """Serialization of YAML (or YAML-like) types."""

    NATIVE_TYPES                            = (
        BoolTypeInfo,
        DateTypeInfo,
        DateTimeTypeInfo,
        DurationTypeInfo,
        FloatTypeInfo,
        IntTypeInfo,
        TimeTypeInfo,
    )

    # ----------------------------------------------------------------------
    @classmethod
    def _SerializeItemImpl(cls, type_info, item, **custom_kwargs):
        # No need to convert those types that YAML supports natively
        if not isinstance(item, six.string_types) and isinstance(type_info, cls.NATIVE_TYPES):
            return item

        return super(YamlSerialization, cls)._SerializeItemImpl(type_info, item, **custom_kwargs)

    # ----------------------------------------------------------------------
    @classmethod
    def _DeserializeItemImpl(cls, type_info, item, **custom_kwargs):
        # No need to convert those types that YAML supports natively
        if not isinstance(item, six.string_types) and isinstance(type_info, cls.NATIVE_TYPES):
            return item

        return super(YamlSerialization, cls)._DeserializeItemImpl(type_info, item, **custom_kwargs)
