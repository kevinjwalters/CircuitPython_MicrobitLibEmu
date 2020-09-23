from microbit import *
import random

item = 0
while True:
    #The code will run when button A is pressed
    if button_a.is_pressed():
        item = random.randint(1, 6) #First a random number is picked between 1 and 6
        #After selecting a number, all LED control lines are set low and turned off
        pin0.write_digital(0)
        pin1.write_digital(0)
        pin2.write_digital(0)
        pin8.write_digital(0)
        if item == 1:   #depending which number is selected, turn on the required pins
            pin0.write_digital(1)
        elif item == 2:
            pin1.write_digital(1)
        elif item == 3:
            pin0.write_digital(1)
            pin1.write_digital(1)
        elif item == 4:
            pin1.write_digital(1)
            pin8.write_digital(1)
        elif item == 5:
            pin0.write_digital(1)
            pin1.write_digital(1)
            pin8.write_digital(1)
        elif item == 6:
            pin1.write_digital(1)
            pin2.write_digital(1)
            pin8.write_digital(1)