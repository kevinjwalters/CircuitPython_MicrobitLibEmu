from microbit import *

Value = 0
Highest = 0

while True:
    Value = pin0.read_analog()
    if Value > Highest:
        Highest = Value

    if button_a.is_pressed():
        display.scroll(str(Highest))
