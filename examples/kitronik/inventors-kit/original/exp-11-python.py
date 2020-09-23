from microbit import *
import music
#set frequency and toneLength of the buzzer
frequency = 440
toneLength = 500

#Turn Green Light of traffic light on
#Turn Red light of crossing on
pin12.write_digital(1)
pin2.write_digital(1)
#When button A is pressed, the code will run the traffic light sequence from Go to Stop
#The crossing will turn green and sound a buzzer
#After the crossing is complete, the traffic light will start the sequence from Stop to Go
while True:
    if button_a.is_pressed():
        #Turn the traffic light green LED off and amber LED on
        pin12.write_digital(0)
        pin8.write_digital(1)
        sleep(1000) #wait 1 second
        #Turn the traffic light amber LED off and red LED on
        pin8.write_digital(0)
        pin1.write_digital(1)
        sleep(1000) #wait 1 second
        #Turn crossing LED's from red to green
        pin2.write_digital(0)
        pin16.write_digital(1)
        sleep(1000) #wait 1 second
        #Sound the buzzer for 8 beeps
        for loop in range(0, 9, 1):
            music.pitch(frequency, toneLength, pin0, True)
            sleep(200)
        #Turn crossing LED's from green to red
        pin2.write_digital(1)
        pin16.write_digital(0)
        sleep(1000) #wait 1 second
        #Set the traffic light red and amber lights both on
        pin1.write_digital(1)
        pin8.write_digital(1)
        sleep(1000) #wait 1 second
        #Set the traffic light to green
        pin1.write_digital(0)
        pin8.write_digital(0)
        pin12.write_digital(1)