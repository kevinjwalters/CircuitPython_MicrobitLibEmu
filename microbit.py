### microbit.py v0.35
### A partial emulation of MicroPython micro:bit microbit library

### Tested with an Adafruit CLUE and CircuitPython and 5.3.1

### MIT License

### Copyright (c) 2020 Kevin J. Walters
### Copyright (c) 2016 British Broadcasting Corporation (pendolino3 font and symbols)

### Permission is hereby granted, free of charge, to any person obtaining a copy
### of this software and associated documentation files (the "Software"), to deal
### in the Software without restriction, including without limitation the rights
### to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
### copies of the Software, and to permit persons to whom the Software is
### furnished to do so, subject to the following conditions:

### The above copyright notice and this permission notice shall be included in all
### copies or substantial portions of the Software.

### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
### IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
### FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
### AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
### LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
### OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
### SOFTWARE.


import array
import time
import math
import collections

### Need to avoid this style of importing as this may be used with "import *"
##from displayio import Bitmap, Group, Palette, TileGrid
import supervisor
import displayio
import terminalio

import analogio
import digitalio
import touchio
import pulseio
import gamepad
import board
import audiopwmio
import audiocore

### For MicroBitDisplayViewText and
### MicroBitDisplayViewEnhanced
try:
    import adafruit_display_text.label
except ImportError:
    print("No display text library: adafruit_display_text")

### For accelerometer
try:
    import adafruit_lsm6ds.lsm6ds33
except ImportError:
    print("No accelerometer library: adafruit_lsm6ds")

### For magnetometer / compass
try:
    import adafruit_lis3mdl
except ImportError:
    print("No magnetometer library: adafruit_lis3mdl")

### For light level
try:
    import adafruit_apds9960.apds9960
except ImportError:
    print("No light sensor library: adafruit_apds9960")


### For MicroBitDisplayViewEnhanced
try:
    import display_pin
except ImportError:
    print("No library: display_pin")


STD_IMAGE_WIDTH = 5
STD_IMAGE_HEIGHT = 5

STD_FONT_WIDTH = 5
STD_FONT_HEIGHT = 5

### This is a MicroBitDisplay brightness level, the micro:bit LED display
### actually offers 0-255
MAX_BRIGHTNESS = 9

### Conversion factors
_MICRO_TO_NANO = 1000
_MILLI_TO_MICRO = 1000


def _makeSample(length):
    vol = 2 ** 15 - 1
    midpoint = 2 ** 15
    for s_idx in range(length):
        yield round(vol * math.sin(2 * math.pi * (s_idx / length)) + midpoint)


class ClueSpeaker:
    """This allow the CLUE's tiny onboard speaker to be used as the
       pin target for music.play(). """

    _CLUE_LOW_FREQ = 40.0


    def __init__(self):
        self._audio = None
        self._sample_len = 21
        sine_wave = array.array("H", _makeSample(self._sample_len))
        self._wave_sample = audiocore.RawSample(sine_wave)


    def music_on(self):
        if self._audio is None:
            self._audio = audiopwmio.PWMAudioOut(board.SPEAKER)


    def music_off(self):
        if self._audio.playing:
            self._audio.stop()

        ##self._audio.deinit()
        ##self._audio = None


    def music_frequency(self, frequency,
                        desc=None,  ### pylint: disable=unused-argument
                        ):
        ### stop() needs to be called on a CLUE / PWMAudioOut
        if self._audio.playing:
            self._audio.stop()

        ### 0 turns off audio but also don't allow low frequencies
        if frequency > self._CLUE_LOW_FREQ:
            self._wave_sample.sample_rate = round(self._sample_len * frequency)
            self._audio.play(self._wave_sample, loop=True)


def sleep(num_ms):
    """Sleep for num_ms milliseconds."""
    time.sleep(num_ms / 1000)


def running_time():
    """In milliseconds since power up."""
    return time.monotonic_ns() // 1000000


def panic(error_code):
    ### TODO - show or scroll??
    raise NotImplementedError


def reset():
    supervisor.reload()


### Some class to manage the calls to update()
### for MicroBitButton and MicroBitDisplay
class backGroundScheduler:
    def __init__(self):
        raise NotImplementedError


    def run(self):
        raise NotImplementedError


def _bytesToWidth(data, offset,
                  *,
                  width=5, height=5):
    """TODO. """
    char_width = 5  ### default for whitespace
    left_col = right_col = None

    ### Make a width "summary" row by mashing them all together with OR
    row_mash = 0x00
    for row in data[offset:offset + height]:
        row_mash |= row

    mask = 1 << (width - 1)
    for col_idx in range(width):
        if row_mash & mask:
            if left_col is None or col_idx < left_col:
                left_col = col_idx
            if right_col is None or col_idx > right_col:
                right_col = col_idx
        mask >>= 1

    ### The Pendolino3 font has 1 pixel wide characters in column 1
    ### not column 0
    if right_col is not None:
        char_width = right_col + 1

    return char_width


def _bytesToSeq(data, offset, seq_out,
                *,
                width=5, height=5, bg=0, fg=MAX_BRIGHTNESS):
    """TODO. """
    seq_idx = 0
    mask = 1 << (width - 1)
    for row in data[offset:offset + height]:
        row_data = row
        for _ in range(width):
            seq_out[seq_idx] = fg if row_data & mask else bg
            seq_idx += 1
            row_data <<= 1


def _bytesToCol(data, offset, column, seq_out,
                *,
                width=5, height=5, bg=0, fg=MAX_BRIGHTNESS):
    """TODO. """
    mask = 0x01 << (width - column - 1)
    for seq_idx, row in enumerate(data[offset:offset + height]):
        seq_out[seq_idx] = fg if row & mask else bg


