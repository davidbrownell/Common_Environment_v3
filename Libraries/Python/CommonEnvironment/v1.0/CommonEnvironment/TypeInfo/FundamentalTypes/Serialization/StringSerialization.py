# ----------------------------------------------------------------------
# |  
# |  StringSerialization.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-04-24 21:43:02
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Contains the RegularExpressionVisitor and StringSerialization objects."""

import datetime
import math
import os
import re
import sys
import textwrap
import uuid

import six

from CommonEnvironment import FileSystem
from CommonEnvironment.Interface import staticderived, override
from CommonEnvironment import RegularExpression

from CommonEnvironment.TypeInfo import ValidationException
from CommonEnvironment.TypeInfo.FundamentalTypes.DateTypeInfo import DateTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.FloatTypeInfo import FloatTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.TimeTypeInfo import TimeTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.UriTypeInfo import UriTypeInfo
from CommonEnvironment.TypeInfo.FundamentalTypes.Visitor import Visitor

from CommonEnvironment.TypeInfo.FundamentalTypes.Serialization import Serialization

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Parameters differ from overridden '<...>' method> pylint: disable = W0221
# <Unused argument> pylint: disable = W0613

# ----------------------------------------------------------------------
@staticderived
class RegularExpressionVisitor(Visitor):
    """Returns an array of regular expression strings able to process a string of the corresponding type."""

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnBool(type_info):
        return [ ( r"(true|t|yes|y|1|false|f|no|n|0)", re.IGNORECASE ),
               ]

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnDateTime(cls, type_info):
        float_regex_string = cls.OnFloat(FloatTypeInfo(min=0))[0]

        return [ textwrap.dedent(
                    # <Wrong hanging indentation> pylint: disable = C0330
                   r"""(?#
                    Date                        ){date}(?#
                    Sep                         )[ T](?#
                    Time                        ){time}(?#
                    Timzone [optional] <begin>  )(?:(?#
                      Header or...              )(?P<tz_utc>Z)|(?#
                      Offset <begin>            )(?:(?#
                        Sign                    )(?P<tz_sign>[\+\-])(?#
                        Hour                    )(?P<tz_hour>\d{{2}})(?#
                        Sep [optional]          ):?(?#
                        Minute                  )(?P<tz_minute>[0-5][0-9])(?#
                      Offset <end>              ))(?#
                    Timezone [optional] <end>   ))?(?#
                    )""").format( date=cls.OnDate(DateTypeInfo())[0],
                                  time=cls.OnTime(TimeTypeInfo())[0],
                                ),

                # Enhanced Unix timestamp: "@<stamp> <timezone>"
                textwrap.dedent(
                   r"""(?#
                    At                          )@(?#
                    Timestamp                   )(?P<stamp>{})(?#
                    Timezone [optional] <begin> )(?:(?#
                      Space                     ) (?#
                      Offset <begin>            )(?:(?#
                        Sign                    )(?P<tz_sign>[\+\-])?(?#
                        Hour                    )(?P<tz_hour>\d{{2}})(?#
                        Sep [optional]          ):?(?#
                        Minute                  )(?P<tz_minute>[0-5][0-9])(?#
                      Offset <end>              ))(?#
                    Timezone [optional] <end>   ))?(?#
                    )""").format(float_regex_string),

                # Unix Timestamp
                float_regex_string,
              ]

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDate(type_info):
        sep = r"[-/\.]"

        # <Wrong hanging indentation> pylint: disable = C0330
        return [ expr % { "sep" : sep,
                          "suffix" : index,
                        }
                 for index, expr in enumerate([ # YYYY-MM-DD
                                                r"(?P<year%(suffix)s>[0-9]{4})%(sep)s(?P<month%(suffix)s>0?[1-9]|1[0-2])%(sep)s(?P<day%(suffix)s>[0-2][0-9]|3[0-1])",
                                                
                                                # MM-DD-YYYY
                                                r"(?P<month%(suffix)s>0?[1-9]|1[0-2])%(sep)s(?P<day%(suffix)s>[0-2][0-9]|3[0-1])%(sep)s(?P<year%(suffix)s>[0-9]{4})",

                                                # YY-MM-DD
                                                r"(?P<year%(suffix)s>\d{2})%(sep)s(?P<month%(suffix)s>0?[1-9]|1[0-2])%(sep)s(?P<day%(suffix)s>[0-2][0-9]|3[0-1])",

                                                # MM-DD-YY
                                                r"(?P<month%(suffix)s>0?[1-9]|1[0-2])%(sep)s(?P<day%(suffix)s>[0-2][0-9]|3[0-1])%(sep)s(?P<year%(suffix)s>\d{2})",
                                              ])
               ]

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDirectory(type_info):
        return [ r".+",
               ]

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDuration(type_info):
        return [ textwrap.dedent(
                    # <Wrong hanging indentation> pylint: disable = C0330
                   r"""(?#
                    Days [optional]         )(?:(?P<days>\d+)[\.:])?(?#
                    Hours                   )(?P<hours>2[0-3]|[0-1][0-9]|[0-9]):(?#
                    Minutes                 )(?P<minutes>[0-5][0-9]):(?#
                    Seconds                 )(?P<seconds>[0-5][0-9])(?#
                    Microseconds [optional] )(?:\.(?P<microseconds>\d+))?(?#
                    )"""),
               ]

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnEnum(type_info):
        return [ "({})".format('|'.join([ re.escape(value) for value in type_info.Values ])),
               ]

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnFilename(type_info):
        return [ r".+",
               ]

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnFloat(cls, type_info):
        return [ r"{}(?:\.\d+)?".format(cls.OnInt(type_info)[0]),
               ]

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnGuid(type_info):
        d = { "char" : r"[0-9A-Fa-f]", }

        concise = "%(char)s{32}" % d
        verbose = "%(char)s{8}-%(char)s{4}-%(char)s{4}-%(char)s{4}-%(char)s{12}" % d

        return [ r"\{%s\}" % verbose,
                 verbose,
                 r"\{%s\}" % concise,
                 concise,
               ]

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnInt(type_info):
        patterns = []

        if type_info.Min is None or type_info.Min < 0:
            patterns.append('-')

            if type_info.Max is None or type_info.Max > 0:
                patterns.append('?')

        patterns.append(r"\d")

        if type_info.Min is None or type_info.Max is None:
            patterns.append('+')
        else:
            value = 10

            while True:
                if ( (type_info.Min is None or type_info.Min > -value) and 
                     (type_info.Max is None or type_info.Max < value)
                   ):
                    break

                value *= 10

            if value != 10:
                patterns.append("{{1,{}}}".format(int(math.log10(value))))

        return [ ''.join(patterns),
               ]

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnString(type_info):
        if type_info.ValidationExpression:
            return [ RegularExpression.PythonToJavaScript(type_info.ValidationExpression),
                   ]

        if type_info.MinLength in [ 0, None ] and type_info.MaxLength is None:
            return [ ".*", ]

        if type_info.MinLength == 1 and type_info.MaxLength is None:
            return [ ".+", ]

        assert type_info.MinLength is not None
        
        if type_info.MaxLength is None:
            return [ ".{%d}.*" % type_info.MinLength, ]

        if type_info.MinLength == type_info.MaxLength:
            return [ ".{%d}" % type_info.MinLength, ]

        assert type_info.MaxLength is not None

        return [ ".{%d,%d}" % (type_info.MinLength, type_info.MaxLength), ]

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnTime(type_info):
        return [ textwrap.dedent(
                    # <Wrong hanging indentation> pylint: disable = C0330
                   r"""(?# 
                    Hour                        )(?P<hour>[0-1][0-9]|2[0-3]):(?#
                    Minute                      )(?P<minute>[0-5][0-9]):(?#
                    Second                      )(?P<second>[0-5][0-9])(?#
                    Microseconds [optional]     )(?:\.(?P<microseconds>\d+))?(?#
                    )"""),
               ]

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnUri(type_info):
        # This regex is overly aggressive in identifying uris, but should work in most cases.
        return [ r"\S+?://\S+", ]

# ----------------------------------------------------------------------
@staticderived
class StringSerialization(Serialization):
    """Serializes items to a from strings."""

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _SerializeItemImpl(type_info, item, **custom_kwargs):
        
        # custom_kwargs:
        #
        #   type_info type          Key             Value       Default             Desc
        #   ----------------------  --------------  ----------  ------------------  ----------------
        #   DateTimeTypeInfo        sep             string      ' '                 String that separates dates and times (' ' or 'T')
        #   DateTypeTypeInfo        microseconds    bool        True                Disables the display of microseconds during serialization if the value is False
        #   DurationTypeInfo        sep             string      '.'                 String that separates days and hours ('.' or ':')

        if type_info.Arity.IsOptional and item is None:
            return "None"

        return _SerializationVisitor.Accept(type_info, item, custom_kwargs)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def _DeserializeItemImpl(type_info, item, **custom_kwargs):
        
        # custom_kwargs:
        #
        #   type_info type          Key         Value       Default             Desc
        #   ----------------------  ----------  ----------  ------------------  ----------------
        #   DirectoryTypeInfo       normalize   Boolean     True                Applies os.path.realpath and os.path.normpath to the string
        #   FilenameTypeInfo        normalize   Boolean     True                Applies os.path.realpath and os.path.normpath to the string

        if type_info.Arity.IsOptional and isinstance(item, six.string_types) and item.lower() == "none":
            return None

        regex_strings = RegularExpressionVisitor.Accept(type_info)

        for regex_index, regex_string in enumerate(regex_strings):
            if isinstance(regex_string, tuple):
                regex_string, regex_flags = regex_string
            else:
                regex_flags = re.DOTALL | re.MULTILINE

            if not regex_string.startswith('^'):
                regex_string = "^{}".format(regex_string)
            if not regex_string.endswith('$'):
                regex_string = "{}$".format(regex_string)

            potential_match = re.match(regex_string, item, regex_flags)
            if potential_match:
                return _DeserializationVisitor.Accept(type_info, item, custom_kwargs, potential_match, regex_index)

        # If here, we didn't find anything
        error = "'{}' is not a valid '{}' string".format(item, type_info.Desc)

        if type_info.ConstraintsDesc:
            error += " - {}".format(type_info.ConstraintsDesc)

        raise ValidationException(error)

# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
@staticderived
class _SerializationVisitor(Visitor):
    
    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnBool(type_info, item, custom_kwargs):
        return str(item)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDateTime(type_info, item, custom_kwargs):
        if not custom_kwargs.get("microseconds", True):
            item = item.replace(microsecond=0)

        return item.isoformat(sep=custom_kwargs.get("sep", ' '))

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDate(type_info, item, custom_kwargs):
        return item.isoformat()

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnDirectory(cls, type_info, item, custom_kwargs):
        return cls.OnFilename(type_info, item, custom_kwargs)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDuration(type_info, item, custom_kwargs):
        seconds = item.total_seconds()

        days, seconds = divmod(seconds, 60 * 60 * 24)
        hours, seconds = divmod(seconds, 60 * 60)
        minutes, seconds = divmod(seconds, 60)

        days = int(days)
        hours = int(hours)
        minutes = int(minutes)

        if days:
            prefix = "{days}{sep}{hours:02}".format( days=days,
                                                     sep=custom_kwargs.get("sep", '.'),
                                                     hours=hours,
                                                   )
        else:
            prefix = str(hours)

        # {seconds:02.6f} doesn't work as a formatting string on some versions of python,
        # so we need to do it ourselves.
        prefix = "{prefix}:{minutes:02}:".format(**locals())

        second_parts = str(seconds).split('.')
        assert len(second_parts) == 2, second_parts

        assert len(second_parts[0]) <= 2, second_parts[0]
        second_parts[0] = second_parts[0].rjust(2, '0')

        if second_parts[1] == "0":
            return "{}{}".format(prefix, second_parts[0])

        second_parts[1] = second_parts[1].ljust(6, '0')
        if len(second_parts[1]) > 6:
            second_parts[1] = second_parts[1][:6]

        return "{}{}.{}".format(prefix, second_parts[0], second_parts[1])

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnEnum(type_info, item, custom_kwargs):
        return item

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnFilename(type_info, item, custom_kwargs):
        return item.replace(os.path.sep, '/')

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnFloat(type_info, item, custom_kwargs):
        return str(item)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnGuid(type_info, item, custom_kwargs):
        return str(item)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnInt(type_info, item, custom_kwargs):
        return str(item)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnString(type_info, item, custom_kwargs):
        return item

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnTime(type_info, item, custom_kwargs):
        return item.isoformat()

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnUri(type_info, item, custom_kwargs):
        return item.ToString()

# ----------------------------------------------------------------------
@staticderived
class _DeserializationVisitor(Visitor):
    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnBool(type_info, item, custom_kwargs, regex_match, regex_index):
        return item.lower() in [ "true", "t", "yes", "y", "1", ]

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnDateTime(cls, type_info, item, custom_kwargs, regex_match, regex_index):
        if regex_index == 0:
            # ISO Format
            item, time_format_string = cls._GetTimeExpr(item)
            
            has_timezone = True
            groupdict = regex_match.groupdict()
            
            for attribute_name in [ "tz_hour", "tz_minute", ]:
                if groupdict.get(attribute_name, None) is None:
                    has_timezone = False
                    break
            
            if not has_timezone:
                if groupdict.get("tz_utc", None):
                    assert item.endswith('Z'), item
                    item = item[:-1]
            
            return datetime.datetime.strptime( item,
                                               "%Y-%m-%d{sep}{time_format_string}".format( sep='T' if 'T' in item else ' ',
                                                                                           time_format_string=time_format_string,
                                                                                         ),
                                             )

        assert regex_index in [ 1, 2, ], regex_index

        if regex_index == 1:
            stamp = regex_match.group("stamp")
        else:
            stamp = item

        # timestamp to date time
        result = datetime.datetime.utcfromtimestamp(float(stamp))

        if regex_index == 1 and regex_match.groupdict().get("tz_hour", None) is not None:
            delta = datetime.timedelta(hours=int(regex_match.group("tz_hour")), minutes=int(regex_match.group("tz_minute")))

            if regex_match.groupdict().get("tz_sign", None) != '-':
                delta = -delta

            result = result + delta

        return result

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDate(type_info, item, custom_kwargs, regex_match, regex_index):
        year = int(regex_match.group("year{}".format(regex_index)))
        month = int(regex_match.group("month{}".format(regex_index)))
        day = int(regex_match.group("day{}".format(regex_index)))

        if year < 100:
            # Assume that the year applies to the current century. This could
            # lead to ambiguity late in each century. :)
            year = int(datetime.datetime.now().year / 100) * 100 + year

        return datetime.date( year=year,
                              month=month,
                              day=day,
                            )

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnDirectory(cls, type_info, item, custom_kwargs, regex_match, regex_index):
        return cls.OnFilename(type_info, item, custom_kwargs, regex_match, regex_index)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnDuration(type_info, item, custom_kwargs, regex_match, regex_index):
        parts = item.split(':')

        if len(parts) == 4:
            # days:hours:minutes:seconds
            days = int(parts[0])
            hours = int(parts[1])
            minutes = int(parts[2])
            seconds_string = parts[3]

        elif len(parts) == 3:
            # days.hours:minutes:seconds
            #   or
            # hours:minutes:seconds
            
            days_and_hours = parts[0].split('.')
            if len(days_and_hours) == 2:
                days = int(days_and_hours[0])
                hours = int(days_and_hours[1])
            else:
                days = 0
                hours = int(days_and_hours[0])

            minutes = int(parts[1])
            seconds_string = parts[2]

        else:
            assert False, parts
        
        second_parts = seconds_string.split('.')
        if len(second_parts) == 2:
            # seconds.microseconds
            seconds = int(second_parts[0])
            microseconds = int(second_parts[1])
        else:
            # seconds
            seconds = int(second_parts[0])
            microseconds = 0

        return datetime.timedelta( days=days,
                                   hours=hours,
                                   minutes=minutes,
                                   seconds=seconds,
                                   microseconds=microseconds,
                                 )

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnEnum(type_info, item, custom_kwargs, regex_match, regex_index):
        return item

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnFilename(type_info, item, custom_kwargs, regex_match, regex_index):
        item = item.replace('/', os.path.sep)

        if custom_kwargs.get("normalize", True) and not item.startswith("\\\\"):
            item = FileSystem.Normalize(item)

        return item

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnFloat(type_info, item, custom_kwargs, regex_match, regex_index):
        return float(item)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnGuid(type_info, item, custom_kwargs, regex_match, regex_index):
        return uuid.UUID(item)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnInt(type_info, item, custom_kwargs, regex_match, regex_index):
        return int(item)

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnString(type_info, item, custom_kwargs, regex_match, regex_index):
        return item

    # ----------------------------------------------------------------------
    @classmethod
    @override
    def OnTime(cls, type_info, item, custom_kwargs, regex_match, regex_index):
        return datetime.datetime.strptime(*cls._GetTimeExpr(item)).time()

    # ----------------------------------------------------------------------
    @staticmethod
    @override
    def OnUri(type_info, item, custom_kwargs, regex_match, regex_index):
        return UriTypeInfo.Uri.FromString(item)

    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    # ----------------------------------------------------------------------
    @staticmethod
    def _GetTimeExpr(item):
        # Limit the fractional part of the time string to 6 chars
        period_index = item.rfind('.')
        if period_index != -1:
            to_trim = len(item) - period_index - 1 - 6
            if to_trim > 0:
                item = item[:-to_trim]

        return item, "%H:%M{seconds}{fraction_seconds}" \
                        .format( seconds=":%S" if item.count(':') > 1 else '',
                                 fraction_seconds=".%f" if '.' in item else '',
                               )
