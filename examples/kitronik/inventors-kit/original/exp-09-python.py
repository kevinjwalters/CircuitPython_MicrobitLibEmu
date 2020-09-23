from microbit import *

CapVoltage = 0
Percentage = 0

while True:
    CapVoltage = pin0.read_analog()
    Percentage = CapVoltage / 10
    display.scroll(str(CapVoltage))

    if (Percentage > 25) and (Percentage <= 50):
        pin1.write_digital(1)
    elif (Percentage > 50) and (Percentage <= 75):
        pin1.write_digital(1)
        pin2.write_digital(1)
    elif (Percentage > 75) and (Percentage <= 90):
        pin1.write_digital(1)
        pin2.write_digital(1)
        pin8.write_digital(1)
    elif Percentage > 90:
        pin1.write_digital(1)
        pin2.write_digital(1)
        pin8.write_digital(1)
        pin12.write_digital(1)
    else:
        pin1.write_digital(0)
        pin2.write_digital(0)
        pin8.write_digital(0)
        pin12.write_digital(0)
