from microbit import *
import music

# This code can be seen running on an Adafruit CLUE
# on https://www.youtube.com/watch?v=3qBej1OPKVY

# Extra code to demo a few features of emulation library
display.mode = "text"
display.scroll("microbit")
display.mode = "basic"
display.scroll("library")
display.mode = "enhanced"
display.scroll("emulation on CLUE")
display.show(Image.SMILE)
sleep(2000)

display.show("Experiment 3 + music")
sleep(2000)
display.scroll("Dimming an LED")

_ = pin1.read_analog()
sleep(2000)
pin2.write_analog(pin1.read_analog())
sleep(2000)
_ = pin0.is_touched()
sleep(2000)
music.play(music.POWER_UP, pin4)

# Code is modified from original MicroPython code for 
# Kitronik Inventor's Kit experiment 3
# This one constantly reads from pin1 and writes to pin2
# and plays music on a right button (B) press
LightState = 0
Switch = 0
while True:
    if LightState == 1:
        pin2.write_analog(pin1.read_analog())
    else:
        pin2.write_digital(0)

    if pin0.is_touched():
        Switch = 1

        if LightState == 0:
            LightState = 1
        else:
            LightState = 0

        while Switch == 1:
            if pin0.is_touched() == 0:
                Switch = 0
    
    if button_b.was_pressed():
        music.play(music.ODE, pin4)
