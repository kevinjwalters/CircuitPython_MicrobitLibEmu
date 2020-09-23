from microbit import *

LightsOn = Image("50505:"
                 "05550:"
                 "55555:"
                 "05550:"
                 "50505")
               
LightsOff = Image("55500:"
                  "05550:"
                  "00550:"
                  "05550:"
                  "55500")

while True:
    if pin0.read_analog() > 512:
        display.show(LightsOn)
    else:
        display.show(LightsOff)
