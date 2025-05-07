import pyglet
from pyglet import window, shapes
from DIPPID import SensorUDP
import random, math, time

# KONSTANTEN ##############################################################################

# Fenster
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
FRAMERATE = 60

# Bewegungssteuerung
GRAVITY_CONTROL_AXIS = 'y'
MAX_GRAVITY_THRESHOLD = 8 # 9.81 => Handy 90 Grad gedreht => Player am Bildschirmand
MAX_PLAYER_SPEED = 200.0
PORT = 5700 # UDP Port für DIPPID-Kommunikation

# Player
MAX_PLAYER_HEALTH = 3
PLAYER_SIZE = 50
PLAYER_COLOR = (0, 0, 255)
START_POS_X = WINDOW_WIDTH / 2 - PLAYER_SIZE / 2
START_POS_Y = PLAYER_SIZE

# Projektile allgemein (Items und Enemies)
PROJECTILE_SIZE = 25
MIN_PROJECTILE_SPEED = 50.0
MAX_PROJECTILE_SPEED = 100.0
SPEED_INCREASE_PER_MS = 0.01
SPAWN_INTERVAL_DECREASE_PER_MS = 0.01

# Items
ITEM_TYPES = ["heart", "points", "slowdown", "shrink_projectiles", "shrink_player"]
FAIL_TO_CATCH_ITEM_HURT = True
ITEM_EFFECT_DURATION = 10
MAX_ITEM_SPAWN_INTERVAL = 10
ITEM_COLOR = (0, 255, 0)
POINT_ITEM_WORTH = 10
SLOWDOWN_ITEM_SPEED_PERCENTAGE = 0.5
SHRINK_PROJECTILES_ITEM_SIZE_PERCENTAGE = 0.5
SHRINK_PLAYER_ITEM_SIZE_PERCENTAGE = 0.5

# Enemies
MAX_NO_ENEMIES = ((WINDOW_WIDTH - PLAYER_SIZE * 2) / PROJECTILE_SIZE) * 2 # Maximale Anzahl Enemies am Feld
POINTS_PER_AVOIDED_ENEMY = 1
MAX_ENEMY_SPAWN_INTERVAL = 3
ENEMY_COLOR = (255, 0, 255)

# GUI
WHITE = (255, 255, 255)
RED = (255, 0, 0)


# "OBJEKT"-KLASSEN #########################################################################

class Player:
    def __init__(self, x, y):
        self.health = MAX_PLAYER_HEALTH # Start mit vollen Leben
        self.x = x
        self.y = y
        self.sprite = shapes.Circle(self.x, self.y, PLAYER_SIZE, color = PLAYER_COLOR)

    def update_position(self):
        self.x = self.x_pos_by_gravity()
        self.sprite.x = self.x

    def x_pos_by_gravity(self):
        gravity_axis_value = gravity[GRAVITY_CONTROL_AXIS]
        gravity_axis_value_percent = gravity_axis_value / MAX_GRAVITY_THRESHOLD
        gravity_axis_value_percent = max(-1, min(1, gravity_axis_value_percent))
        distance_from_center = (WINDOW_WIDTH / 2 - PLAYER_SIZE) * gravity_axis_value_percent
        return WINDOW_WIDTH / 2 + distance_from_center
    

class Projectile:
    def __init__(self, type, x, y, speed):
        self.type = type
        self.x = x
        self.y = y
        self.speed = speed

        self.color = ITEM_COLOR
        if self.type == "enemy":
            self.color = ENEMY_COLOR

        self.size = PROJECTILE_SIZE
        if shrink_projectiles_item_active and self.type == "enemy":
            self.size = PROJECTILE_SIZE * SHRINK_PROJECTILES_ITEM_SIZE_PERCENTAGE

        self.sprite = shapes.Circle(self.x, self.y, self.size, color = self.color)

    def update_position(self, dt):
        if slowdown_item_active:
            self.y -= self.speed * SLOWDOWN_ITEM_SPEED_PERCENTAGE * dt
        else:
            self.y -= self.speed * dt
        self.sprite.y = self.y


# VARIABLEN UND INSTANZEN ##################################################################

# Spielzustand
game_state = "start"
time_elapsed = 0
score = 0

# Fenster
win = window.Window(WINDOW_WIDTH, WINDOW_HEIGHT)

# Bewegungssteuerung
sensor = SensorUDP(PORT)
gravity = {'x': 0, 'y': 0, 'z': 0}

# Player
player = Player(START_POS_X, START_POS_Y)

# Projektile allgemein
speed_multiplier = 1
spawn_interval_multiplier = 1

# Enemies
enemies = []
enemy_spawn_timer = 0

# Items
items = []
item_spawn_timer = 0
slowdown_item_active = False
slowdown_item_timestamp = 0
shrink_projectiles_item_active = False
shrink_projectiles_item_timestamp = 0
shrink_player_item_active = False
shrink_player_item_timestamp = 0

