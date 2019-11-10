import multiprocessing
import threading
import queue

from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw

from screen import Location

# todo: errors here are not caught... log them somehow?
# todo: add logging instead of print

class InkyDeviceController(multiprocessing.Process):

    def __init__(self, shutdown_event, render_queue):
        super(InkyDeviceController, self).__init__()
        self.thread_shutdown_event = shutdown_event
        self.shutdown_event = multiprocessing.Event()
        self.render_queue = render_queue

        self.start_shutdown_listener_thread()

    # we have a thread listening on the threading.event (from the signal handler) which should trigger a multiprocessing.event (to stop any future device rendering)
    # this indirection is necessary since a multiprocessing.event cannot be safely used within the same process (potential deadlock)
    def start_shutdown_listener_thread(self):
        t = threading.Thread(target=self.shutdown_listener_thread,)
        t.daemon = True
        t.start()

    def shutdown_listener_thread(self):

        # why does wait deadlock? I shouldn't need a loop here...
        while not self.thread_shutdown_event.is_set():
            self.thread_shutdown_event.wait(timeout=0.1)


        print('signaling inky device shutdown')
        self.shutdown_event.set()

    def run(self):
        device = InkyDevice()

        previous_item = {} # render nothing
        while not self.shutdown_event.is_set():
            try:
                render_result = self.render_queue.get(block=True, timeout=0.2)
                if render_result != previous_item:
                    device.write(render_result)
                previous_item = render_result
            except queue.Empty:
                continue
        device.shutdown()

        print("exiting inky device handler process...")

class InkyDevice():

    def __init__(self):
        self.display = InkyPHAT("black")
        self.display.set_border(self.display.WHITE)
        self.default_font_size = 12
        self.default_font_face = 'Eden_Mills_Bold.ttf'
        self.font_face = self.default_font_face
        self.set_font()
        self.lock = threading.Lock()

        self.startup()

    def set_font(self, face=None, size=None):
        if face is None:
            face = self.default_font_face
        face = os.path.join('resources', os.path.basename(face))

        if size is None:
            size = self.default_font_size
        size = min(30, max(size, 10))
        
        self.font = ImageFont.truetype(face, size)

    def startup(self):
        print('writing startup image...')
        with self.lock:
            img = Image.open("resources/k8s-bw.png")
            draw = ImageDraw.Draw(img)
            self.display.set_image(img)
            self.display.show()

    def shutdown(self):
        print('writing shutdown image...')
        with self.lock:
            img = Image.open("resources/8-bit-dino.png")
            draw = ImageDraw.Draw(img)

            font = ImageFont.truetype('resources/Eden_Mills_Bold.ttf', 28)
            
            message = "offline    "
            message_width, message_height = self.get_text_size(message, font)
            x, y = Location.CenterRight.place(message, font, message_width, message_height, self.display.WIDTH, self.display.HEIGHT)
            draw.text((x, y), message, self.display.BLACK, font)

            self.display.set_image(img)
            self.display.show()

    def get_text_size(self, message, font):
        # render the text in another text buffer to get the dimensions
        message_width, message_height = 0,0
        for line in message.split("\n"):
            partial_width, partial_height = font.getsize(line)
            message_width = max(message_width, partial_width)
            approx_line_spacing = 1.2
            message_height += int(partial_height*approx_line_spacing)

        return message_width, message_height

    def write(self, render_result):
        with self.lock:

            img = Image.new("P", (self.display.WIDTH, self.display.HEIGHT))
            draw = ImageDraw.Draw(img)

            for location, buffer_render in render_result.items():

                self.set_font(size=buffer_render.font_size)

                # render the text in another text buffer to get the dimensions
                message_width, message_height = self.get_text_size(buffer_render.content, self.font)

                # find the placement of the text buffer and overlay onto the screen buffer
                x, y = location.place(buffer_render.content, self.font, message_width, message_height, self.display.WIDTH, self.display.HEIGHT)
                draw.text((x, y), buffer_render.content, self.display.BLACK, self.font)

            # flush the screen buffer to the device
            self.display.set_image(img)
            self.display.show()