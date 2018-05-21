# ----------------------------------------------------------------------
# |  
# |  All.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 10:05:42
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""All items from this module."""

import os
import sys

from CommonEnvironment.TypeInfo.FundamentalTypes.BoolTypeInfo import BoolTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.DateTimeTypeInfo import DateTimeTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.DateTypeInfo import DateTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.DirectoryTypeInfo import DirectoryTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.DurationTypeInfo import DurationTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.EnumTypeInfo import EnumTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.FilenameTypeInfo import FilenameTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.FloatTypeInfo import FloatTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.GuidTypeInfo import GuidTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.IntTypeInfo import IntTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.StringTypeInfo import StringTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.TimeTypeInfo import TimeTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.UriTypeInfo import Uri, UriTypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
ALL_FUNDAMENTAL_TYPES                       = [ BoolTypeInfo,
                                                DateTimeTypeInfo,
                                                DateTypeInfo,
                                                DirectoryTypeInfo,
                                                DurationTypeInfo,
                                                EnumTypeInfo,
                                                FilenameTypeInfo,
                                                FloatTypeInfo,
                                                GuidTypeInfo,
                                                IntTypeInfo,
                                                StringTypeInfo,
                                                TimeTypeInfo,
                                                UriTypeInfo,
                                              ]

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def CreateFromPythonType(typ, **kwargs):
    """
    Creates a TypeInfo object based on the provided type.

    Examples:
        CreateFromPythonType(int)
        CreateFromPythonType(string)
    """

    if sys.version_info[0] == 2:
        if typ in [ str, unicode, basestring, ]:        # <Undefined variable> pylint: disable = E0602
            return StringTypeInfo(**kwargs)
    else:
        if typ == str:
            return StringTypeInfo(**kwargs)

    for potential_type_info in [ BoolTypeInfo,
                                 DateTimeTypeInfo,
                                 DateTypeInfo,
                                 # Ambiguous: DirectoryTypeInfo
                                 DurationTypeInfo,
                                 # Abmiguous: EnumTypeInfo
                                 # Ambiguous: FilenameTypeInfo
                                 FloatTypeInfo,
                                 GuidTypeInfo,
                                 IntTypeInfo,
                                 # Defined above: StringTypeInfo
                                 TimeTypeInfo,
                                 UriTypeInfo,
                               ]:
        if potential_type_info.ExpectedType == typ:
            return potential_type_info(**kwargs)

    raise Exception("'{}' is not a recognized type".format(typ))
