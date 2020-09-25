### music.py v0.13
### A partial emulation of MicroPython micro:bit music library

### Tested with an Adafruit CLUE and CircuitPython and 5.3.1

### MIT License

### Copyright (c) 2020 Kevin J. Walters
### Copyright (c) 2015 Damien P. George and Nicholas H. Tollervey (music)

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

import time

import microbit


### TODO - remove when fixed
### https://github.com/adafruit/circuitpython/issues/3387
BUG_WORKAROUND = True


_ticks = 4  ### _ticks per beat
_bpm = 120
_duration = 4
_octave = 4

gate_off_time_ms = 10  ### 10ms


### The microbit music classical selection
### from https://github.com/micropython/micropython/blob/264d80c84e034541bd6e4b461bfece4443ffd0ac/ports/nrf/modules/music/musictunes.c  pylint: disable=line-too-long
DADADADUM = "r4:2 g g g eb:8 r:2 f f f d:8"
ENTERTAINER = "d4:1 d# e c5:2 e4:1 c5:2 e4:1 c5:3 c:1 d d# e c d e:2 b4:1 d5:2 c:4"
PRELUDE = ("c4:1 e g c5 e g4 c5 e c4 e g c5 e g4 c5 e c4 d g d5 f g4 d5 f c4 "
           "d g d5 f g4 d5 f b3 d4 g d5 f g4 d5 f b3 d4 g d5 f g4 d5 f c4 e g "
           "c5 e g4 c5 e c4 e g c5 e g4 c5 e")
ODE = "e4 e f g g f e d c c d e e:6 d:2 d:8 e:4 e f g g f e d c c d e d:6 c:2 c:8"
NYAN = ("f#5:2 g# c#:1 d#:2 b4:1 d5:1 c# b4:2 b c#5 d d:1 c# b4:1 c#5:1 d# f# "
        "g# d# f# c# d b4 c#5 b4 d#5:2 f# g#:1 d# f# c# d# b4 d5 d# d c# b4 "
        "c#5 d:2 b4:1 c#5 d# f# c# d c# b4 c#5:2 b4 c#5 b4 f#:1 g# b:2 f#:1 "
        "g# b c#5 d# b4 e5 d# e f# b4:2 b f#:1 g# b f# e5 d# c# b4 f# d# e "
        "f# b:2 f#:1 g# b:2 f#:1 g# b b c#5 d# b4 f# g# f# b:2 b:1 a# b f# "
        "g# b e5 d# e f# b4:2 c#5")
RINGTONE = "c4:1 d e:2 g d:1 e f:2 a e:1 f g:2 b c5:4"
FUNK = "c2:2 c d# c:1 f:2 c:1 f:2 f# g c c g c:1 f#:2 c:1 f#:2 f d#"
BLUES = ("c2:2 e g a a# a g e c2:2 e g a a# a g e f a c3 d d# d c a2 c2:2 e "
         "g a a# a g e g b d3 f f2 a c3 d# c2:2 e g e g f e d")
BIRTHDAY = ("c4:3 c:1 d:4 c:4 f e:8 c:3 c:1 d:4 c:4 g f:8 c:3 c:1 c5:4 a4 f "
            "e d a#:3 a#:1 a:4 f g f:8")
WEDDING = "c4:4 f:3 f:1 f:8 c:4 g:3 e:1 f:8 c:4 f:3 a:1 c5:4 a4:3 f:1 f:4 e:3 f:1 g:8"
FUNERAL = "c3:4 c:3 c:1 c:4 d#:3 d:1 d:3 c:1 c:3 b2:1 c3:4"
PUNCHLINE = "c4:3 g3:1 f# g g#:3 g r b c4"
PYTHON = ("d5:1 b4 r b b a# b g5 r d d r b4 c5 r c c r d e:5 c:1 a4 r a a "
          "g# a f#5 r e e r c b4 r b b r c5 d:5 d:1 b4 r b b a# b b5 r g "
          "g r d c# r a a r a a:5 g:1 f#:2 a:1 a g# a e:2 a:1 a g# a d r "
          "c# d r c# d:2 r:3")
BADDY = "c3:3 r d:2 d# r c r f#:8"
CHASE = ("a4:1 b c5 b4 a:2 r a:1 b c5 b4 a:2 r a:2 e5 d# e f e d# e b4:1 "
         "c5 d c b4:2 r b:1 c5 d c b4:2 r b:2 e5 d# e f e d# e")