class MicroBitFonts:
    ### This is from https://github.com/lancaster-university/microbit-dal/blob/master/source/core/MicroBitFont.cpp  pylint:disable=line-too-long
    ### 32 to 126, 5 bytes per char, 475 bytes total
    PENDOLINO3 = (
        b"\x00\x00\x00\x00\x00"
        b"\x08\x08\x08\x00\x08"
        b"\x0a\x4a\x40\x00\x00"
        b"\x0a\x5f\xea\x5f\xea"
        b"\x0e\xd9\x2e\xd3\x6e"
        b"\x19\x32\x44\x89\x33"
        b"\x0c\x92\x4c\x92\x4d"
        b"\x08\x08\x00\x00\x00"
        b"\x04\x88\x08\x08\x04"
        b"\x08\x04\x84\x84\x88"
        b"\x00\x0a\x44\x8a\x40"
        b"\x00\x04\x8e\xc4\x80"
        b"\x00\x00\x00\x04\x88"
        b"\x00\x00\x0e\xc0\x00"
        b"\x00\x00\x00\x08\x00"
        b"\x01\x22\x44\x88\x10"
        b"\x0c\x92\x52\x52\x4c"
        b"\x04\x8c\x84\x84\x8e"
        b"\x1c\x82\x4c\x90\x1e"
        b"\x1e\xc2\x44\x92\x4c"
        b"\x06\xca\x52\x5f\xe2"
        b"\x1f\xf0\x1e\xc1\x3e"
        b"\x02\x44\x8e\xd1\x2e"
        b"\x1f\xe2\x44\x88\x10"
        b"\x0e\xd1\x2e\xd1\x2e"
        b"\x0e\xd1\x2e\xc4\x88"
        b"\x00\x08\x00\x08\x00"
        b"\x00\x04\x80\x04\x88"
        b"\x02\x44\x88\x04\x82"
        b"\x00\x0e\xc0\x0e\xc0"
        b"\x08\x04\x82\x44\x88"
        b"\x0e\xd1\x26\xc0\x04"
        b"\x0e\xd1\x35\xb3\x6c"
        b"\x0c\x92\x5e\xd2\x52"
        b"\x1c\x92\x5c\x92\x5c"
        b"\x0e\xd0\x10\x10\x0e"
        b"\x1c\x92\x52\x52\x5c"
        b"\x1e\xd0\x1c\x90\x1e"
        b"\x1e\xd0\x1c\x90\x10"
        b"\x0e\xd0\x13\x71\x2e"
        b"\x12\x52\x5e\xd2\x52"
        b"\x1c\x88\x08\x08\x1c"
        b"\x1f\xe2\x42\x52\x4c"
        b"\x12\x54\x98\x14\x92"
        b"\x10\x10\x10\x10\x1e"
        b"\x11\x3b\x75\xb1\x31"
        b"\x11\x39\x35\xb3\x71"
        b"\x0c\x92\x52\x52\x4c"
        b"\x1c\x92\x5c\x90\x10"
        b"\x0c\x92\x52\x4c\x86"
        b"\x1c\x92\x5c\x92\x51"
        b"\x0e\xd0\x0c\x82\x5c"
        b"\x1f\xe4\x84\x84\x84"
        b"\x12\x52\x52\x52\x4c"
        b"\x11\x31\x31\x2a\x44"
        b"\x11\x31\x35\xbb\x71"
        b"\x12\x52\x4c\x92\x52"
        b"\x11\x2a\x44\x84\x84"
        b"\x1e\xc4\x88\x10\x1e"
        b"\x0e\xc8\x08\x08\x0e"
        b"\x10\x08\x04\x82\x41"
        b"\x0e\xc2\x42\x42\x4e"
        b"\x04\x8a\x40\x00\x00"
        b"\x00\x00\x00\x00\x1f"
        b"\x08\x04\x80\x00\x00"
        b"\x00\x0e\xd2\x52\x4f"
        b"\x10\x10\x1c\x92\x5c"
        b"\x00\x0e\xd0\x10\x0e"
        b"\x02\x42\x4e\xd2\x4e"
        b"\x0c\x92\x5c\x90\x0e"
        b"\x06\xc8\x1c\x88\x08"
        b"\x0e\xd2\x4e\xc2\x4c"
        b"\x10\x10\x1c\x92\x52"
        b"\x08\x00\x08\x08\x08"
        b"\x02\x40\x02\x42\x4c"
        b"\x10\x14\x98\x14\x92"
        b"\x08\x08\x08\x08\x06"
        b"\x00\x1b\x75\xb1\x31"
        b"\x00\x1c\x92\x52\x52"
        b"\x00\x0c\x92\x52\x4c"
        b"\x00\x1c\x92\x5c\x90"
        b"\x00\x0e\xd2\x4e\xc2"
        b"\x00\x0e\xd0\x10\x10"
        b"\x00\x06\xc8\x04\x98"
        b"\x08\x08\x0e\xc8\x07"
        b"\x00\x12\x52\x52\x4f"
        b"\x00\x11\x31\x2a\x44"
        b"\x00\x11\x31\x35\xbb"
        b"\x00\x12\x4c\x8c\x92"
        b"\x00\x11\x2a\x44\x98"
        b"\x00\x1e\xc4\x88\x1e"
        b"\x06\xc4\x8c\x84\x86"
        b"\x08\x08\x08\x08\x08"
        b"\x18\x08\x0c\x88\x18"
        b"\x00\x00\x0c\x83\x60"
    )

    STANDARD = PENDOLINO3

    ### PENDOLINO3_WIDTHS and STANDARD_WIDTHS attributes are created and
    ### added after the class has been created

### Can't do these inside class for some reason
MicroBitFonts.PENDOLINO3_WIDTHS = tuple(_bytesToWidth(MicroBitFonts.PENDOLINO3,
                                                      offset, width=5, height=5)
                                        for offset in range(0, len(MicroBitFonts.PENDOLINO3), 5))
MicroBitFonts.STANDARD_WIDTHS = MicroBitFonts.PENDOLINO3_WIDTHS


### https://microbit-micropython.readthedocs.io/en/latest/microbit.html
###

### This is the actual type of microbit.display
class MicroBitDisplay():
    def __init__(self, display=None,  ### pylint: disable=redefined-outer-name
                 mode="basic",
                 *,
                 led_rows=5,
                 led_cols=5,
                 font=MicroBitFonts.STANDARD,
                 font_widths=MicroBitFonts.STANDARD_WIDTHS,
                 light_sensor=None,
                 exception=False,
                 display_show=True):
        """disp  active display
           mode "small", "enhanced", "basic"
           """
        self.display = display
        self._mode = None  ### will be set by _initView
        self.exception = exception
        self._display_show = display_show
        self.font = font
        self.font_widths = font_widths
        self.view = None  ### will be set by _initView
        self.view_update_count = 0

        self._initView(display, mode,
                       led_rows=led_rows, led_cols=led_cols)

        self._light_sensor = light_sensor
        if light_sensor:
            light_sensor.enable_color = True
        self._showing = None
        self._scrolling = None
        self._led_rows = led_rows
        self._led_cols = led_cols
        self._leds = led_rows * led_cols * [0]

        self._viewUpdate(None, None)
        ### Place the graphics on screen
        if display_show and display:
            display.show(self.view.group)


    def deinint(self):
        display.view.deinint()
        if self._display_show and self.display:
            display.show(None)


    def _initView(self, display,  ### pylint: disable=redefined-outer-name
                  mode,
                  *,
                  led_rows=5, led_cols=5):
        self._mode = mode
        self.view_update_count = 0
        self.view = MicroBitDisplayView.makeView(mode,
                                                 display=display,
                                                 led_rows=led_rows, led_cols=led_cols)


    def _viewUpdate(self, x_chg, y_chg, text=None, text_idx=None):
        self.view.update(self._leds, x_chg, y_chg)

        if text is not None and self.view_update_count == 0:
            try:
                self.view.updateString(text)
            except AttributeError:
                pass  ### Optional method

        if text_idx is not None:
            try:
                self.view.updateStringPos(text_idx)
            except AttributeError:
                pass  ### Optional method

        self.view_update_count += 1


    def get_pixel(self, x, y):
        return self._leds[x + y * self._led_cols]


    def set_pixel(self, x, y, value):
        if not 0 <= value <= MAX_BRIGHTNESS:
            raise ValueError("value must be 0 to 9 inclusive")

        idx = x + y * self._led_cols
        old_value = self._leds[idx]
        if value != old_value:
            self._leds[idx] = value
            self._viewUpdate(x, y)


    def clear(self):
        self._leds = self._led_rows * self._led_cols * [0]
        self.view_update_count = 0
        self._viewUpdate(None, None, text="")


    ### wait=False runs in the background - don't think we can do that
    ### or maybe could have an .update function with programmer
    ### committing to call that regularly (check adafruit_debouncer)
    def show(self, value, delay=400,
             *,
             wait=True, loop=False, clear=False):

        if not wait:
            raise NotImplementedError

        self.view_update_count = 0

        ### value can be all sorts of things including an image
        if isinstance(value, MicroBitImage):
            ### TODO clear text
            self.showImage(value)
            return

        show_seq = str(value) if isinstance(value, (int, float)) else value
        if len(show_seq) == 1:
            ### TODO clear text
            self.showItem(show_seq[0], seq=show_seq)
            return  ### Impl. on microbit has no delay for "a" or 5

        elem_delay_s = delay / 1000.0
        ### TODO _showing needs to have loop and delay in too
        self._showing = enumerate(show_seq)
        while True:
            try:
                idx, elem = next(self._showing)
                self.showItem(elem, seq=show_seq, seq_idx=idx)
                time.sleep(elem_delay_s)
            except StopIteration:
                if loop:
                    self._showing = enumerate(show_seq)
                else:
                    break
        self._showing = None
        if clear:
            self.clear()


    def showItem(self, item, seq=None, seq_idx=None):
        """Show a character or Image."""

        if isinstance(item, MicroBitImage):
            self.showImage(item)
        elif isinstance(item, str) and len(item) == 1:
            self.showCharacter(item, full_text=seq, text_idx=seq_idx)
        else:
            raise ValueError("Must be MicroBitImage or single character string.")


    def showCharacter(self, char, *, bg=0, fg=MAX_BRIGHTNESS,
                      full_text=None, text_idx=None):
        """Show a character."""

        ### TODO - loads of font specific knowledge is burnt into this code
        x = ord(char[0])
        if not 32 <= x <= 126:
            x = ord('?')

        ### Calculate offset into font data
        f_idx = (x - 32) * 5  ### TODO
        _bytesToSeq(self.font, f_idx, self._leds,
                    width=self._led_cols, height=self._led_rows, fg=fg, bg=bg)
        self._viewUpdate(None, None, text=full_text, text_idx=text_idx)


    def showImage(self, image):
        """This shows the image as it is but does not update it if image changes.
           TODO - check how microbit behaves with a 3x3 - does it blank the border???
           """

        src_idx = idx = 0
        for _ in range(min(self._led_rows, image.height())):
            for col_idx in range(min(self._led_cols, image.width())):
                self._leds[idx + col_idx] = image.pixels[src_idx + col_idx]
            src_idx += image.width()
            idx += self._led_cols
        self._viewUpdate(None, None)


    ### This scrolls the text one pixel (column) at a time
    def scroll(self, value, delay=150, *, wait=True, loop=False, monospace=False):

        if not wait:
            raise NotImplementedError

        ### Clear screen
        self.clear()
        self.view_update_count = 0  ### This must be zeroed after clear()

        scroll = {"text": value + " ",
                  "char_col": 0,
                  "idx" : 0,
                  "loop": loop,
                  "delay": delay / 1000.0}
        self._scrolling = scroll

        text_len = len(scroll["text"])
        new_col = [0] * self._led_rows
        while True:
            text_idx = scroll["idx"]
            if text_idx >= text_len:
                if scroll["loop"]:
                    scroll["idx"] = 0
                else:
                    break
                text_idx = 0

            char = scroll["text"][text_idx]

            ### TODO - yet another 5x5 font specific value below
            width = 5 if monospace else self._getCharWidth(char)

            ### Add the thin column of whitespace if gone beyond last column
            if scroll["char_col"] == width:
                new_col = [0] * self._led_rows
            else:
                self._getCharCol(char,
                                 scroll["char_col"],
                                 new_col)

            self._shiftLeftOne(new_column=new_col)
            self._viewUpdate(None, None, text=scroll["text"], text_idx=text_idx)
            scroll["char_col"] += 1
            if scroll["char_col"] > width:
                scroll["char_col"] = 0
                scroll["idx"] += 1
            time.sleep(scroll["delay"])

        self._scrolling = None


    def _shiftLeftOne(self, new_column=None):

        last_row = self._led_rows - 1
        col_idx = 0
        if new_column is None:
            new_column = [0] * self._led_rows

        for idx in range(len(self._leds)):
            if idx % self._led_cols == last_row:
                self._leds[idx] = new_column[col_idx]
                col_idx += 1
            else:
                self._leds[idx] = self._leds[idx + 1]


    def _getCharCol(self, char, column, seq_out, *, bg=0, fg=MAX_BRIGHTNESS):
        ### TODO - loads of font specific knowledge is burnt into this code
        ### TODO - cut and paste with showCharacter
        x = ord(char[0])
        if not 32 <= x <= 126:
            x = ord('?')

        ### Calculate offset into font data
        f_idx = (x - 32) * 5  ### TODO
        _bytesToCol(self.font, f_idx, column, seq_out,
                    width=self._led_cols, height=self._led_rows, fg=fg, bg=bg)


    def _getCharWidth(self, char):
        ### TODO - loads of font specific knowledge is burnt into this code
        ### TODO - cut and paste with showCharacter
        x = ord(char[0])
        if not 32 <= x <= 126:
            x = ord('?')

        ### Calculate offset into font data
        f_idx = (x - 32)  ### TODO
        return self.font_widths[f_idx]


    def tickUpdate(self):
        """Returns True if an update took place, False if complete and
           None if no update is needed."""
        if not self._showing and not self._scrolling:
            return None

        ### Work out where timing goes - here or in caller
        ### caller may make more sense as simple form of scheduling
        ### requesting a rate

        ### do something
        ### this may need a timer, i.e. if something is due to happen in 50ms then wait for it
        ### otherwise return
        still_updating = True

        return still_updating


    def on(self):
        self._nopOrE()


    def off(self):
        self._nopOrE()


    def _nopOrE(self):
        if self.exception:
            raise NotImplementedError


    ### Rather clever implementation on micro:bit although there is a visible flicker
    def read_light_level(self):
        """ TODO - this is 0-255, reads 30 on a micro:bit at my desk"""
        if self._light_sensor:
            ### r,g,b,clear comes back from the APDS9960
            return self._light_sensor.color_data[3] // 256
        else:
            raise RuntimeError("No light sensor configured - missing library?")


    @property
    def group(self):
        return self.view.group


    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, data):
        if self._mode != data:
            if self.view:
                self.view.deinit()
            self._initView(self.display, data,
                           led_rows=self._led_rows,
                           led_cols=self._led_cols)
            self._viewUpdate(None, None)
            ### Place the graphics on screen
            if self._display_show and self.display:
                self.display.show(self.view.group)


