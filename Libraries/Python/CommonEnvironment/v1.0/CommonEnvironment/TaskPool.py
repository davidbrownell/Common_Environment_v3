# ----------------------------------------------------------------------
# |  
# |  TaskPool.py
# |  
# |  David Brownell <db@DavidBrownell.com>
# |      2018-05-23 19:48:29
# |  
# ----------------------------------------------------------------------
# |  
# |  Copyright David Brownell 2018.
# |  Distributed under the Boost Software License, Version 1.0.
# |  (See accompanying file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
# |  
# ----------------------------------------------------------------------
"""Tools that help when creating tasks that execute in parallel."""

import datetime
import multiprocessing
import os
import sys
import textwrap
import time
import threading
import traceback

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from enum import Enum
import six

from CommonEnvironment import Nonlocals
from CommonEnvironment import Interface
from CommonEnvironment.StreamDecorator import StreamDecorator

# ----------------------------------------------------------------------
_script_fullpath = os.path.abspath(__file__) if "python" in sys.executable.lower() else sys.executable
_script_dir, _script_name = os.path.split(_script_fullpath)
# ----------------------------------------------------------------------

StreamDecorator.InitAnsiSequenceStreams()

# ----------------------------------------------------------------------
# |  
# |  Public Types
# |  
# ----------------------------------------------------------------------
class Task(object):
    """Work to be executed in parallel"""

    # ----------------------------------------------------------------------
    def __init__( self,
                  name,                     # Used when display status
                  functor,                  # def Functor(<args>) -> None|str|(result, str)
                                            #
                                            #       Where <args> can be zero or more of:
                                            #           task_index
                                            #           core_index          # Technically speaking, this isn't the core index but is sufficient to simulate thread local storage
                                            #           output_stream
                                            #           on_status_update    # def Func(content)
                ):
        assert name
        assert functor

        self.Name                           = name
        self.Functor                        = functor

# ----------------------------------------------------------------------
class ExecuteException(Exception):
    def __init__(self, exceptions):
        strs = []

        for index, ex in six.iteritems(exceptions):
            strs.append("{}) {}".format(index, str(ex)))

        super(ExecuteException, self).__init__('\n'.join(strs))

        self.Exceptions                     = exceptions

# ----------------------------------------------------------------------
# |  
# |  Public Methods
# |  
# ----------------------------------------------------------------------
def Transform( items,
               functor,                     # def Func(item) -> transformed item
               optional_output_stream,
               display_exception_callstack=False,
               display_errors=True,
               num_concurrent_tasks=None,
               name_functor=None,           # def Func(index, item) -> string
             ):
    """
    Applies the functor to each item in the list of items, returning a list of
    transformed items. The operation is considered to be atomic, and will raise
    an exception if one or more of the functor invocations fail.
    """

    assert items
    assert functor

    functor = Interface.CreateCulledCallable(functor)
    name_functor = name_functor or (lambda index, item: "Results from {} [{}]".format(str(item), index))

    transformed_items = [ None, ] * len(items)

    # ----------------------------------------------------------------------
    def Impl(task_index, on_status_update):
        transformed_items[task_index] = functor(OrderedDict([ ( "item", items[task_index] ),
                                                              ( "on_status_update", on_status_update ),
                                                            ]))

    # ----------------------------------------------------------------------

    Execute( [ Task(name_functor(index, item), Impl) for index, item in enumerate(items) ],
             optional_output_stream=optional_output_stream,
             progress_bar=bool(optional_output_stream),
             raise_on_error=True,
             display_exception_callstack=display_exception_callstack,
             display_errors=display_errors,
             num_concurrent_tasks=num_concurrent_tasks,
           )

    return transformed_items

