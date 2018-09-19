# ----------------------------------------------------------------------
# |  
# |  UriTypeInfo.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-23 12:19:59
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the Uri and UriTypeInfo objects."""

import os
import sys

import six

import CommonEnvironment
from CommonEnvironment.Interface import staticderived, override, DerivedProperty
from CommonEnvironment.TypeInfo import TypeInfo

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

class Uri(object):
    """Contains components of a uri"""

    # ----------------------------------------------------------------------
    @classmethod
    def FromString(cls, value):
        """Creates a Uri object from a string."""

        result = six.moves.urllib.parse.urlparse(value)

        if not (result.scheme and result.hostname):
            raise Exception("'{}' is not a valid uri".format(value))

        return cls( result.scheme,
                    result.netloc if result.scheme == "file" else result.hostname,
                    six.moves.urllib.parse.unquote(result.path or ''),
                    result.query,
                    credentials=None if not (result.username and result.password) else ( six.moves.urllib.parse.unquote(result.username or ''),
                                                                                         six.moves.urllib.parse.unquote(result.password or ''),
                                                                                       ),
                    port=result.port,
                  )

    # ----------------------------------------------------------------------
    def __init__( self,
                  scheme,
                  host,
                  path,
                  query=None,               # string or dict
                  credentials=None,         # (username, password)
                  port=None,
                ):
        if not scheme:                      raise Exception("'scheme' must be valid")
        if not host:                        raise Exception("'host' must be valid")

        self.Scheme                         = scheme
        self.Host                           = host
        self.Path                           = path or None
        self.Query                          = six.moves.urllib.parse.parse_qs(query) if isinstance(query, six.string_types) else (query or {})
        self.Credentials                    = credentials
        self.Port                           = port

    # ----------------------------------------------------------------------
    def __repr__(self):
        return CommonEnvironment.ObjectReprImpl(self)

    # ----------------------------------------------------------------------
    def ToString(self):
        host = []

        if self.Credentials:
            username, password = self.Credentials

            if username:
                host.append(six.moves.urllib.parse.quote(username))
            if password:
                host.append(":{}".format(six.moves.urllib.parse.quote(password)))

            host.append("@")

        host.append(self.Host)

        if self.Port:
            host.append(":{}".format(self.Port))

        query = ''
        if self.Query:
            query = six.moves.urllib.parse.urlencode(self.Query, True)

        return six.moves.urllib.parse.urlunparse(( self.Scheme,
                                                   ''.join(host),
                                                   self.Path or '',
                                                   '',
                                                   query,
                                                   '',
                                                 ))

    # ----------------------------------------------------------------------
    def ToFilename(self):
        if self.Scheme != "file":
            raise Exception("This method is only valid when the scheme is 'file'")

        filename = self.ToString()

        assert filename.startswith("file://"), filename
        filename = filename[len("file://"):]

        filename = filename.replace('/', os.path.sep)

        return filename

    # ----------------------------------------------------------------------
    def __eq__(self, other):
        return self.__dict__ == other.__dict__

# ----------------------------------------------------------------------
@staticderived
class UriTypeInfo(TypeInfo):
    """Type information for an uri value."""

    Uri                                     = Uri

    Desc                                    = DerivedProperty("Uri")
    ConstraintsDesc                         = DerivedProperty('')
    ExpectedType                            = Uri

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _ValidateItemNoThrowImpl(item):
        return