class MicroBitDisplayView:
    ### These are set after the sub-classes are defined
    _VIEW_NAMES = []
    _VIEW_CLASSES = []


    def __init__(self, mode, display=None,  ### pylint: disable=redefined-outer-name
                 ):
        if type(self) == MicroBitDisplayView:  ### pylint: disable=unidiomatic-typecheck
            raise TypeError("No MicroBitDisplayView for you - this must be subclassed")

        self._mode = None  ### Must be set for property mode to work
        self._display = display
        self._display_width = 240 if display is None else display.width
        self._display_height = 240 if display is None else display.height
        self._levels = 10

        self.mode = mode  ### property setting


    @classmethod
    def makeView(cls, view_name,
                 *, display=None,  ### pylint: disable=redefined-outer-name
                 led_rows=5, led_cols=5):
        ### TODO - could replace this with a proper class registration scheme
        try:
            view_class = cls._VIEW_CLASSES[cls._VIEW_NAMES.index(view_name)]
        except ValueError:
            raise ValueError("Unknown view name")

        view = view_class(display=display, led_rows=led_rows, led_cols=led_cols)
        return view


    def deinit(self):
        pass


    @property
    def mode(self):
        return self._mode

    @mode.setter
    def mode(self, data):
        if self._mode is not None and self._mode != data:
            self.deinit()


class MicroBitDisplayViewBasic(MicroBitDisplayView):
    def __init__(self,
                 mode="basic", display=None,  ### pylint: disable=redefined-outer-name
                 *, led_rows=5, led_cols=5, scale=None, group_extras=0):
        ### pylint: disable=too-many-locals
        super().__init__(mode=mode,
                         display=display)

        red_shades = self._levels
        led_bitmap = displayio.Bitmap(led_cols, led_rows, red_shades)
        self._led_bitmap = led_bitmap
        self._led_count = led_cols * led_rows

        ### Make the number of shades of red required for display
        palette = displayio.Palette(red_shades)
        for idx in range(red_shades):
            red_level = round(idx * 255 / (red_shades - 1))
            palette[idx] = (red_level, 0, 0)

        led_tg = displayio.TileGrid(led_bitmap, pixel_shader=palette)
        self._led_tg = led_tg

        min_display_dim = min(self._display_width, self._display_height)
        if scale is None:
            ### 48x scale for 5x5
            text_scale = min_display_dim // max(led_cols, led_rows)
            x_pos = 0
        else:
            text_scale = scale
            x_pos = (min_display_dim - scale * led_cols) // 2

        led_group = displayio.Group(max_size=1, scale=text_scale)
        led_group.x = x_pos
        led_group.append(led_tg)
        self._led_group = led_group

        if group_extras:
            disp_group = displayio.Group(max_size=1 + group_extras)
            disp_group.append(led_group)
            self.group = disp_group
        else:
            self.group = led_group  ### A public attribute


    def update(self, leds, x_chg, y_chg):
        ### TODO - respect the change hints

        ## self.led_bitmap[:] = leds  ### NotImplementedError: Slices not supported

        ##af_mode = self._display.auto_refresh if self._display else None

        ##if af_mode:
        ##    self._display.auto_refresh = False

        for idx in range(min(len(leds), self._led_count)):
            self._led_bitmap[idx] = leds[idx]  ### trusting these are 0-9

        ##if af_mode:
        ##    self._display.auto_refresh = af_mode


