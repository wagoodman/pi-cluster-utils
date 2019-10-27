import time
import sys
# import signal
import threading
import datetime
# import functools
import multiprocessing

from xmlrpc.server import SimpleXMLRPCServer

from screen import Screen
from device import handle_events

PORT = 5000
SCREEN = Screen()


# generate events for grabing the screen state and pushing to the device (via queue)
def screen_state_update_loop(render_queue):
    while True:
        render_queue.put(SCREEN.render())
        time.sleep(10)

def render_loop():
    shutdown_event = multiprocessing.Event()
    render_queue = multiprocessing.Queue()

    # start the render loop (thread)
    t = threading.Thread(target=screen_state_update_loop, args=(render_queue,))
    t.daemon = True
    t.start()

    # start the device worker (process)
    p = multiprocessing.Process(target=handle_events, args=(shutdown_event, render_queue,))
    p.start()
    return render_queue


# class SignalObject:
#     MAX_TERMINATE_CALLED = 3

#     def __init__(self, shutdown_event):
#         self.terminate_called = 0
#         self.shutdown_event = shutdown_event

# def default_signal_handler(signal_object, exception_class, signal_num, current_stack_frame):
#     signal_object.terminate_called += 1
#     signal_object.shutdown_event.set()
#     if signal_object.terminate_called == signal_object.MAX_TERMINATE_CALLED:
#         raise exception_class()

# def init_signal(signal_num, signal_object, exception_class, handler):
#     handler = functools.partial(handler, signal_object, exception_class)
#     signal.signal(signal_num, handler)
#     signal.siginterrupt(signal_num, False)

# def init_signals(shutdown_event, int_handler=default_signal_handler, term_handler=default_signal_handler):
#     signal_object = SignalObject(shutdown_event)
#     init_signal(signal.SIGINT, signal_object, KeyboardInterrupt, int_handler)
#     init_signal(signal.SIGTERM, signal_object, RuntimeError("TerminateInterrupt"), term_handler)
#     return signal_object

def main():
    # init_signals(SHUTDOWN)

    render_loop()

    server = SimpleXMLRPCServer(("localhost", PORT), allow_none=True)
    server.register_function(SCREEN.register_buffer, "register_buffer")
    server.register_function(SCREEN.unregister_buffer, "unregister_buffer")
    server.register_function(SCREEN.update_row, "update_row")
    server.register_function(SCREEN.clear_buffer, "clear_buffer")

    print("Listening on port %d..." % PORT)
    server.serve_forever()

if __name__ == "__main__":
    main()