# GUI
time_label = pyglet.text.Label(
    f"Zeit: {time_elapsed}s",
    font_name='Arial',
    font_size=20,
    x=WINDOW_WIDTH - 30, y=WINDOW_HEIGHT - 30,
    anchor_x='right',
    anchor_y='center',
    color=WHITE
)
score_label = pyglet.text.Label(
    f"Score: {score}",
    font_name='Arial',
    font_size=30,
    x=WINDOW_WIDTH // 2, y=WINDOW_HEIGHT - 30,
    anchor_x='center',
    anchor_y='center',
    color=WHITE
)
game_over_label = pyglet.text.Label(
    "GAME OVER",
    font_name='Arial',
    font_size=48,
    x=WINDOW_WIDTH // 2,
    y=WINDOW_HEIGHT // 2,
    anchor_x='center',
    anchor_y='center',
    color=RED
)
restart_label = pyglet.text.Label(
    "Press button 1 to retry",
    font_name='Arial',
    font_size=20,
    x=WINDOW_WIDTH // 2,
    y=WINDOW_HEIGHT // 2 - 80,
    anchor_x='center',
    anchor_y='center',
    color=WHITE
)

# SPIELVERLAUF ##############################################################################

def update(dt):
    global game_state, time_elapsed, score, speed_multiplier, spawn_interval_multiplier, slowdown_item_active, slowdown_item_timestamp, shrink_projectiles_item_active, shrink_projectiles_item_timestamp, shrink_player_item_active, shrink_player_item_timestamp, enemy_spawn_timer, item_spawn_timer
    if game_state == "running":
        update_time_and_speed(dt)
        update_projectiles_pos_and_collision(dt)
        player.update_position()
        update_item_effects()
        spawn_projectiles(dt)

        if player.health <= 0:
            game_state = "game over"


def update_time_and_speed(dt):
    global time_elapsed, speed_multiplier, spawn_interval_multiplier

    time_elapsed += dt
    speed_multiplier = 1 + (time_elapsed * SPEED_INCREASE_PER_MS)

    spawn_interval_multiplier = 1 - (time_elapsed * SPAWN_INTERVAL_DECREASE_PER_MS)
    if spawn_interval_multiplier <= 0:
        spawn_interval_multiplier = 0.01


def update_projectiles_pos_and_collision(dt):
    global score, slowdown_item_active, slowdown_item_timestamp, shrink_projectiles_item_active, shrink_projectiles_item_timestamp, shrink_player_item_active, shrink_player_item_timestamp
    
    for enemy in enemies[:]:
        enemy.update_position(dt)
        if enemy.y < -PROJECTILE_SIZE:
            enemies.remove(enemy)
            score += POINTS_PER_AVOIDED_ENEMY
        if check_player_collision(enemy):
            enemies.remove(enemy)
            player.health -= 1

    for item in items[:]:
        item.update_position(dt)
        if item.y < -PROJECTILE_SIZE:
            if FAIL_TO_CATCH_ITEM_HURT:
                player.health -= 1
            items.remove(item)
        if check_player_collision(item):
            match item.type:
                case "points":
                    score += POINT_ITEM_WORTH
                case "heart":
                    if player.health < MAX_PLAYER_HEALTH:
                        player.health += 1
                    else:
                        score += POINT_ITEM_WORTH
                case "slowdown":
                    slowdown_item_active = True
                    print("slowdown activated")
                    slowdown_item_timestamp = time.time()
                case "shrink_projectiles":
                    shrink_projectiles_item_active = True
                    for enemy in enemies[:]:
                        enemy.sprite.radius *= SHRINK_PROJECTILES_ITEM_SIZE_PERCENTAGE
                    print("shrink projectiles activated")
                    shrink_projectiles_item_timestamp = time.time()
                case "shrink_player":
                    shrink_player_item_active = True
                    player.sprite.radius *= SHRINK_PLAYER_ITEM_SIZE_PERCENTAGE
                    print("shrink player activated")
                    shrink_player_item_timestamp = time.time()
            items.remove(item)


def check_player_collision(entity):
    distance = math.hypot(player.x - entity.x, player.y - entity.y)
    return distance < PLAYER_SIZE + PROJECTILE_SIZE


def update_item_effects():
    global slowdown_item_active, shrink_projectiles_item_active, shrink_player_item_active

    if slowdown_item_active and (time.time() - slowdown_item_timestamp) > ITEM_EFFECT_DURATION:
        slowdown_item_active = False
        print("slowdown item deactivated")
    if shrink_projectiles_item_active and (time.time() - shrink_projectiles_item_timestamp) > ITEM_EFFECT_DURATION:
        shrink_projectiles_item_active = False
        for enemy in enemies[:]:
            enemy.sprite.radius = PROJECTILE_SIZE
        print("shrink projectiles item deactivated")
    if shrink_player_item_active and (time.time() - shrink_player_item_timestamp) > ITEM_EFFECT_DURATION:
        player.sprite.radius = PLAYER_SIZE
        shrink_player_item_active = False
        print("shrink player item deactivated")


