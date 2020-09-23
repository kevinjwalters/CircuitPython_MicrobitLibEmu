from microbit import *

YTilt = 0

while True:
    YTilt = accelerometer.get_y()
    if YTilt <= 0:
        YTilt = 0
        pin0.write_analog(YTilt)
    else:
        pin0.write_analog(YTilt)
