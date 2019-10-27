import time
import sys
import signal
import threading
import datetime
import functools
import multiprocessing

from xmlrpc.server import SimpleXMLRPCServer

from screen import Screen
from device import InkyDeviceController


class RPCServer():

    def __init__(self, shutdown_event, render_queue, screen, host="localhost", port=5000, interval=10):
        self.screen = screen
        self.port = port
        self.host = host
        self.interval = interval
        self.shutdown_event = shutdown_event

        self.server = SimpleXMLRPCServer((host, port), allow_none=True)
        self.server.register_function(screen.register_buffer, "register_buffer")
        self.server.register_function(screen.unregister_buffer, "unregister_buffer")
        self.server.register_function(screen.update_row, "update_row")
        self.server.register_function(screen.clear_buffer, "clear_buffer")

        self.render_queue = render_queue

    def start(self):
        rpc_thread = threading.Thread(target=self.listen_rpc_requests,)
        rpc_thread.daemon = True
        rpc_thread.start()

        event_thread = threading.Thread(target=self.generate_events,)
        event_thread.daemon = True
        event_thread.start()

    # generate events for grabing the screen state and pushing to the device (via queue)
    def generate_events(self):
        print('generating screen events...')
        while not self.shutdown_event.is_set():
            self.render_queue.put(self.screen.render())
            time.sleep(self.interval)

    def listen_rpc_requests(self):
        print("listening on %s:%d..." % (self.host, self.port))
        self.server.serve_forever()


class SignalObject:
    MAX_TERMINATE_CALLED = 3

    def __init__(self, shutdown_event):
        self.terminate_called = 0
        self.shutdown_event = shutdown_event

def default_signal_handler(signal_object, exception_class, signal_num, current_stack_frame):
    signal_object.terminate_called += 1
    signal_object.shutdown_event.set()
    if signal_object.terminate_called == signal_object.MAX_TERMINATE_CALLED:
        raise exception_class()

def init_signal(signal_num, signal_object, exception_class, handler):
    handler = functools.partial(handler, signal_object, exception_class)
    signal.signal(signal_num, handler)
    signal.siginterrupt(signal_num, False)

def init_signals(shutdown_event, int_handler=default_signal_handler, term_handler=default_signal_handler):
    signal_object = SignalObject(shutdown_event)
    init_signal(signal.SIGINT, signal_object, KeyboardInterrupt, int_handler)
    init_signal(signal.SIGTERM, signal_object, RuntimeError("TerminateInterrupt"), term_handler)
    return signal_object

def main():
    shutdown_event = threading.Event()
    init_signals(shutdown_event)

    render_queue = multiprocessing.Queue()
    screen = Screen()

    # listens for renderable events
    inky_device = InkyDeviceController(shutdown_event, render_queue)
    inky_device.start()

    # generates renderable events
    rpc_server = RPCServer(shutdown_event, render_queue, screen)
    rpc_server.start()

    # why does wait deadlock? I shouldn't need a loop here...
    while not shutdown_event.is_set():
        shutdown_event.wait(timeout=0.1)
    print("main thread shutdown")


if __name__ == "__main__":
    main()