def spawn_projectiles(dt):
    global enemy_spawn_timer, item_spawn_timer, spawn_interval_multiplier

    spawn_slowdown = 1
    if slowdown_item_active:
        spawn_slowdown /= SLOWDOWN_ITEM_SPEED_PERCENTAGE
        
    enemy_spawn_timer += dt
    if enemy_spawn_timer >= MAX_ENEMY_SPAWN_INTERVAL * spawn_interval_multiplier * spawn_slowdown:
        spawn_enemy()
        enemy_spawn_timer = 0

    item_spawn_timer += dt
    if item_spawn_timer >= MAX_ITEM_SPAWN_INTERVAL * spawn_interval_multiplier * spawn_slowdown:
        spawn_item() 
        item_spawn_timer = 0


def spawn_enemy():
    if game_state == "running":
        if len(enemies) < MAX_NO_ENEMIES:
            x = random.randint(0 + PROJECTILE_SIZE, WINDOW_WIDTH - PROJECTILE_SIZE)
            y = WINDOW_HEIGHT - PROJECTILE_SIZE
            speed = random.uniform(MIN_PROJECTILE_SPEED * speed_multiplier, MAX_PROJECTILE_SPEED * speed_multiplier)

            enemies.append(Projectile("enemy", x, y, speed))
            #print("max_speed: " + str(MAX_PROJECTILE_SPEED*speed_multiplier) + ", interval: " + str(MAX_ENEMY_SPAWN_INTERVAL*spawn_interval_multiplier))
        else:
            print(len(enemies))


def spawn_item():
    if game_state == "running":
        x = random.randint(0 + PROJECTILE_SIZE, WINDOW_WIDTH - PROJECTILE_SIZE)
        y = WINDOW_HEIGHT - PROJECTILE_SIZE
        speed = random.uniform(MIN_PROJECTILE_SPEED * speed_multiplier, MAX_PROJECTILE_SPEED * speed_multiplier)

        exclude_hearts = 0
        if player.health >= MAX_PLAYER_HEALTH:
            exclude_hearts = 1
        type = ITEM_TYPES[random.randint(exclude_hearts, len(ITEM_TYPES) - 1)]

        items.append(Projectile(type, x, y, speed))


# DIPPID STEUERUNG CALLBACK #################################################################

def handle_gravity(data):
    global gravity

    if game_state == "running":
        gravity = data


def start(data):
    global player, enemies, items, score, time_elapsed, game_state, gravity, speed_multiplier, spawn_interval_multiplier, enemy_spawn_timer, item_spawn_timer, slowdown_item_active, slowdown_item_timestamp, shrink_projectiles_item_active, shrink_projectiles_item_timestamp, shrink_player_item_active, shrink_player_item_timestamp
    if game_state == "start":
        if data == 1:
            game_state = "running"  
    if game_state == "game over":
        if data == 1:
            player = Player(START_POS_X, START_POS_Y)
            enemies.clear()
            items.clear()
            score = 0
            time_elapsed = 0 
            game_state = "start"
            gravity = {'x': 0, 'y': 0, 'z': 0}
            speed_multiplier = 1
            spawn_interval_multiplier = 1

            enemy_spawn_timer = 0
            item_spawn_timer = 0

            slowdown_item_active = False
            slowdown_item_timestamp = 0
            shrink_projectiles_item_active = False
            shrink_projectiles_item_timestamp = 0
            shrink_player_item_active = False
            shrink_player_item_timestamp = 0


sensor.register_callback('gravity', handle_gravity)
sensor.register_callback('button_1', start)


# PYGLET LOGIK ############################################################################

@win.event
def on_draw():
    win.clear()
    if game_state == "start":
        draw_start_screen()
    if game_state == "running":
        player.sprite.draw()
        for enemy in enemies:
            enemy.sprite.draw()
        for item in items:
            item.sprite.draw()
        for i in range(player.health):
            heart = shapes.Circle(30 + i * 30, WINDOW_HEIGHT - 30, 10, color = RED)
            heart.draw()
        time_label.text = format_time(time_elapsed)
        score_label.text = f"Score: {score}"
        time_label.draw()
        score_label.draw()
    if game_state == "game over":
        game_over_label.draw()
        restart_label.draw()
        time_label.draw()
        score_label.draw()


def draw_start_screen():
    instructions = [
        ("Blue = You. Tilt phone to roll", PLAYER_COLOR),
        ("Pink = Don't touch -> Points, else: hurt ;(", ENEMY_COLOR),
        ("Green = Must touch -> Points, Lives, Surprise Effects..., else: hurt :(", ITEM_COLOR),
        ("", WHITE),
        ("Press button 1 to begin", WHITE),
    ]

    for i, (text, color) in enumerate(instructions):
        label = pyglet.text.Label(
            text,
            font_name='Arial',
            font_size=20,
            x=WINDOW_WIDTH // 2,
            y=WINDOW_HEIGHT - 50 - i * 30,
            anchor_x='center',
            color=(*color, 255)
        )
        label.draw()


def format_time(t):
    minutes = int(t // 60)
    seconds = int(t % 60)
    milliseconds = int((t - int(t)) * 1000)
    return f"{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


pyglet.clock.schedule_interval(update, 1/FRAMERATE)


pyglet.app.run()
