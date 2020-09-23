from microbit import *

Red = 0
Green = 0
Blue = 0

Switch = 0

while True:
	pin0.write_analog(Green)
	pin1.write_analog(Red)
	pin2.write_analog(Blue)

	if pin8.read_digital() and (Green < 1020):
		Green += 10
		Switch = 1
	elif pin8.read_digital() and (Green >= 1020):
		Green = 0
		Switch = 1

	if pin12.read_digital() and (Red < 1020):
		Red += 10
		Switch = 1
	elif pin12.read_digital() and (Red >= 1020):
		Red = 0
		Switch = 1

	if pin16.read_digital() and (Blue < 1020):
		Blue += 10
		Switch = 1
	elif pin16.read_digital() and (Blue >= 1020):
		Blue = 0
		Switch = 1

	while Switch == 1:
		if (pin8.read_digital() == 0) and (pin12.read_digital() == 0) and (pin16.read_digital() == 0):
			Switch = 0
