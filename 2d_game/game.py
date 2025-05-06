import pyglet
from pyglet import window, shapes
from DIPPID import SensorUDP

PORT = 5700
sensor = SensorUDP(PORT)

def handle_gravity(data):
    print('gravity: ' + str(data))
    update_position(data)

sensor.register_callback('gravity', handle_gravity)

WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800

win = window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)

square = shapes.Rectangle(400, 400, 200, 200, (0, 0, 255))

speed_x = 0
speed_y = 0

friction = 0.98

max_speed = 5.0

def update_velocity(gravity):
    global speed_x, speed_y

    speed_x += gravity['x'] * 0.1
    speed_y += gravity['y'] * 0.1

    speed_x *= friction
    speed_y *= friction

    if speed_x > max_speed:
        speed_x = max_speed
    elif speed_x < -max_speed:
        speed_x = -max_speed

    if speed_y > max_speed:
        speed_y = max_speed
    elif speed_y < -max_speed:
        speed_y = -max_speed


def update_position(gravity):
    global square

    update_velocity(gravity)

    square.x += speed_x
    square.y += speed_y

    if square.x < 0:
        square.x = 0
    elif square.x + square.width > WINDOW_WIDTH:
        square.x = WINDOW_WIDTH - square.width

    if square.y < 0:
        square.y = 0
    elif square.y + square.height > WINDOW_HEIGHT:
        square.y = WINDOW_HEIGHT - square.height

# Funktion zum Bewegen des Rechtecks
def move_rec(direction: int):
    if direction == 0 and square.x - 1 >= 0:  # Links
        square.x -= 1
    if direction == 1 and square.x + square.width + 1 <= WINDOW_WIDTH:  # Rechts
        square.x += 1
    if direction == 2 and square.y + square.height + 1 <= WINDOW_HEIGHT:  # Unten
        square.y += 1
    if direction == 3 and square.y - 1 >= 0:  # Oben
        square.y -= 1

@win.event
def on_key_press(symbol):
    if symbol == window.key.Q:  # Beendet das Programm, wenn Q gedrückt wird
        pyglet.app.exit()
    if symbol == window.key.LEFT:  # Bewege nach links
        move_rec(0)
    if symbol == window.key.RIGHT:  # Bewege nach rechts
        move_rec(1)
    if symbol == window.key.UP:  # Bewege nach oben
        move_rec(2)
    if symbol == window.key.DOWN:  # Bewege nach unten
        move_rec(3)

@win.event
def on_draw():
    win.clear()
    square.draw()

@win.event
def on_close():
    print("Fenster wird geschlossen – Sensor stoppen")
    win.close()

pyglet.app.run()