class MicroBitDisplayViewText(MicroBitDisplayView):

    PIXEL_TEXT = "II"  ### The text used for each pixel
    VERY_DARK_GREY = 0x080808

    def __init__(self, mode="text", display=None,  ### pylint: disable=redefined-outer-name
                 *, led_rows=5, led_cols=5, scale=3):
        ### pylint: disable=too-many-locals
        super().__init__(mode=mode,
                         display=display)

        self._dio_font = terminalio.FONT

        red_shades = self._levels
        ### initialise with level 0, a dim background colour
        self._colours = [self.VERY_DARK_GREY] * self._levels
        ### then replace 1 onwards with red of varying intensity
        for idx in range(1, red_shades):
            red_level = round(idx * 255 / (red_shades - 1))
            self._colours[idx] = red_level << 16  ### shift past G and B

        text_group = displayio.Group(max_size=led_rows * led_cols,
                                     scale=scale)
        text_y_pos = 4  ### TODO - calc these
        text_y_spacing = 17
        text_x_spacing = 17
        for _ in range(led_rows):
            text_x_pos = 0
            for _ in range(led_cols):
                text_cell = adafruit_display_text.label.Label(text=self.PIXEL_TEXT,
                                                              font=self._dio_font,
                                                              color=self._colours[0])
                text_cell.x = text_x_pos
                text_cell.y = text_y_pos
                text_group.append(text_cell)
                text_x_pos += text_x_spacing
            text_y_pos += text_y_spacing

        self._led_text = text_group
        self.group = text_group  ### A public attribute


    def update(self, leds, x_chg, y_chg):
        ### TODO - respect the change hints

        ## self.led_bitmap[:] = leds  ### NotImplementedError: Slices not supported

        ##af_mode = self._display.auto_refresh if self._display else None

        ##if af_mode:
        ##    self._display.auto_refresh = False

        for idx in range(min(len(leds), len(self._led_text))):
            ### trusting these are 0-9
            new_intensity = self._colours[leds[idx]]
            if self._led_text[idx].color != new_intensity:
                self._led_text[idx].color = new_intensity

        ##if af_mode:
        ##    self._display.auto_refresh = af_mode


class MicroBitDisplayViewStandard(MicroBitDisplayView):
    """TODO - what was I planning here for Standard view????"""
    def __init__(self, led_rows=5, led_cols=5):
        super().__init__()
        raise NotImplementedError("TODO!!!")


    def update(self, leds, pos_x, pos_y):
        raise NotImplementedError("TODO!!!")


class MicroBitDisplayViewSmall(MicroBitDisplayViewBasic):
    def __init__(self, mode="small", display=None,  ### pylint: disable=redefined-outer-name
                 *, led_rows=5, led_cols=5):
        super().__init__(mode=mode,
                         display=display,
                         led_rows=led_rows, led_cols=led_cols,
                         scale=24)


def _pin_write_digital_cb(pin_obj, view, value):
    view.updatePin(pin_obj.pin_name, "write_digital", value)


def _pin_read_digital_cb(pin_obj, view, value):
    view.updatePin(pin_obj.pin_name, "read_digital", value)


def _pin_write_analog_cb(pin_obj, view, value):
    view.updatePin(pin_obj.pin_name, "write_analog", value)


def _pin_read_analog_cb(pin_obj, view, value):
    view.updatePin(pin_obj.pin_name, "read_analog", value)


def _pin_touch_cb(pin_obj, view, value):
    view.updatePin(pin_obj.pin_name, "touch", value)


def _pin_music_frequency_cb(pin_obj, view, value_and_desc):
    view.updatePin(pin_obj.pin_name, "music_frequency", value_and_desc)


### Maybe text could overlap in different colour?
### to preserve the pixel writing with wider text on the screen
class MicroBitDisplayViewEnhanced(MicroBitDisplayViewBasic):
    ### Something unclear going on with staticmethods here so punted them
    ### outside - .__func__ cannot be used in CP on staticmethods
    _HOOKS = (("write_digital", _pin_write_digital_cb),
              ("read_digital", _pin_read_digital_cb),
              ("write_analog", _pin_write_analog_cb),
              ("read_analog", _pin_read_analog_cb),
              ("touch", _pin_touch_cb),
              ("music_frequency", _pin_music_frequency_cb),
              )

    _LARGE_PIN = (230, 62)
    _MED_PIN   = (230, 36)
    _SMALL_PIN = (110, 24)

    def __init__(self, mode="enhanced", display=None,  ### pylint: disable=redefined-outer-name
                 *, led_rows=5, led_cols=5):
        super().__init__(mode=mode,
                         display=display,
                         led_rows=led_rows, led_cols=led_cols,
                         scale=24,
                         group_extras=2 + 1)

        self._text = None
        self._text_idx = None
        self._text_pane_font = terminalio.FONT
        self._text_pane_char_width = 20  ### TODO - calc this
        self._text_pane = adafruit_display_text.label.Label(text="",
                                                            max_glyphs=self._text_pane_char_width,
                                                            font=self._text_pane_font,
                                                            color=0xff0000,
                                                            scale=2)
        self._text_pane_highlight_char = \
            adafruit_display_text.label.Label(text="",
                                              max_glyphs=1,
                                              font=self._text_pane_font,
                                              color=0xc0c0c0,
                                              scale=2)
        self._text_pane.y = 138  ### TODO - set properly
        self._text_pane_highlight_char.y = self._text_pane.y
        self.group.append(self._text_pane)
        self.group.append(self._text_pane_highlight_char)

        for method_name, func in self._HOOKS:
            PinManager.addHookPins(method_name, func, self)

        self._max_pins = 6  ### 3 rows of 2 columns = 6
        self._pin_data = collections.OrderedDict()
        self._pin_group = displayio.Group(max_size=self._max_pins)
        self._pin_group.y = 156
        self._pinarea_width = self._display_width
        self._pinarea_height = self._display_width - 156  ### TODO
        self.group.append(self._pin_group)


    def deinit(self):
        super().deinit()
        for method_name, func in self._HOOKS:
            _ = PinManager.removeHookPins(method_name, func, self)


    def updateString(self, text):
        self._text = text
        if text == "":
            self._text_pane.text = ""
            self._text_pane_highlight_char.text = ""
        elif len(text) <= self._text_pane_char_width:
            self._text_pane.text = text
        else:
            self._text_pane.text = text[:self._text_pane_char_width]
            ### TODO jump scroll feature


    def updateStringPos(self, text_idx):
        if self._text_idx != text_idx and self._text is not None:
            self._text_idx = text_idx
            self._text_pane_highlight_char.text = self._text[text_idx]
            self._text_pane_highlight_char.x = 2 * 6 * text_idx  ### TODO


    def _pinSize(self, num):
        if num == 0:
            return (None, None)
        elif num == 1:
            return self._LARGE_PIN
        elif num == 2:
            return self._MED_PIN
        else:
            return self._SMALL_PIN


    def _adjustPinPosAndSize(self):
        """A very basic attempt at grid layout with dynamic sizing for up to six pins."""
        ### pylint: disable=too-many-locals
        pins_shown = len(self._pin_data)
        if pins_shown == 0:
            return
        pin_disp_size = self._pinSize(pins_shown)

        rows = 2 if pins_shown == 2 else (pins_shown + 1) // 2
        cols = 1 if pins_shown <= 2 else 2
        pin_spacing = self._pinarea_height / rows  ### float not int

        new_pin_width, new_pin_height = pin_disp_size
        for pin_idx, (pin_name, pin_entry) in enumerate(self._pin_data.items()):
            if pin_entry[1] != pin_disp_size:
                pin_entry[1] = pin_disp_size
                ### Create a replacement DisplayPin with the new dimensions
                ### preserving value from the existing object
                new_pin_obj = display_pin.DisplayPin(*pin_entry[0],
                                                     width=pin_entry[1][0],
                                                     height=pin_entry[1][1],
                                                     value=pin_entry[2].value)
                pin_entry[2] = new_pin_obj
                self._pin_group[pin_idx] = new_pin_obj.group

            ### Update only if changed to minimise any work displayio might do
            new_x = 0 if cols == 1 else (self._display_width - new_pin_width) * (pin_idx & 0x01)
            row = pin_idx if cols == 1 else (pin_idx & 0xfe) >> 1
            new_y = round(pin_spacing * row)
            if pin_entry[2].group.x != new_x:
                pin_entry[2].group.x = new_x
            if pin_entry[2].group.y != new_y:
                pin_entry[2].group.y = new_y


    def updatePin(self, pin_name, pin_type, value):
        ##print("updatePin", pin_name, pin_type, value)

        ### Disable auto_refresh to reduce flicker and increase efficiency
        ### this reduces a pwm sweep of range(0, 1024, 4) from 40s to 19s
        restore_refresh = None
        if self._display:
            restore_refresh = self._display.auto_refresh
            if restore_refresh:
                self._display.auto_refresh = False

        pin_entry = self._pin_data.get(pin_name)
        if pin_entry is None:
            ### pin is not yet on display, add it if it fits
            next_idx = len(self._pin_data)
            if next_idx >= self._max_pins:
                return  ### Run out of space!

            pin_width, pin_height = self._pinSize(next_idx + 1)
            pin_obj = display_pin.DisplayPin(pin_name, pin_type, "MP",
                                             width=pin_width, height=pin_height)
            pin_entry = [(pin_name, pin_type, "MP"),
                         (pin_width, pin_height),
                         pin_obj]
            self._pin_data[pin_name] = pin_entry
            self._pin_group.append(pin_obj.group)
            self._adjustPinPosAndSize()

        elif pin_entry[0][2] != pin_type:
            ### pin already on display but mode needs changing
            pin_width, pin_height = pin_entry[1]
            pin_obj = display_pin.DisplayPin(pin_name, pin_type, "MP",
                                             width=pin_width, height=pin_height)
            pin_entry = [(pin_name, pin_type, "MP"),
                         (pin_width, pin_height),
                         pin_obj]
            self._pin_data[pin_name] = pin_entry
            grp_idx = tuple(self._pin_data.keys()).index(pin_name)
            self._pin_group[grp_idx] = pin_obj.group
            self._adjustPinPosAndSize()  ### Position still needs setting

        pin_entry[2].value = value

        if restore_refresh:
            self._display.auto_refresh = restore_refresh

