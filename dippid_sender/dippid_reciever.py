from DIPPID import SensorUDP

# use UPD (via WiFi) for communication
PORT = 5700
sensor = SensorUDP(PORT)

def handle_accelerometer(data):
    print('acc: ' + str(data))

def handle_button_1(data):
    print('button_1: ' + str(data))

sensor.register_callback('accelerometer', handle_accelerometer)
sensor.register_callback('button_1', handle_button_1)
