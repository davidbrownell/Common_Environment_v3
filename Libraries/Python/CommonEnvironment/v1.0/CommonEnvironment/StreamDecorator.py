# ----------------------------------------------------------------------
# |  
# |  StreamDecorator.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-05 11:46:08
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
# """Contains the StreamDecorator object"""

import datetime
import os
import re
import sys
import time

from contextlib import contextmanager

from CommonEnvironment import Nonlocals
from CommonEnvironment.CallOnExit import CallOnExit
from CommonEnvironment import StringHelpers

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

# <Naming style> pylint: disable = C0103

# ----------------------------------------------------------------------
class StreamDecorator(object):
    """Augments the provided stream with additional functionality."""

    # ----------------------------------------------------------------------
    # |  
    # |  Public Methods
    # |  
    # ----------------------------------------------------------------------
    @classmethod
    def AreAnsiSequenceStreamsInitialized(cls):
        return getattr(cls, "_ansi_sequence_streams_initialized", False)

    # ----------------------------------------------------------------------
    @classmethod
    def InitAnsiSequenceStreams(cls):
        """Initializes colorama"""
        if not cls.AreAnsiSequenceStreamsInitialized():
            import colorama

            colorama.init()
            cls._ansi_sequence_streams_initialized = True

    # ----------------------------------------------------------------------
    @classmethod
    @contextmanager
    def GenerateAnsiSequenceStream( cls,
                                    stream,
                                    preserve_ansi_escape_sequences=False,
                                    autoreset=False,
                                    do_not_modify_std_streams=False,
                                  ):
        """
        Ensures that sys.stdout and sys.stderr are configured to preserve
        (or not preserve) ansi escape sequences.
        """

        # By default, colorama initializes sys.stdout and sys.stderr to strip
        # and convert ansi escape sequences.
        cls.InitAnsiSequenceStreams()

        if not preserve_ansi_escape_sequences:
            if not isinstance(stream, cls):
                stream = cls(stream)

            yield stream
            return

        import colorama.initialise as cinit
        from colorama.ansitowin32 import AnsiToWin32

        restore_functors = []

        if do_not_modify_std_streams:
            # CallOnExit needs at least 1 functor
            restore_functors.append(lambda: None)
        else:
            # ----------------------------------------------------------------------
            def RestoreConvertor(wrapped_stream, original_convertor):
                wrapped_stream._StreamWrapper__convertor = original_convertor

            # ----------------------------------------------------------------------

            for wrapped_stream, original_stream in [ ( cinit.wrapped_stdout, cinit.orig_stdout ),
                                                     ( cinit.wrapped_stderr, cinit.orig_stderr ),
                                                   ]:
                original_convertor = wrapped_stream._StreamWraper__convertor

                if not getattr(original_convertor, "_modified", False):
                    convertor = AnsiToWin32( original_stream,
                                             strip=False,
                                             convert=False,
                                             autoreset=autoreset,
                                           )
                    convertor._modified = True

                    wrapped_stream._StreamWrapper__convertor = convertor

                    restore_functors.append(lambda wrapped_stream=wrapped_stream, original_convertor=original_convertor: RestoreConvertor(wrapped_stream, original_convertor))

            if restore_functors:
                cinit.reinit()
                restore_functors.append(cinit.reinit)

        with CallOnExit(*restore_functors):
            this_stream = None

            wrapped = getattr(stream, "_StreamWrapper__wrapped")
            if wrapped:
                if wrapped == cinit.orig_stdout:
                    this_stream = cinit.wrapped_stdout
                elif wrapped == cinit.orig_stderr:
                    this_stream = cinit.wrapped_stderr

            if this_stream is None:
                this_stream = stream

            yield StreamDecorator(cinit.wrap_stream( this_stream,
                                                     convert=False,
                                                     strip=False,
                                                     autoreset=autoreset,
                                                     wrap=True,
                                                   ))

    # ----------------------------------------------------------------------
    def __init__( self,
                  stream_or_streams,                    # Can be None to suppress output
                  line_prefix=None,                     # string or def Func(column_offset) -> string  
                  line_suffix=None,                     # string or def Func(column_offset) -> string
                  prefix=None,                          # string or def Func(column_offset) -> string
                  suffix=None,                          # string or def Func(column_offset) -> string
                  one_time_prefix=None,                 # string or def Func(column_offset) -> string
                  one_time_suffix=None,                 # string or def Func(column_offset) -> string
                  tab_length=4,
                  skip_first_line_prefix=False,         # If True, skip the first line prefix
                  flush_after_write=False,              # Call flush after every write
                  is_associated_stream=False,           # Internal flag set when creating StreamDecorators that are logically associated with other StreamDecorators
                ):
        """
        prefix:                             Content displayed after a flush
        suffix:                             Content displayed immediately before a flush
        line_prefix:                        Content displayed after a newline
        line_suffix:                        Content displayed immediately before a newline
        one_time_prefix:                    Content displayed before the first write
        one_time_suffix:                    Content displayed immediately before the first flush
        """

        self._streams                       = stream_or_streams if isinstance(stream_or_streams, list) else [ stream_or_streams, ] if stream_or_streams is not None else []

        # ----------------------------------------------------------------------
        def ToFunctor(value):
            if callable(value):
                return value

            if value is None:
                value = ''

            return lambda column_index: value

        # ----------------------------------------------------------------------

        self._line_prefix                   = ToFunctor(line_prefix)
        self._line_suffix                   = ToFunctor(line_suffix)
        self._prefix                        = ToFunctor(prefix)
        self._suffix                        = ToFunctor(suffix)
        self._one_time_prefix               = ToFunctor(one_time_prefix)
        self._one_time_suffix               = ToFunctor(one_time_suffix)
        self._tab_length                    = tab_length
        self._flush_after_write             = flush_after_write
        self._skip_first_line_prefix        = skip_first_line_prefix

        self._displayed_one_time_prefix     = False
        self._displayed_one_time_suffix     = False
        self._displayed_prefix              = False
        
        self._column                        = 0
        self._wrote_content                 = False

        self.IsSet                          = any(stream for stream in self._streams if (stream and getattr(stream, "IsSet", True)))
        self.IsAssociatedStream             = is_associated_stream or any(stream for stream in self._streams if (stream and getattr(stream, "IsAssociatedStream", False)))

        encoding = None

        for index, stream in enumerate(self._streams):
            this_encoding = getattr(stream, "encoding", None)
            if this_encoding is not None:
                if encoding is None:
                    encoding = this_encoding
                elif encoding != this_encoding:
                    raise Exception("Encodings do not match ({}: {}, {})".format(index, encoding, this_encoding))

        self.encoding                       = encoding

    # ----------------------------------------------------------------------
    def write(self, content, custom_line_prefix=None):
        if not self._streams or not content:
            return self

        # ----------------------------------------------------------------------
        def Impl(content, eol=None):
            if self._column == 0:
                if self._skip_first_line_prefix:
                    self._skip_first_line_prefix = False
                else:
                    self.write_raw(self._line_prefix(self._column))

                    if custom_line_prefix:
                        self.write_raw(custom_line_prefix)

            self.write_raw(content)
            self._column += len(content) + (content.count('\t') * (self._tab_length - 1))

            if eol:
                self.write_raw(self._line_suffix(self._column))
                self.write_raw(eol)

                self._column = 0

        # ----------------------------------------------------------------------

        if not self._displayed_one_time_prefix:
            self.write_raw(self._one_time_prefix(self._column))
            self._displayed_one_time_prefix = True

        if not self._displayed_prefix:
            self.write_raw(self._prefix(self._column))
            self._displayed_prefix = True

        while True:
            match = self._eol_regex.search(content)
            if not match:
                break

            Impl(content[:match.start()], eol=match.group("eol"))
            content = content[match.end():]

        if content:
            Impl(content)

        self._wrote_content = True

        if self._flush_after_write:
            self.flush()

        return self

    # ----------------------------------------------------------------------
    def write_raw(self, content):
        for stream in self._streams:
            stream.write(content)

        return self

    # ----------------------------------------------------------------------
    def flush( self, 
               force_suffix=False,
               force_newline=False,
             ):
        if self._streams:
            if self._column != 0 and force_newline:
                self.write('\n')

            if self._wrote_content or force_suffix:
                suffix = self._suffix(self._column)

                if self._displayed_one_time_suffix:
                    one_time_suffix = ''
                else:
                    one_time_suffix = self._one_time_suffix(self._column)
                    self._displayed_one_time_suffix = True

                for stream in self._streams:
                    stream.write(suffix)
                    stream.write(one_time_suffix)

                self._displayed_prefix = False
                self._wrote_content = False
                
            for stream in self._streams:
                stream.flush()

        return self

    # ----------------------------------------------------------------------
    @contextmanager
    def DoneManager( self,
                     line_prefix="  ",

                     prefix=None,                       # string or def Func() -> string
                     suffix=None,                       # string or def Func() -> string

                     done_suffix=None,                  # string or def Func() -> string
                     done_suffixes=None,                # List of string or def Func() -> string

                     display=True,                      # Display done information; will sometimes be False for nested DoneManagers created to manage error propagation
                     display_result=True,               # Display the result
                     display_time=True,                 # Display the time delta

                     display_exceptions=True,           # Display exception information
                     display_exception_callstacks=True, # Display exception callstack info
                     suppress_exceptions=False,         # Do not let exception propagate

                     associated_stream=None,    
                     associated_streams=None,           # Streams that should be adjusted in conjunction with this stream. Most of the time, this is used
                                                        # to manage verbose streams that are aligned with status streams, where the status stream is self
                                                        # and the verbose stream content is interleaved with it.
                                                        #
                                                        # Example:
                                                        #     import sys
                                                        #
                                                        #     from StringIO import StringIO 
                                                        #     from CommonEnvironment.StreamDecorator import StreamDecorator
                                                        #
                                                        #     sink = StringIO()
                                                        #     
                                                        #     verbose_stream = StreamDecorator(sink)
                                                        #     status_stream = StreamDecorator([ sys.stdout, verbose_stream, ])
                                                        #     
                                                        #     status_stream.write("0...")
                                                        #     with status_stream.DoneManager(associated_stream=verbose_stream) as ( dm1, verbose_stream1 ):
                                                        #         verbose_stream1.write("Verbose 0\n----")
                                                        #     
                                                        #         dm1.stream.write("1...")
                                                        #         with dm1.stream.DoneManager(associated_stream=verbose_stream1) as ( dm2, verbose_stream2 ):
                                                        #             verbose_stream2.write("Verbose 1\n----")
                                                        #     
                                                        #             dm2.stream.write("2...")
                                                        #             with dm2.stream.DoneManager(associated_stream=verbose_stream2) as ( dm3, verbose_stream3 ):
                                                        #                 verbose_stream3.write("Verbose 2\n----")
                                                        #     
                                                        #                 dm3.stream.write("3...")
                                                        #                 with dm3.stream.DoneManager(associated_stream=verbose_stream3) as ( dm4, verbose_stream4 ):
                                                        #                     verbose_stream4.write("Verbose 3\n----")
                                                        #                     verbose_stream4.flush() 
                                                        #     
                                                        #     sys.stdout.write("\n**\n{}\n**\n".format(sink.getvalue()))
                   ):
        """Displays done information upon completion."""

        assert display_exceptions or not suppress_exceptions, "It isn't wise to not display exceptions while also suppressing them"

        # ----------------------------------------------------------------------
        def ToFunctor(value):
            if callable(value):
                return value

            if value is None:
                value = ''

            return lambda: value

        # ----------------------------------------------------------------------

        prefix_func = ToFunctor(prefix)
        suffix_func = ToFunctor(suffix)

        if not display:
            line_prefix = ''

        nonlocals = Nonlocals(time_delta=None)

        info = self._DoneManagerInfo(self, line_prefix)

        done_suffixes_funcs = [ ToFunctor(ds) for ds in (done_suffixes or []) ]
        if done_suffix:
            done_suffixes_funcs.append(ToFunctor(done_suffix))

        if display_time:
            done_suffixes_funcs.insert(0, lambda: str(nonlocals.time_delta))

        if display_result:
            done_suffixes_funcs.insert(0, lambda: str(info.result))

        # ----------------------------------------------------------------------
        def Cleanup():
            assert info.result is not None
            
            if display:
                prefix = prefix_func()
                suffix = suffix_func()

                suffixes = []

                for done_suffix in done_suffixes_funcs:
                    result = done_suffix()
                    if result:
                        suffixes.append(result)

                if suffixes:
                    content = ', '.join(suffixes)

                    if prefix.strip():
                        content = "({})".format(content)
                    elif not line_prefix:
                        pass
                    else:
                        # Single-line results
                        content = "DONE! ({})".format(content)

                else:
                    content = ''

                self.write("{}{}{}\n".format( prefix,
                                              content,
                                              suffix,
                                            ))
                self.flush()

            # Propogate the result
            if info.result != 0:
                for index, dm in enumerate(info.Enumerate()):
                    if index == 0:
                        continue

                    if ( dm.result != info.result and
                         (dm.result == 0 or (dm.result > 0 and info.result < 0))
                       ):
                        dm.result = info.result

        # ----------------------------------------------------------------------

        with CallOnExit(Cleanup):
            start_time = time.time()

            try:
                associated_streams = associated_streams or []
                if associated_stream:
                    associated_streams.append(associated_stream)
        
                if not associated_streams:
                    yield info
                else:
                    yield tuple([ info, ] + [ StreamDecorator( stream,
                                                               line_prefix=' ' * len(line_prefix),
                                                               one_time_prefix='\n',
                                                               one_time_suffix="\n<flush>",
                                                               is_associated_stream=True,
                                                             )
                                              for stream in associated_streams
                                            ])

                if info.result is None:
                    info.result = 0

            except Exception:
                if info.result is None or info.result >= 0:
                    info.result = -1

                if display_exceptions:
                    ex = sys.exc_info()[1]

                    if ( not getattr(ex, "_DisplayedException", False) and 
                         not getattr(info.stream, "IsAssociatedStream", False)
                       ):
                        ex._DisplayedException = True

                        if display_exception_callstacks:
                            import traceback
                            info.stream.write("ERROR: {}\n".format(StringHelpers.LeftJustify(traceback.format_exc(), len("ERROR: ")).rstrip()))
                        else:
                            info.stream.write("ERROR: {}\n".format(StringHelpers.LeftJustify(str(ex), len("ERROR: ")).rstrip()))

                if not suppress_exceptions:
                    raise

            finally:
                current_time = time.time()

                # There is a bug (and I have seen it) where the value calculated
                # in the past will be greater than the value calculated now. This is
                # wrong in theory, but apparently there is a BIOS bug that causes the
                # behavior on multicore machines (I have a hunch that virtualized machines
                # contribute to the problem as well). More info at http://bytes.com/topic/python/answers/527849-time-clock-going-backwards.
                # Regardless, asserting here is causing problems and this method is
                # only used for scripts. If we encounter the scenario, populate with 
                # bogus data.
                if start_time > current_time:
                    # This is a total lie, but hopefully the value is unique enough to
                    # generate a double take. This is preferable to causing a long-
                    # running process to fail.
                    current_time = start_time + (12 * 60 * 60) + (34 * 60) + 56         # 12:34:56      
                
                assert current_time >= start_time, (current_time, start_time)

                nonlocals.time_delta = str(datetime.timedelta(seconds=current_time - start_time))
            
    # ----------------------------------------------------------------------
    @contextmanager
    def SingleLineDoneManager( self,
                               initial_status,
                               max_cols=150,
                               *done_manager_args,
                               **done_manager_kwargs
                             ):
        """
        Useful when displaying a status message along with a progress bar (or 
        other content) that should disappear once the activity is complete.

        Output is only written via the following methods:

            - write_status                  # Will not be preserved, no impact to result
            - write_verbose                 # Will be preserved, no impact to result
            - write_info                    # Will be preserved, no impact to result
            - write_warning                 # Will be preserved, result = 1
            - write_error                   # Will be preserved, resutl = -1
        """

        if not self.AreAnsiSequenceStreamsInitialized():
            raise Exception("You must call 'InitAnsiSequenceStreams()' before creating this StreamDecorator when using the SingleLineDoneManager")

        nonlocals = Nonlocals( dm_ref=None,
                               dm_write_ref=None,
                               reset_content=True,
                               status_content=None,
                               status_content_prefix=None,
                               first_write=True,
                               max_cols=max_cols,
                             )

        # ----------------------------------------------------------------------
        def GenerateLinePrefix(skip_current):
            # Get the whitespace associated with all parents (if any)
            line_prefix_stack = []

            for index, dm in enumerate(nonlocals.dm_ref.Enumerate()):
                if skip_current and index == 0:
                    continue

                line_prefix_stack.append(dm.stream._line_prefix)

            line_prefix = ''
            while line_prefix_stack:
                line_prefix += line_prefix_stack.pop()(len(line_prefix))

            return line_prefix

        # ----------------------------------------------------------------------
        def ClearTempStatus():
            if nonlocals.status_content is None:
                return

            nonlocals.dm_write_ref("\033[1A\r{}\r".format(' ' * (len(nonlocals.status_content_prefix) + len(nonlocals.status_content))))
            nonlocals.status_content = None

        # ----------------------------------------------------------------------
        def DonePrefix():
            ClearTempStatus()
            
            if not nonlocals.reset_content:
                # Don't eliminate any data that was displayed
                return "DONE! "

            # Move up a line and display the original status message along
            # with the done notifiation.
            return "\033[1A\r{}{}DONE! ".format(GenerateLinePrefix(skip_current=True), initial_status)

        # ----------------------------------------------------------------------

        self.write(initial_status)
        with self.DoneManager( prefix=DonePrefix,
                               *done_manager_args,
                               **done_manager_kwargs
                             ) as dm:
            nonlocals.dm_ref = dm
            nonlocals.dm_write_ref = dm.stream.write

            # ----------------------------------------------------------------------
            def Write(content, prefix, result):
                ClearTempStatus()

                message = StringHelpers.LeftJustify( "{}: {}\n".format(prefix, content.strip()),
                                                     len(prefix),
                                                   )

                if nonlocals.first_write:
                    message = "{}{}".format(dm.stream._line_prefix(0), message)
                    nonlocals.first_write = False

                nonlocals.dm_write_ref(message)
                nonlocals.reset_content = False

                if ( result is not None and 
                     (dm.result in [ None, 0, ] or (dm.result > 0 and result < 0))
                   ):
                    dm.result = result

            # ----------------------------------------------------------------------
            def WriteStatus(content):
                ClearTempStatus()

                if content:
                    if nonlocals.status_content_prefix is None:
                        nonlocals.status_content_prefix = GenerateLinePrefix(skip_current=False)
                        if len(nonlocals.status_content_prefix) < nonlocals.max_cols:
                            nonlocals.max_cols -= len(nonlocals.status_content_prefix)

                    if len(content) > nonlocals.max_cols:
                        content = "{}...{}".format( content[:int(nonlocals.max_cols * 0.40)],
                                                    content[-(len("...") + int(nonlocals.max_cols * 0.60)):],
                                                  )

                    nonlocals.dm_write_ref("\r{}{}\n".format( nonlocals.status_content_prefix,
                                                              content,
                                                            ))

                    nonlocals.status_content = content

            # ----------------------------------------------------------------------

            dm.stream.write_verbose = lambda content: Write(content, "VERBOSE", None)
            dm.stream.write_info = lambda content: Write(content, "INFO", None)
            dm.stream.write_warning = lambda content: Write(content, "WARNING", 1)
            dm.stream.write_error = lambda content: Write(content, "ERROR", -1)
            dm.stream.write_status = WriteStatus

            try:
                yield dm
            except:
                nonlocals.reset_content = False
                raise

    # ----------------------------------------------------------------------
    # |  
    # |  Private Data
    # |  
    # ----------------------------------------------------------------------
    _eol_regex                              = re.compile(r"(?P<eol>\r?\n)")

    # ----------------------------------------------------------------------
    # |  
    # |  Private Types
    # |  
    # ----------------------------------------------------------------------
    class _DoneManagerInfo(object):

        # ----------------------------------------------------------------------
        def __init__(self, stream_decorator, line_prefix, result=0):
            self.stream                     = StreamDecorator( stream_decorator,
                                                               one_time_prefix='\n' if line_prefix else '',
                                                               line_prefix=line_prefix,
                                                               flush_after_write=True,
                                                             )
            self.stream._done_manager       = self

            self.result                     = result

        # ----------------------------------------------------------------------
        def Enumerate(self):
            # ----------------------------------------------------------------------
            def Impl(decorator):
                for stream in decorator._streams:
                    if hasattr(stream, "_done_manager"):
                        yield stream._done_manager

                        for dm in Impl(stream._done_manager.stream):
                            yield dm

            # ----------------------------------------------------------------------

            yield self
            for dm in Impl(self.stream):
                yield dm
        