### pylint: disable=protected-access
MicroBitDisplayView._VIEW_NAMES = ("basic",
                                   "standard",
                                   "small",
                                   "text",
                                   "enhanced",
                                  )
MicroBitDisplayView._VIEW_CLASSES = (MicroBitDisplayViewBasic,
                                     MicroBitDisplayViewStandard,
                                     MicroBitDisplayViewSmall,
                                     MicroBitDisplayViewText,
                                     MicroBitDisplayViewEnhanced,
                                    )
### pylint: enable=protected-access


SYMBOL_BYTES = (
    b"\x0a\x1f\x1f\x0e\x04"
    b"\x00\x0a\x0e\x04\x00"
    b"\x00\x0a\x00\x11\x0e"
    b"\x00\x00\x00\x11\x0e"
    b"\x00\x0a\x00\x0e\x11"
    b"\x00\x0a\x00\x0a\x15"
    b"\x11\x0a\x00\x1f\x15"
    b"\x00\x1b\x00\x0e\x00"
    b"\x0a\x00\x04\x0a\x04"
    b"\x11\x00\x1f\x05\x07"
    b"\x1f\x1b\x00\x0a\x0e"
    b"\x0a\x00\x02\x04\x08"
    b"\x00\x01\x02\x14\x08"
    b"\x11\x0a\x04\x0a\x11"
    b"\x04\x04\x04\x00\x00"
    b"\x02\x02\x04\x00\x00"
    b"\x00\x03\x04\x00\x00"
    b"\x00\x00\x07\x00\x00"
    b"\x00\x00\x04\x03\x00"
    b"\x00\x00\x04\x02\x02"
    b"\x00\x00\x04\x04\x04"
    b"\x00\x00\x04\x08\x08"
    b"\x00\x00\x04\x18\x00"
    b"\x00\x00\x1c\x00\x00"
    b"\x00\x18\x04\x00\x00"
    b"\x08\x08\x04\x00\x00"
    b"\x04\x0e\x15\x04\x04"
    b"\x07\x03\x05\x08\x10"
    b"\x04\x02\x1f\x02\x04"
    b"\x10\x08\x05\x03\x07"
    b"\x04\x04\x15\x0e\x04"
    b"\x01\x02\x14\x18\x1c"
    b"\x04\x08\x1f\x08\x04"
    b"\x1c\x18\x14\x02\x01"
    b"\x00\x04\x0a\x1f\x00"
    b"\x10\x18\x14\x12\x1f"
    b"\x0a\x15\x0a\x15\x0a"
    b"\x04\x0a\x11\x0a\x04"
    b"\x00\x04\x0a\x04\x00"
    b"\x1f\x11\x11\x11\x1f"
    b"\x00\x0e\x0a\x0e\x00"
    b"\x14\x14\x1e\x1a\x1e"
    b"\x11\x11\x1f\x0e\x04"
    b"\x04\x04\x04\x1c\x1c"
    b"\x04\x06\x05\x1c\x1c"
    b"\x0f\x09\x09\x1b\x1b"
    b"\x15\x15\x1f\x04\x04"
    b"\x04\x0e\x04\x0e\x1f"
    b"\x0f\x1a\x1c\x1e\x0f"
    b"\x04\x0e\x1b\x0e\x04"
    b"\x1b\x1f\x0e\x0e\x0e"
    b"\x03\x03\x1f\x1f\x0a"
    b"\x0c\x1c\x0f\x0e\x00"
    b"\x04\x0e\x1f\x0e\x0a"
    b"\x00\x0e\x1f\x0a\x00"
    b"\x1b\x1f\x04\x1f\x1b"
    b"\x04\x1f\x04\x0a\x11"
    b"\x1f\x15\x1f\x1f\x15"
    b"\x04\x04\x04\x0e\x04"
    b"\x18\x08\x08\x0e\x0a"
    b"\x0e\x15\x1f\x0e\x0e"
    b"\x0e\x1f\x04\x14\x0c"
    b"\x18\x1b\x0a\x0e\x00"
)


SYMBOL_NAMES = (
    "HEART",
    "HEART_SMALL",
    "HAPPY",
    "SMILE",
    "SAD",
    "CONFUSED",
    "ANGRY",
    "ASLEEP",
    "SURPRISED",
    "SILLY",
    "FABULOUS",
    "MEH",
    "YES",
    "NO",
    "CLOCK12",
    "CLOCK1",
    "CLOCK2",
    "CLOCK3",
    "CLOCK4",
    "CLOCK5",
    "CLOCK6",
    "CLOCK7",
    "CLOCK8",
    "CLOCK9",
    "CLOCK10",
    "CLOCK11",
    "ARROW_N",
    "ARROW_NE",
    "ARROW_E",
    "ARROW_SE",
    "ARROW_S",
    "ARROW_SW",
    "ARROW_W",
    "ARROW_NW",
    "TRIANGLE",
    "TRIANGLE_LEFT",
    "CHESSBOARD",
    "DIAMOND",
    "DIAMOND_SMALL",
    "SQUARE",
    "SQUARE_SMALL",
    "RABBIT ",
    "COW ",
    "MUSIC_CROTCHET",
    "MUSIC_QUAVER",
    "MUSIC_QUAVERS",
    "PITCHFORK",
    "XMAS",
    "PACMAN",
    "TARGET",
    "TSHIRT",
    "ROLLERSKATE",
    "DUCK",
    "HOUSE",
    "TORTOISE",
    "BUTTERFLY",
    "STICKFIGURE",
    "GHOST",
    "SWORD",
    "GIRAFFE",
    "SKULL",
    "UMBRELLA",
    "SNAKE",
)


### Predefined are all in
### https://github.com/bbcmicrobit/micropython/blob/master/source/microbit/microbitconstimage.cpp

