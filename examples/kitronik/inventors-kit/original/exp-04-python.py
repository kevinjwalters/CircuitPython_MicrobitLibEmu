from microbit import *

Duty = 0

while True:
    while Duty < 1023:
        pin0.write_analog(Duty)
        Duty += 1

    while Duty > 0:
        pin0.write_analog(Duty)
        Duty -= 1