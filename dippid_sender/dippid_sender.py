import socket
import time
import math
import random
import json

IP = '127.0.0.1'
PORT = 5700

# Sine frequency in Hz
X_FREQUENCY = 1
Y_FREQUENCY = 2
Z_FREQUENCY = 3

# Sine amplitude in g
X_AMPLITUDE = 3
Y_AMPLITUDE = 3
Z_AMPLITUDE = 3

# Data sending interval in s
SENDING_INTERVAL = 0.001

# Min and max interval for button state change in s
BUTTON_STATE_CHANGE_MIN_INTERVAL = 1
BUTTON_STATE_CHANGE_MAX_INTERVAL = 2

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

start_time = time.time()
button_state = 1
last_button_state_change = time.time()
button_state_change_interval = 1


def main():
    while True:
        acc_message = simulate_accelerometer()
        print(acc_message)
        sock.sendto(acc_message.encode(), (IP, PORT))

        button_1_message = simulate_button_1()
        print(button_1_message)
        sock.sendto(button_1_message.encode(), (IP, PORT))

        time.sleep(SENDING_INTERVAL)


def simulate_accelerometer():
    t = time.time() - start_time

    x = round(X_AMPLITUDE * math.sin(2 * math.pi * X_FREQUENCY * t), 10)
    y = round(Y_AMPLITUDE * math.sin(2 * math.pi * Y_FREQUENCY * t), 10)
    z = round(Z_AMPLITUDE * math.sin(2 * math.pi * Z_FREQUENCY * t), 10)

    acc_data = {"x": x, "y": y, "z": z}
    return '{"accelerometer" : ' + str(json.dumps(acc_data)) + '}'


def simulate_button_1():
    global last_button_state_change, button_state_change_interval, button_state

    if (time.time() - last_button_state_change > button_state_change_interval):
        if (button_state == 1):
            button_state = 0
        else:
            button_state = 1
        
        last_button_state_change = time.time()
        button_state_change_interval = random.uniform(BUTTON_STATE_CHANGE_MIN_INTERVAL, BUTTON_STATE_CHANGE_MAX_INTERVAL)

    return '{"button_1" : ' + str(button_state) + '}'


if __name__ == "__main__":
    main()