class MicroBitImage():

    def __init__(self, *args):
        if len(args) == 0:
            self._width = STD_IMAGE_WIDTH
            self._height = STD_IMAGE_HEIGHT
            self.pixels = self._width * self._height * [0]
        elif len(args) == 1:
            ### Based on a string (dimensions based on data,
            ### largest width is width, trailing padding on short rows)

            if isinstance(args[0], bytes):
                self._width = STD_IMAGE_WIDTH
                self._height = STD_IMAGE_HEIGHT
                self.pixels = self._width * self._height * [0]
                ### This defaults to 5x5
                _bytesToSeq(args[0], 0, self.pixels)

            else:
                rows = tuple(r for r in args[0].split(":") if len(r))
                self._width = max(len(row) for row in rows)
                self._height = len(rows)
                self.pixels = self._width * self._height * [0]
                idx = 0
                for row in rows:
                    self.pixels[idx:idx + len(row)] = [int(r) for r in row]
                    idx += self._width

        elif len(args) == 2:
            ### blank n x m
            raise NotImplementedError  ### TODO

        elif len(args) == 3:
            ### n x m based on string
            raise NotImplementedError  ### TODO

        self._readonly = False


    def width(self):
        return self._width


    def height(self):
        return self._height


### Add the standard images as class attributes
for im_idx, im_name in enumerate(SYMBOL_NAMES):
    setattr(MicroBitImage, im_name,
            MicroBitImage(SYMBOL_BYTES[im_idx * 5:im_idx * 5 + 5]))

### Add the standard lists of images, clocks and arrows
MicroBitImage.ALL_CLOCKS = ( MicroBitImage.CLOCK12, MicroBitImage.CLOCK1,
                             MicroBitImage.CLOCK2,  MicroBitImage.CLOCK3,
                             MicroBitImage.CLOCK4, MicroBitImage.CLOCK5,
                             MicroBitImage.CLOCK6, MicroBitImage.CLOCK7,
                             MicroBitImage.CLOCK8, MicroBitImage.CLOCK9,
                             MicroBitImage.CLOCK10, MicroBitImage.CLOCK11 )

MicroBitImage.ALL_ARROWS = ( MicroBitImage.ARROW_N, MicroBitImage.ARROW_NE,
                             MicroBitImage.ARROW_E, MicroBitImage.ARROW_SE,
                             MicroBitImage.ARROW_S, MicroBitImage.ARROW_SW,
                             MicroBitImage.ARROW_W, MicroBitImage.ARROW_NW )


### Save some memory as these are no longer needed
del SYMBOL_BYTES, SYMBOL_NAMES


class MicroBitButtonMonitor():
    """A monitor for multiple buttons to enable queries for presses in the past.
       All of the users of this class must create an instance of it
       before was_pressed() is called.
       """

    _gamepad = None

    buttons = 0
    button_callback = {}
    button_index = {}
    button_digin = []

    _pressed_unread = 0x00   ### tracks pressed buttons for was_pressed()

    def __init__(self, name, digin, call_back=None):
        self.name = name
        cls = type(self)
        cls.button_digin.append(digin)
        cls.button_callback[name] = call_back
        cls.button_index[name] = cls.buttons
        cls.buttons += 1


    @classmethod
    def _gamepad_init(cls):
        cls._gamepad = gamepad.GamePad(*cls.button_digin)


    @classmethod
    def _updatePressedUnread(cls, value):
        cls._pressed_unread = value


    def was_pressed(self):
        if self._gamepad is None:
            self._gamepad_init()

        all_pressed = self._gamepad.get_pressed()
        combined_pressed = all_pressed | self._pressed_unread

        ### Do callbacks for all buttons but only set pressed for
        ### the button associated with this instance
        button_idx = self.button_index.get(self.name)
        pressed = False
        mask = 0x01
        for idx in range(self.buttons):
            if combined_pressed & mask:
                try:
                    self.button_callback[self.name](self.name, mask, combined_pressed)
                except (KeyError, TypeError):
                    pass
                if idx == button_idx:
                    pressed = True
            mask <<= 1

        ### Note the buttons pressed which are not this one
        self._updatePressedUnread(combined_pressed & ~(0x01 << button_idx))

        return pressed


### For button_a (left) and button_b (right)
class MicroBitButton():
    def __init__(self, pin_obj, name=None):
        self._pin_obj = pin_obj

        ### Buttons needs to be set to PULL_UP to work
        pin_obj.read_digital()
        pin_obj.set_pull(pin_obj.PULL_UP)

        button_name = str(pin_obj.pin).split(".")[-1] if name is None else name

        self._monitor = MicroBitButtonMonitor(button_name, pin_obj.get_diginout())


    def is_pressed(self):
        """Returns True if button is currently pressed, otherwise False.
           """
        pressed = self._pin_obj.read_digital()
        return not bool(pressed)


    def was_pressed(self):
        return self._monitor.was_pressed()

    ### This seems to be number of presses since last call to get_presses()
    ### May not be possible
    def get_presses(self):
        raise NotImplementedError


### https://microbit-micropython.readthedocs.io/en/latest/pin.html#classes

### The pull mode for a pin is automatically configured when the pin changes
### to an input mode. Input modes are when you call read_analog / read_digital
### / is_touched. The default pull mode for these is, respectively, NO_PULL,
### PULL_DOWN, PULL_UP. Calling set_pull will configure the pin to be in
### read_digital mode with the given pull mode.

### The micro:bit has external weak (10M) pull-ups fitted on
### pins 0, 1 and 2 only, in order for the touch sensing to work.
### There are also external (10k) pull-ups fitted on pins 5 and 11, in order
### for buttons A and B to work.

### https://github.com/bbcmicrobit/micropython/blob/e10a5ffdbaf1cc40a82a665d79343c7b6b78d13b/tests/test_pins.py    pylint:disable=line-too-long

### CircuitPython 5.3.x bug in transitioning from input to output for analogue
### https://github.com/adafruit/circuitpython/issues/3313

###    The I2C pins are on on the same P19/P20 (we like to use D19/D20 naming)
###    The SPI pins are on on the same P13-P15 (we like to use D13-D15 naming)
###    There are analog pins on P0 (Arduino A2), P1 (Arduino A3),
###      P2 (Arduino A4), P3 (Arduino A5), P4 (Arduino A6), P10 (Arduino A7)
###      just like the micro:bit
###    There are additional analog pins on D12 (Arduino A0) and P16 (Arduino A1)
###    Button A and B are on the same P5 and P11 pins
###    Since we don't have an LED matrix, you can use P3, P4, P6, P7, P9, P10, P11
###      without worrying about conflicting with an LED grid

### get_mode is peculiar
### https://forum.micropython.org/viewtopic.php?f=2&t=8933

### pin5 pin6 pin7 pin8 pin9 pin11 pin12 pin13 pin14 pin15 pin16 pin19 pin20
class MicroBitDigitalPin():

    ### These are instance attributes in microbit with these values
    NO_PULL = 0
    PULL_DOWN = 1
    PULL_UP = 3

    def _nop(self):
        pass


    def __init__(self, pin):
        self.pin = pin          ### CircuitPython Pin
        self.pin_name = str(pin).split(".")[-1]
        self._diginout = None   ### CircuitPython DigitalInOut
        self._pull = None
        self._mode = "unused"
        self._deinit = self._nop  ### This is the method used to turn-off previous use
        self._post_hooks = {}


    def addHook(self, method_name, when, cb, cb_args):
        if when == "post":
            callbacks = self._post_hooks.get(method_name)
            if callbacks is None:
                self._post_hooks[method_name] = [(cb, cb_args)]
            else:
                self._post_hooks[method_name].append((cb, cb_args))


    def removeHook(self, method_name, when, cb, cb_args):
        count = 0
        if when == "post":
            callbacks = self._post_hooks.get(method_name)
            if callbacks is not None:
                len_before_rm = len(callbacks)
                self._post_hooks[method_name] = [c for c in callbacks if c[0] is not cb]
                count = len_before_rm - len(self._post_hooks[method_name])
        return count


    def _runHooks(self, method_name, when, args):
        if when == "post":
            callbacks = self._post_hooks.get(method_name)
            results = []
            for cb, cbargs in (callbacks if callbacks is not None else []):  ### pylint: disable=superfluous-parens
                try:
                    rv = cb(self, cbargs, args)
                except Exception as ex:  ### pylint: disable=broad-except
                    rv = ex
                results.append(rv)
            return results
        else:
            raise ValueError("Only post is implemented")


    def _digitalDeinit(self, mark_unused=False):
        if self._diginout:
            self._diginout.deinit()
            self._diginout = None
            self._pull = None

        if mark_unused:
            self._mode = "unused"
            self._deinit = self._nop


    def _digital(self, direction, pull=None):
        if direction == "in":
            if pull is not None:
                self._pull = pull
            if self._pull is None:
                self._pull = self.PULL_DOWN

            if self._diginout:
                self._diginout.switch_to_input(self._get_cp_pull())
            else:
                self._diginout = digitalio.DigitalInOut(self.pin)
                self._diginout.pull = self._get_cp_pull()

            self._mode = "read_digital"
            self._deinit = self._digitalDeinit

        elif direction == "out":
            if self._diginout is None:
                self._diginout = digitalio.DigitalInOut(self.pin)
                self._pull = None
                self._mode = "write_digital"
                self._deinit = self._digitalDeinit

            self._diginout.switch_to_output()


    def set_pull(self, pull):
        if not pull in (self.NO_PULL,
                        self.PULL_DOWN,
                        self.PULL_UP):
            raise ValueError("invalid pull")
        if self._mode != "read_digital":
            self._deinit()
            self._digital("in")

        self._digital("in", pull=pull)


    def get_pull(self):
        return self._pull


    def _get_cp_pull(self):
        """Translate from MicroPython pull state to CircuitPython."""
        if self._pull == self.NO_PULL:
            return None
        elif self._pull == self.PULL_DOWN:
            return digitalio.Pull.DOWN
        elif self._pull == self.PULL_UP:
            return digitalio.Pull.UP

        raise ValueError("_pull illegal value: " + str(self._pull))


    def read_digital(self):
        if self._mode != "read_digital":
            self._deinit()
            self._digital("in")
        rv = 1 if self._diginout.value else 0
        self._runHooks("read_digital", "post", rv)
        return rv


    def write_digital(self, value):
        if value not in (0, 1):
            raise ValueError("value must be 0 or 1")
        if self._mode != "write_digital":
            self._deinit()
            self._digital("out")
        self._diginout.value = bool(value)
        self._runHooks("write_digital", "post", value)


    def get_mode(self):
        return self._mode


    def get_diginout(self):
        return self._diginout


