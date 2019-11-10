import enum
import multiprocessing
from threading import Lock
from collections import namedtuple

DEFAULT_FONT_SIZE = 12

class AutoName(enum.Enum):
    def _generate_next_value_(name, start, count, last_values):
        return name.lower()

class Location(AutoName):
    UpperLeft = enum.auto()
    UpperRight = enum.auto()
    LowerLeft = enum.auto()
    LowerRight = enum.auto()
    Center = enum.auto()
    CenterRight = enum.auto()
    CenterLeft = enum.auto()

    def place(self, message, font, message_width, message_height, width, height):

        if self == Location.UpperLeft:
            return 0, 0

        if self == Location.UpperRight:
            return width-message_width, 0

        if self == Location.LowerLeft:
            return 0, height-message_height

        if self == Location.LowerRight:
            return width-message_width, height-message_height

        if self == Location.Center:
            return width/2 - message_width/2, height/2 - message_height/2

        if self == Location.CenterRight:
            return width-message_width, height/2 - message_height/2

        if self == Location.CenterLeft:
            return 0, height/2 - message_height/2

        raise RuntimeError("unimplemented location placement: %s" % repr(self))

BufferRenderResult = namedtuple('BufferRenderResult', 'content font_size')

class Buffer():

    def __init__(self, font_size=DEFAULT_FONT_SIZE):
        self.lines = {} # {name: content}
        self.font_size = font_size

    def update_row(self, name, content):
        self.lines[name] = content
    
    def clear(self):
        self.lines = {}

    def render(self):
        ret = ""
        for name in sorted(self.lines.keys()):
            ret += self.lines[name] + "\n"
        return BufferRenderResult(ret, self.font_size)


class Screen():

    def __init__(self):
        self.buffers = {} # {name : buffer}
        self.locations = {} # {name : location}
        self.lock = Lock()

    def register_buffer(self, buffer, location_str, font_size):
        with self.lock:
            location = Location(str(location_str).lower())
            
            for existing_name, existing_loc in self.locations.items():
                if buffer != existing_name and existing_loc == location:
                    raise RuntimeError("location already taken by another buffer")

            if self.buffers.get(buffer) == None:
                self.buffers[buffer] = Buffer(font_size=font_size)
                self.locations[buffer] = location
    
    def unregister_buffer(self, buffer):
        with self.lock:
            if buffer in self.buffers:
                del self.buffers[buffer]
                del self.locations[buffer]

    def update_row(self, buffer, row, content):
        with self.lock:
            if buffer not in self.buffers.keys():
                raise RuntimeError("attempted to write to unregistered buffer")
            self.buffers[buffer].update_row(row, content)

    def clear_buffer(self, buffer):
        with self.lock:
            self.buffers[buffer].clear()

    def reset(self):
        with self.lock:
            self.buffers = {}
            self.locations = {}

    def render(self):
        with self.lock:
            ret = {}
            for name, buffer in self.buffers.items():
                location = self.locations[name]
                ret[location] = buffer.render()
            return ret

# if __name__ == '__main__':
#     scr = Screen()
#     scr.register_buffer("nodes", Location.LowerLeft.value)
#     scr.update_row("nodes", "pi-1", "pi1: 192.168.234.32 Ready")
#     scr.update_row("nodes", "pi-4", "pi1: Offline")
#     scr.update_row("nodes", "pi-3", "pi1: DiskPressure")
#     scr.update_row("nodes", "pi-2", "pi1: MemPressure") 
#     print(scr.render())