# ----------------------------------------------------------------------
def Execute( tasks,
             optional_output_stream,
             verbose=False,
             progress_bar=False,
             progress_bar_cols=150,
             raise_on_error=False,
             display_exception_callstack=True,
             display_errors=True,
             num_concurrent_tasks=None,
           ):
    """Invokes each task in parallel"""

    assert tasks

    tasks = [ _InternalTask(task) for task in tasks ]
    num_concurrent_tasks = num_concurrent_tasks or (multiprocessing.cpu_count() * 5)
    output_stream = optional_output_stream or StreamDecorator(None)

    prev_statuses = []

    # ----------------------------------------------------------------------
    class StatusUpdate(Enum):
        Start = 1
        Status = 2
        Stop = 3

    # ----------------------------------------------------------------------
    def Invoke( get_status_functor,                     # def Func(future, task, update_type, optional_content) -> string
                write_statuses_functor,                 # def Func(statuses)
                clear_status_when_complete=False,
                display_status_update_frequency=0.5,    # seconds
              ):
        tls = threading.local()

        nonlocals = Nonlocals(thread_index=0)
        thread_index_mutex = threading.Lock()

        futures = []

        initialized_event = threading.Event()
        terminate_event = threading.Event()

        # ----------------------------------------------------------------------
        def UpdateStatus(future, task, update_type, optional_content):
            with task.status_lock:
                task.status = get_status_functor(future, task, update_type, optional_content)

        # ----------------------------------------------------------------------
        def DisplayStatusesThreadProc():
            previous = None

            while True:
                statuses = []

                for task in tasks:
                    with task.status_lock:
                        if task.status:
                            statuses.append(task.status)

                if statuses != previous:
                    write_statuses_functor(statuses)
                    previous = statuses

                initialized_event.set()

                if terminate_event.wait(display_status_update_frequency):
                    break

            write_statuses_functor([])

        # ----------------------------------------------------------------------
        def Func(task, task_index):
            this_thread_index = getattr(tls, "index", None)
            if this_thread_index is None:
                with thread_index_mutex:
                    this_thread_index = nonlocals.thread_index
                    nonlocals.thread_index += 1

                setattr(tls, "index", this_thread_index)

            initialized_event.wait()

            start_time = time.time()
            future = futures[task_index]

            sink = six.moves.StringIO()

            # ----------------------------------------------------------------------
            def OnStatusUpdate(content):
                UpdateStatus(future, task, StatusUpdate.Status, content)

            # ----------------------------------------------------------------------

            try:
                result = task.Functor(OrderedDict([ ( "task_index", task_index ),
                                                    ( "output_stream", sink ),
                                                    ( "core_index", this_thread_index ),
                                                    ( "on_status_update", OnStatusUpdate ),
                                                  ]))

                if result is None:
                    task.result = 0

                elif isinstance(result, six.string_types):
                    task.result = 0
                    sink.write(result)

                elif isinstance(result, tuple):
                    task.result = result[0]
                    sink.write(result[1])

                else:
                    task.result = result

            except:
                task.result = -1

                message = str(sys.exc_info()[1]).rstrip()

                OnStatusUpdate("ERROR: {}".format(message))

                if display_exception_callstack:
                    sink.write(traceback.format_exc())
                else:
                    sink.write("{}\n".format(message))

            if clear_status_when_complete and task.result >= 0:
                OnStatusUpdate(None)

            task.output = sink.getvalue()
            task.time_delta_string = str(datetime.timedelta(seconds=(time.time() - start_time)))

            task.complete.set()

        # ----------------------------------------------------------------------

        with ThreadPoolExecutor(min(num_concurrent_tasks, len(tasks))) as executor:
            futures += [ executor.submit(Func, task, index) for index, task in enumerate(tasks) ]
            
            # We can't combine this loop with the comprehension above, as the
            # update status functor expects a fully constructed list of futures.
            for future, task in six.moves.zip(futures, tasks):
                UpdateStatus(future, task, StatusUpdate.Start, None)
                future.add_done_callback(lambda ignore, future=future, task=task: UpdateStatus(future, task, StatusUpdate.Stop, None))

            display_thread = threading.Thread(target=DisplayStatusesThreadProc)
            display_thread.start()

            exceptions = OrderedDict()

            for index, future in enumerate(futures):
                try:
                    future.result()
                except Exception as ex:
                    # An exception here is pretty significant error and likely something that 
                    # happened outside the scope of the executed function. This code is here to 
                    # prevent a catastrophic failure within the TaskPool.
                    exceptions[index] = ex

            terminate_event.set()
            display_thread.join()

            if exceptions:
                raise ExecuteException(exceptions)

    # ----------------------------------------------------------------------
    def WriteStatuses(statuses):
        original_statuses = list(statuses)

        for index, status in enumerate(statuses):
            if index < len(prev_statuses):
                prev_status = prev_statuses[index]
            else:
                prev_status = ''

            if len(status) < len(prev_status):
                statuses[index] = "{}{}".format(status, ' ' * (len(prev_status) - len(status)))

        if len(statuses) < len(prev_statuses):
            for index in six.moves.range(len(statuses), len(prev_statuses)):
                statuses.append(' ' * len(prev_statuses[index]))

        if statuses:
            # Write the content
            output_stream.write('\n'.join([ "\r{}".format(status) for status in statuses ]))

            # Move back to the original line
            output_stream.write("\033[{}A\r".format(len(statuses) - 1))

        prev_statuses[:] = original_statuses

    # ----------------------------------------------------------------------

    if progress_bar:
        from tqdm import tqdm

        pb_lock = threading.Lock()

        with tqdm( total=len(tasks),
                   file=output_stream,
                   ncols=progress_bar_cols,
                   unit=" items",
                   leave=False,
                 ) as pb:
            # ----------------------------------------------------------------------
            def PBGetStatus(_, task, update_type, optional_content):
                if update_type == StatusUpdate.Stop:
                    with pb_lock:
                        pb.update()

                if not optional_content:
                    return optional_content

                return "    {}: {}".format(task.Name, optional_content)

            # ----------------------------------------------------------------------
            def PBWriteStatuses(statuses):
                with pb_lock:
                    # Move down one line to compensate for the progress bar
                    output_stream.write("\033[1B") 

                    WriteStatuses(statuses)

                    # Move up one line to move back to the progress bar
                    output_stream.write("\033[1A\r")

            # ----------------------------------------------------------------------

            Invoke( PBGetStatus,
                    PBWriteStatuses,
                    clear_status_when_complete=True,
                  )

    else:
        max_name_length = max(50, *[ len(task.Name) for task in tasks ])

        status_template = "  {{name:<{}}} {{suffix}}".format(max_name_length + 1)

        # ----------------------------------------------------------------------
        def GetStatus(future, task, update_type, optional_content):
            if task.complete.is_set():
                suffix = "DONE! ({}, {})".format(task.result, task.time_delta_string)
            elif future.running():
                suffix = "Running"
            else:
                suffix = "Queued"

            if optional_content:
                suffix += " [{}]".format(optional_content)

            return status_template.format( name="{}:".format(task.Name),
                                           suffix=suffix,
                                         )

        # ----------------------------------------------------------------------

        Invoke(GetStatus, WriteStatuses)

    # Calculate the final result
    sink = six.moves.StringIO()

    # ----------------------------------------------------------------------
    def Output(stream, task):
        stream.write(textwrap.dedent(
            """\

            # ----------------------------------------------------------------------
            # |  
            # |  {name} ({result}, {time})
            # |  
            # ----------------------------------------------------------------------
            {output}

            """).format( name=task.Name,
                         result=task.result,
                         time=task.time_delta_string,
                         output=task.output,
                       ))

    # ----------------------------------------------------------------------

    result = 0

    for task in tasks:
        if task.result != 0:
            Output(sink, task)
            result = result or task.result

    sink = sink.getvalue()

    if display_errors and result != 0:
        if raise_on_error:
            raise Exception(sink or result)
        elif hasattr(output_stream, "write_error"):
            for line in sink.split('\n'):
                output_stream.write_error(line)
        else:
            output_stream.write(sink)

    if verbose and result == 0:
        sink = six.moves.StringIO()

        for task in tasks:
            if task.output:
                Output(sink, task)

        sink = sink.getvalue()

        if hasattr(output_stream, "write_verbose"):
            for line in sink.split('\n'):
                output_stream.write_verbose(line)
        else:
            output_stream.write(sink)

    return result

# ----------------------------------------------------------------------
# |  
# |  Private Types
# |  
# ----------------------------------------------------------------------
class _InternalTask(Task):
    def __init__(self, task):
        super(_InternalTask, self).__init__( task.Name,
                                             Interface.CreateCulledCallable(task.Functor),
                                           )

        # Working data
        self.output                         = ''
        self.result                         = 0
        self.time_delta_string              = ''

        self.status                         = None
        self.status_lock                    = threading.Lock()

        self.complete                       = threading.Event()