### pin10, pin3, pin4
class MicroBitAnalogDigitalPin(MicroBitDigitalPin):
    DEFAULT_FREQUENCY = 50

    ### Use a short duty cycle similar to micro:bit's as this appears to
    ### have useful harmonics making things more audible on piezos
    MUSIC_DC_CP = 9000

    def __init__(self, pin):      ## , direction="in")
        super().__init__(pin)     ## , direction="in", mode="digital")
        self._pwm = None  ### needs to be variable frequency
        self._analogin = None
        self._frequency = self.DEFAULT_FREQUENCY  ## Looks like 20ms period on my iffy scope


    def _deinitAnalog(self, mark_unused=False):
        if self._pwm:
            self._pwm.deinit()
            self._pwm = None
        if self._analogin:
            self._analogin.deinit()
            self._analogin = None

        if mark_unused:
            self._mode = "unused"
            self._deinit = self._nop


    def _analog(self, direction):
        if direction == "in":
            if self._pwm:
                self._pwm.deinit()   ### check this exists! TODO
                self._pwm = None
            if self._analogin is None:
                self._analogin = analogio.AnalogIn(self.pin)
            self._mode = "read_analog"  ### microbit is unused for read_analog()
            self._deinit = self._deinitAnalog

        elif direction in ("out", "music_out"):
            if self._analogin:
                self._analogin.deinit()
                self._analogin = None
            if self._pwm is None:
                self._frequency = self.DEFAULT_FREQUENCY
                ### TODO - review fixed use of variable_frequency=True here
                ### as it's probably dramatically lowering number of PWM outputs
                self._pwm = pulseio.PWMOut(self.pin,
                                           frequency=self._frequency,
                                           duty_cycle=0,
                                           variable_frequency=True)
            ### microbit mode is unused for write_analog(0)
            ### https://forum.micropython.org/viewtopic.php?t=8933&p=50377
            self._mode = "write_analog" if direction == "out" else "music"
            self._deinit = self._deinitAnalog


    def read_analog(self):
        if self._mode != "read_analog":
            self._deinit()
            self._analog("in")

        rv = self._analogin.value >> 6  ### convert to 0-1023
        self._runHooks("read_analog", "post", rv)
        return rv


    def write_analog(self, value):
        if not 0 <= value <= 1023:
            raise ValueError("value must be between 0 and 1023")

        if self._mode != "write_analog":
            self._deinit()
            self._analog("out")
        ### Max value will be 65472
        ### micro:bit on a scope isn't 100% d/c for 1023
        self._pwm.duty_cycle = value << 6
        self._runHooks("write_analog", "post", value)
    ### One period/frequency to rule them all :(
    ### https://github.com/bbcmicrobit/micropython/issues/644


    def set_analog_period(self, period):
        self.set_analog_period_microseconds(period * _MILLI_TO_MICRO)


    def set_analog_period_microseconds(self, period):
        ### Change it if set but do not turn PWM on yet if not set
        self._frequency = round(1e6 / period)
        if self._pwm:
            self._pwm.frequency = self._frequency


    def music_on(self):
        if self._mode != "music":
            self._analog("music_out")


    def music_off(self):
        if self._mode == "music":
            self._deinit()
            self._mode = "unused"


    def music_frequency(self, frequency, desc=None):
        ### Ensure in music mode
        if self._mode != "music":
            raise ValueError("music_on() must be executed to change mode")

        if frequency == 0:
            self._pwm.duty_cycle = 0
        else:
            self._pwm.frequency = round(frequency)
            if self._pwm.duty_cycle == 0:
                self._pwm.duty_cycle = self.MUSIC_DC_CP

        self._runHooks("music_frequency", "post", (frequency, desc))


### pin0, pin1, pin2
class MicroBitTouchPin(MicroBitAnalogDigitalPin):

    _MICROBIT_GND_TOUCH = 5

    def __init__(self, pin):   ### , direction="in"):
        super().__init__(pin)
        self._touchpad = None


    def _deinitTouch(self, mark_unused=False):
        if self._touchpad:
            self._touchpad.deinit()
            self._touchpad = None

        if mark_unused:
            self._mode = "unused"
            self._deinit = self._nop


    def _touch(self):
        if self._touchpad is None:
            self._touchpad = touchio.TouchIn(self.pin)
            self._mode = "touch"
            self._deinit = self._deinitTouch


    def is_touched(self):
        if self._mode != "touch":
            self._deinit()
            self._touch()

        ### The micro:bit touch works differently and some circuits
        ### may briefly ground the pin to simulate touch
        rv = (self._touchpad.value
              or self._touchpad.raw_value <= self._MICROBIT_GND_TOUCH)

        self._runHooks("touch", "post", rv)
        return rv


class MicroBitAccelerometer:
    """Units are milli-gravity where gravity is 9.80665ms-2."""

    ### This undoes the scaling within LSM6DS class
    _ACCEL_TO_MILLI_G = 101.9716


    def __init__(self, i2c=board.I2C()):
        self._i2c = i2c
        self._accel = None


    def _init(self):
        try:
            self._accel = adafruit_lsm6ds.lsm6ds33.LSM6DS33(self._i2c)
        except NameError:
            print("ERROR:", "missing adafruit_lsm6ds library on CIRCUITPY")
            raise


    def get_x(self):
        if self._accel is None:
            self._init()
        return round(self._accel.acceleration[0] * self._ACCEL_TO_MILLI_G)


    def get_y(self):
        if self._accel is None:
            self._init()
        return round(self._accel.acceleration[1] * self._ACCEL_TO_MILLI_G)


    def get_z(self):
        if self._accel is None:
            self._init()
        return round(self._accel.acceleration[2] * self._ACCEL_TO_MILLI_G)


    def get_values(self):
        if self._accel is None:
            self._init()
        return tuple(round(av * self._ACCEL_TO_MILLI_G) for av in self._accel.acceleration)


    def current_gesture(self):
        raise NotImplementedError


    def is_gesture(self):
        raise NotImplementedError


    def was_gesture(self):
        raise NotImplementedError


    def get_gestures(self):
        raise NotImplementedError


    @property
    def accel(self):
        """Return the accelerometer."""
        return self._accel


### https://github.com/bbcmicrobit/micropython/blob/master/source/microbit/microbitcompass.cpp    pylint:disable=line-too-long
### https://github.com/lancaster-university/microbit-dal/blob/master/source/drivers/MicroBitCompass.cpp    pylint:disable=line-too-long