BA_DING = "b5:1 e6:3"
WAWAWAWAA = "e3:3 r:1 d#:3 r:1 d:4 r:1 c#:8"
JUMP_UP = "c5:1 d e f g"
JUMP_DOWN = "g5:1 f e d c"
POWER_UP = "g4:1 c5 e g:2 e:1 g:3"
POWER_DOWN = "g5:1 d# c g4:2 b:1 c5:3"


def set_tempo(ticks=4, bpm=120):
    global _ticks, _bpm  ### pylint: disable=global-statement

    _ticks = ticks
    _bpm = bpm


def get_tempo():
    return (_ticks, _bpm)


### From C3 - A and B are above G
### Semitones   A   B   C   D   E   F   G
_NOTE_OFFSET = [21, 23, 12, 14, 16, 17, 19]

_MIDI_A4 = 69
_FREQ_A4 = 440.0


def _parseNote(note):
    """Converts the string encoded note form into frequency and duration in milliseconds.
       A rest is returned as note_freq of 0.
       """

    if not isinstance(note, str):
        raise ValueError("Bad note format")

    idx = 0
    try:
        char_uc = note[idx].upper()
        if char_uc == "R":
            note_st = None  ### signifies a rest
        else:
            note_st = _NOTE_OFFSET[ord(char_uc) - 65]  ### 65 is ord("A")
        idx += 1
    except IndexError:
        raise ValueError("Bad note format")

    sharpen = 0
    note_oct = _octave
    note__ticks = _ticks

    ### Optional #/b, then octave, then :tickduration
    try:
        if note[idx] == "#":
            sharpen = 1
            idx += 1
        elif note[idx] == "b":
            sharpen = -1
            idx += 1

        if "0" <= note[idx] <= "9":
            note_oct = int(note[idx])
            idx += 1

        if note[idx] == ":":
            idx += 1

        note__ticks = int(note[idx:])

    except (IndexError, ValueError):
        pass

    ### Convert to a frequency using A4 as the reference
    ### and counting semitones as MIDI note numbers
    if note_st is None:
        note_freq = 0
    else:
        ### 12 semitones in an octave
        note_freq = _FREQ_A4 * 2 ** (note_oct + (note_st + sharpen - _MIDI_A4) / 12.0)

    ### _bpm and _ticks are globals here, first number is ms in a minute
    note_dur = 60000 * note__ticks / _bpm / _ticks

    return (note_freq, note_dur)


def play(music, pin=microbit.pin0, wait=True, loop=False):
    if not wait:
        raise NotImplementedError("non-blocking play not implemented")

    if isinstance(music, str):
        ### Could check for tabs here...
        notes = music.split() if " " in music else (music,)
    else:
        notes = music

    while True:
        for note in notes:
            freq, dur_ms = _parseNote(note)
            if dur_ms > gate_off_time_ms:
                pitch(freq, dur_ms - gate_off_time_ms, pin=pin, music_off=False, desc=note)
                time.sleep(gate_off_time_ms / 1000.0)
            else:
                pitch(freq, dur_ms, pin=pin, music_off=False, desc=note)
        if not loop:
            break
    stop(pin)


def pitch(frequency, duration=-1, pin=microbit.pin0, wait=True, music_off=True, desc=None):
    """Play a note of specified frequency for duration or if duration is
       negative play it forever.
       A frequency of 0 can be used to silence the output
       but leave pin in music mode.
       """
    if not wait and duration > 0:
        raise NotImplementedError("non-blocking pitch not implemented")

    if frequency < 0:
        raise ValueError("invalid pitch")

    pin.music_on()
    pin.music_frequency(frequency, desc=desc)
    if BUG_WORKAROUND:
        time.sleep(0.008)
        pin.music_frequency(frequency, desc=desc)

    if wait and duration > 0:
        time.sleep(duration / 1000.0)
        stop(pin, music_off=music_off)


def stop(pin=microbit.pin0, music_off=True):
    """Silence the music output on the pin and turn off music mode."""
    pin.music_frequency(0)
    if music_off:
        pin.music_off()


def reset():
    global _ticks, _bpm, _duration, _octave  ### pylint: disable=global-statement

    _ticks = 4
    _bpm = 120
    _duration = 4
    _octave = 4


### Extras

def update():
    pass
