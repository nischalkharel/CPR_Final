import serial
import json
import time
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
from pathlib import Path

# Initialize I2C bus and PCA9685 at I2C address 0x40
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c, address=0x40)
pca.frequency = 50

# Initialize servo on channel 0 : THis is the gripper one (new one we added)
gripper_servo = servo.Servo(pca.channels[0], min_pulse=500, max_pulse=2500)

CLOSE_POS= 179
OPEN_POS = 168.2

gripper_servo.angle = CLOSE_POS