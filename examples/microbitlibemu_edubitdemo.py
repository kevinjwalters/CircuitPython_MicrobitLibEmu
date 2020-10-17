# A very simple demonstration of the Cytron Edu:bit

from microbit import *
import music

# This code can be seen running on an Adafruit CLUE
# on https://www.youtube.com/watch?v=u6KseA54gzI

display.mode = "text"
display.show(Image.SMILE)
sleep(1000)
display.show(Image.HAPPY)
music.play(music.POWER_UP)
sleep(1000)

display.mode = "enhanced"
display.scroll(" CLUE with Edu:bit ")
sleep(2000)

while True:
    p1 = pin1.read_analog()   # Sound Bit
    p2 = pin2.read_analog()   # Potentio Bit
    p8 = pin8.read_digital()  # IR Bit

    # 3 LEDs R, G, B
    pin14.write_digital(int(p1 > 200))
    pin15.write_digital(int(p2 > 512))
    pin16.write_digital(p8)
