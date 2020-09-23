Introduction
============

This is a set of `CircuitPython <https://circuitpython.org/>`_ libraries
to emulate most of the functionality in two of 
the `BBC micro:bit <https://www.microbit.org/>`_'s MicroPython libraries
on an `Adafruit CLUE <https://learn.adafruit.com/adafruit-clue>`_.
The CLUE is a more advanced derivative of the micro:bit with a 
full colour 240x240 LCD screen, a compatible edge connector,
more sensors and a tiny onboard speaker.

This allows existing micro:bit code to run without modification on the CLUE.
It also provides visualisation of any values read from or written to the
GPIO pads/pins.

* `microbit <https://microbit-micropython.readthedocs.io/en/latest/micropython.html>`_ -
* `music <https://microbit-micropython.readthedocs.io/en/latest/music.html>`_ - 

An earlier version of the library can be seen in the video: `Adafruit CLUE running MicroPython code from Kitronik's Inventor's Kit using an emulation library <https://www.youtube.com/watch?v=0wWk_PiNFdY>`_ (YouTube).
The video features `experiment 3 <https://kitronik.co.uk/blogs/resources/inventors-kit-experiment-3-further-help>`_ from `Kitronik's Inventor's Kit for BBC micro:bit <https://kitronik.co.uk/products/inventors-kit-for-the-bbc-micro-bit>`_ running on the Adafruit CLUE.
The full set of MicroPython examples are replicated in this repository in `examples/kitronik <examples/kitronik/>`_ directory. 


Dependencies
=============

These libraries depend on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_
* `display_pin <https://github.com/kevinjwalters/CircuitPython_DisplayPin>`_


Usage Example
=============

The example below shows how the data from the pins is displayed in `enhanced` mode.
The code ultimately outputs PWM audio on `pad 0`,
reads an analogue voltage from `pad 1`
and writes that voltate to `pad 2` as a PWM signal.

.. code-block:: python

    from microbit import *
    import music

    display.mode = "text"
    display.scroll("Hello world...")
    display.show(Image.HAPPY)
    sleep(2000)
    display.mode = "basic"
    display.scroll("Basic mode...")
    display.mode = "small"
    display.show("Small mode!")
    display.mode = "enhanced"
    display.show("Enhanced = small + pins")
    sleep(2000)
    pin1.read_digital()
    sleep(2000)
    pin1.read_analog()
    sleep(2000)
    pin2.read_digital()
    sleep(2000)
    music.play(music.WAWAWAWAA, pin=speaker)
    while True:
        if button_a.is_pressed():
            music.play(music.WAWAWAWAA)
        if button_b.is_pressed():
            pin2.write_analog(pin1.read_analog())

