from microbit import *

while True:
    if button_a.is_pressed():
        display.show(Image.SMILE)
    elif button_b.is_pressed():
        display.scroll("Hello world")
    sleep(100)
