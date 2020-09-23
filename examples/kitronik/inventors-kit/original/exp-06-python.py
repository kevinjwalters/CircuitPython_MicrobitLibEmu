from microbit import *

import music

while True:
    if button_a.is_pressed():
        music.pitch(400,500)
