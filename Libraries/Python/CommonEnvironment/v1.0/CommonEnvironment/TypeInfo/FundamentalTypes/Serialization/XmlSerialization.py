# ----------------------------------------------------------------------
# |
# |  XmlSerialization.py
# |
# |  David Brownell <db@DavidBrownell.com>
# |      2019-02-23 16:53:57
# |
# ----------------------------------------------------------------------
# |
# |  Copyright David Brownell 2019
# |  Distributed under the Boost Software License, Version 1.0. See
# |  accompanying file LICENSE_1_0.txt or copy at
# |  http://www.boost.org/LICENSE_1_0.txt.
# |
# ----------------------------------------------------------------------
"""Contains the XmlSerialization type"""

import os

import six

import CommonEnvironment
from CommonEnvironment.TypeInfo.FundamentalTypes.All import BoolTypeInfo, DateTimeTypeInfo, DurationTypeInfo

from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization.StringSerialization import StringSerialization

# ----------------------------------------------------------------------
_script_fullpath                            = CommonEnvironment.ThisFullpath()
_script_dir, _script_name                   = os.path.split(_script_fullpath)
#  ----------------------------------------------------------------------

# ----------------------------------------------------------------------
class XmlSerialization(StringSerialization):
    """Serialization of XML types."""

    # ----------------------------------------------------------------------
    @classmethod
    def _SerializeItemImpl(cls, type_info, item, **custom_kwargs):
        if isinstance(type_info, DateTimeTypeInfo):
            custom_kwargs["sep"] = "T"
            custom_kwargs["regex_index"] = 0
        elif isinstance(type_info, DurationTypeInfo):
            custom_kwargs["regex_index"] = 1

        result = super(XmlSerialization, cls)._SerializeItemImpl(type_info, item, **custom_kwargs)

        if isinstance(type_info, BoolTypeInfo):
            result = result.lower()

        return result
