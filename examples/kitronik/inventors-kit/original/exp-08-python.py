from microbit import *

import random

Degrees = 0
Difference = 0
Goal = random.randrange(360)
Smiley = Image("05050:"
               "05050:"
               "00000:"
               "50005:"
               "05550")

compass.calibrate()
display.show(Smiley)

while True:

    while button_a.is_pressed() == False:

        Degrees = compass.heading()
        Difference = abs(Goal - Degrees)
        pin0.write_digital(1)
        sleep(Difference * 5)
        pin0.write_digital(0)
        sleep(Difference * 5)

    if Difference < 15:
        display.scroll("Winner")
        Goal = random.randrange(360)

    else:
        display.scroll("Try Again")
        Goal = random.randrange(360)
