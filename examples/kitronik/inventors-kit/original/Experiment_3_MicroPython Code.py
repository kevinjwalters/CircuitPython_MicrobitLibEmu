from microbit import *



LightState = 0

Switch = 0



while True:

	if pin0.is_touched():

		Switch = 1

		if LightState == 0:

			LightState = 1

		else:

			LightState = 0



	if LightState == 1:

		pin2.write_analog(pin1.read_analog())

	else:

		pin2.write_digital(0)



	while Switch == 1:

		if pin0.is_touched() == 0:

			Switch = 0
