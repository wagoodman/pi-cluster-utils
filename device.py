from threading import Lock
import queue

from inky import InkyPHAT
from PIL import Image, ImageFont, ImageDraw

def handle_events(shutdown_event, render_queue):
    # while not shutdown_event.is_set():
    #     try:
    #         render_result = render_queue.get(block=True, timeout=0.5)
    #         print(render_result)
    #     except queue.Empty:
    #         continue

    device = InkyDevice()
    previous_item = None
    while not shutdown_event.is_set():
        try:
            render_result = render_queue.get(block=True, timeout=0.5)
            if render_result != previous_item:
                device.write(render_result)
            previous_item = render_result
        except queue.Empty:
            continue

    print("exiting device handler process...")

class InkyDevice():

    def __init__(self):
        self.display = InkyPHAT("black")
        self.display.set_border(self.display.WHITE)
        self.font = ImageFont.truetype('resources/Eden_Mills_Bold.ttf', 12)
        self.lock = Lock()

    def write(self, render_result):
        with self.lock:
            img = Image.new("P", (self.display.WIDTH, self.display.HEIGHT))
            draw = ImageDraw.Draw(img)

            for location, message in render_result.items():

                # render the text in another text buffer to get the dimensions
                message_width, message_height = 0,0
                for line in message.split("\n"):
                    partial_width, partial_height = self.font.getsize(line)
                    message_width = max(message_width, partial_width)
                    approx_line_spacing = 1.2
                    message_height += int(partial_height*approx_line_spacing)

                # find the placement of the text buffer and overlay onto the screen buffer
                x, y = location.place(message, self.font, message_width, message_height, self.display.WIDTH, self.display.HEIGHT)
                draw.text((x, y), message, self.display.BLACK, self.font)

            # flush the screen buffer to the device
            self.display.set_image(img)
            self.display.show()