def _scToNed(x, y, z):
    return (y, x, -z)


def _accelToPitchRoll(x, y, z):
    roll = math.atan2(x, -z)
    pitch = math.atan2(y, (x * math.sin(roll) - z * math.cos(roll)))
    return (pitch, roll)


### TODO - micro:bit calibrates if not calibrated when methods
### are called that return data
### ponder storage using nvm module for eeprom-like storage
### could use magic identifer number a la microbit and NaN for NA numbers
class MicroBitCompass:
    def __init__(self, i2c=board.I2C(), accel=None):
        self._i2c = i2c
        self._accel = accel
        self._mag = None
        self._calibrated = False
        self._tilt_compensation = False


    def _init(self):
        try:
            self._mag = adafruit_lis3mdl.LIS3MDL(self._i2c)
        except NameError:
            print("ERROR:", "missing adafruit_lis3mdl library on CIRCUITPY")
            raise


    def _basicBearing(self):
        ### micro:bit facing south gives (5.41797, -26.1172, 40.3125)
        ### 4th CLUE gives (2.8062, -94.8845, 117.743)
        ### suggesting ENU coords
        m_x, m_y, _ = self._mag.magnetic
        bearing = round(math.degrees(math.atan2(m_x, m_y)))

        if bearing < 0:
            bearing += 360

        return bearing


    ### This is based on MicroBitCompass::tiltCompensatedBearing() in
    ### https://github.com/lancaster-university/microbit-dal/blob/master/source/drivers/MicroBitCompass.cpp    pylint:disable=line-too-long
    def _tiltCompensatedBearing(self):
        """This does not work well if the device is accelerating or
           subject to any vibration.
        """
        pitch, roll = _accelToPitchRoll(*self._accel.acceleration)
        m_x_ned, m_y_ned, m_z_ned = _scToNed(*self._mag.magnetic)

        sinPhi = math.sin(roll)
        cosPhi = math.cos(roll)
        sinTheta = math.sin(pitch)
        cosTheta = math.cos(pitch)

        ### Calculate the tilt compensated bearing, and convert to degrees.
        bearing_rad = math.atan2((0.0
                                  - m_y_ned * cosPhi
                                  + m_z_ned * sinPhi),
                                 (m_x_ned * cosTheta
                                  + m_y_ned * sinTheta * sinPhi
                                  + m_z_ned * sinTheta * cosPhi))

        bearing = round(math.degrees(bearing_rad))

        if bearing < 0:
            bearing += 360

        print("TODO - UNTESTED AND LIKELY NOT TO WORK")
        print("TODO - UNTESTED AND REALLY LIKELY NOT TO WORK")
        return bearing


    def heading(self):
        """TODO"""
        if self._mag is None:
            self._init()

        if self._accel and self._tilt_compensation:
            return self._tiltCompensatedBearing()

        return self._basicBearing()


    def is_calibrated(self):
        if self._mag is None:
            self._init()

        return self._calibrated


    ### TODO - got an external implementation of this but need to
    ### tidy it up and work out how to glue it in
    def calibrate(self):
        if self._mag is None:
            self._init()


    def get_x(self):
        """Gives the reading of the magnetic field strength on the x axis
           in nano tesla, as a positive or negative integer,
            depending on the direction of the field."""
        if self._mag is None:
            self._init()

        x, _, _ = self._mag.magnetic
        return round(x * _MICRO_TO_NANO)


    def get_y(self):
        """Gives the reading of the magnetic field strength on the y axis
           in nano tesla, as a positive or negative integer,
            depending on the direction of the field."""
        if self._mag is None:
            self._init()

        _, y, _ = self._mag.magnetic
        return round(y * _MICRO_TO_NANO)


    def get_z(self):
        """Gives the reading of the magnetic field strength on the z axis
           in nano tesla, as a positive or negative integer,
            depending on the direction of the field."""
        if self._mag is None:
            self._init()

        _, _, z = self._mag.magnetic
        return round(z * _MICRO_TO_NANO)


    def get_field_strength(self):
        if self._mag is None:
            self._init()

        x, y, z = self._mag.magnetic
        return round(math.sqrt(x * x + y * y + z * z) * _MICRO_TO_NANO)


class PinManager:
    pins = []


    @classmethod
    def addHookPins(cls, method_name, cb, cb_args):
        for pin in cls.pins:
            pin.addHook(method_name, "post", cb, cb_args)


    @classmethod
    def removeHookPins(cls, method_name, cb, cb_args):
        count = 0
        for pin in cls.pins:
            count += pin.removeHook(method_name, "post", cb, cb_args)
        return count


### TODO - ponder some sort of background tick thing to call any periodic stuff
### what's a reasonable target frequency? 50 Hz?
### 1) display update
### 2) button update (gamepad looks like it does a good job of this as clue object uses that)


### Class aliases
Image = MicroBitImage


### microbit summary - 3 is high, 1 is low
### pin5 and pin11 are buttons, pin0 is also high for some reason
### pin0, pin1 and pin2 had been used here - if no code has run
### then they will be unused

# pin0 3
# pin1 1
# pin2 1
# pin3 Pin 3 in display mode
# pin4 Pin 4 in display mode
# pin5 3
# pin6 Pin 6 in display mode
# pin7 Pin 7 in display mode
# pin8 Pin 8 in unused mode
# pin9 Pin 9 in display mode
# pin10 Pin 10 in display mode
# pin11 3
# pin12 Pin 12 in unused mode
# pin13 Pin 13 in unused mode
# pin14 Pin 14 in unused mode
# pin15 Pin 15 in unused mode
# pin16 Pin 16 in unused mode
# pin17 name 'pin17' is not defined
# pin18 name 'pin18' is not defined
# pin19 Pin 19 in i2c mode
# pin20 Pin 20 in i2c mode


### Instances
### pins 5 and 11 are connected to button A and B and
### match the micro:bit's default PULL_UP state
pin0 = MicroBitTouchPin(board.P0)
pin1 = MicroBitTouchPin(board.P1)
pin2 = MicroBitTouchPin(board.P2)
PinManager.pins.extend([pin0, pin1, pin2])

pin3 = MicroBitAnalogDigitalPin(board.P3)
pin4 = MicroBitAnalogDigitalPin(board.P4)
pin10 = MicroBitAnalogDigitalPin(board.P10)
PinManager.pins.extend([pin3, pin4, pin10])

pin5 = MicroBitDigitalPin(board.P5)
pin6 = MicroBitDigitalPin(board.P6)
pin7 = MicroBitDigitalPin(board.P7)
pin8 = MicroBitDigitalPin(board.P8)
pin9 = MicroBitDigitalPin(board.P9)
pin11 = MicroBitDigitalPin(board.P11)
pin12 = MicroBitDigitalPin(board.P12)  ### CLUE can do (pwm) analog on this pin
pin13 = MicroBitDigitalPin(board.P13)
pin14 = MicroBitDigitalPin(board.P14)
pin15 = MicroBitDigitalPin(board.P15)
pin16 = MicroBitDigitalPin(board.P16)  ### CLUE can do (pwm) analog on this pin
pin19 = MicroBitDigitalPin(board.P19)
pin20 = MicroBitDigitalPin(board.P20)
PinManager.pins.extend([pin5, pin6, pin7, pin8,
                        pin9, pin11, pin12, pin13,
                        pin14, pin15, pin16, pin19,
                        pin20])

### The pins will be set to PULL_UP by MicroBitButton
button_a = MicroBitButton(pin5)
button_b = MicroBitButton(pin11)


try:
    apds9660_sensor = adafruit_apds9960.apds9960.APDS9960(board.I2C())
except NameError:
    apds9660_sensor = None

### This needs to be created after pins and PinManager setup and buttons
display = MicroBitDisplay(board.DISPLAY,
                          "enhanced",
                          light_sensor=apds9660_sensor)
del apds9660_sensor

### These have some lazy initialisation to stop the instantiation
### blowing up if the relevant CircuitPython libraries aren't present in /lib
accelerometer = MicroBitAccelerometer()
compass = MicroBitCompass(accel=accelerometer.accel)

### 20k sound system in 5x5mm
speaker = ClueSpeaker()
