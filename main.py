import pygame
import random
import os
import sys

pygame.init()
pygame.mixer.init()

# -------------------- SETTINGS --------------------
WIDTH, HEIGHT = 500, 700
FPS = 60

CAR_SPEED = 5
VEHICLE_SPEED = 5
COIN_SPEED = 5
SPEED_INCREMENT = 0.005  # gradually increase vehicle speed

HITS_ALLOWED = 3

# Paths
ASSETS = "assets"
MAIN_CAR_IMG = os.path.join(ASSETS, "main.car", "maincar.png")
VEHICLES_FOLDER = os.path.join(ASSETS, "vehicles")
COINS_FOLDER = os.path.join(ASSETS, "collect")
FONT_PATH = os.path.join(ASSETS, "font", "Minecraft.ttf")
HIGH_SCORE_FILE = "highscore.txt"

# Colors
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
YELLOW = (255, 255, 0)

# -------------------- SCREEN --------------------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Car Rush")

# -------------------- LOAD IMAGES --------------------
main_car_img = pygame.image.load(MAIN_CAR_IMG).convert_alpha()
main_car_img = pygame.transform.scale(main_car_img, (60, 120))

vehicle_images = []
for file in os.listdir(VEHICLES_FOLDER):
    if file.endswith(".png"):
        img = pygame.image.load(os.path.join(VEHICLES_FOLDER, file)).convert_alpha()
        vehicle_images.append(pygame.transform.scale(img, (60, 120)))

coin_images = []
for file in os.listdir(COINS_FOLDER):
    if file.endswith(".png"):
        img = pygame.image.load(os.path.join(COINS_FOLDER, file)).convert_alpha()
        coin_images.append(pygame.transform.scale(img, (40, 40)))

font = pygame.font.Font(FONT_PATH, 28)

# -------------------- HELPER FUNCTIONS --------------------
def random_x(rect_width, avoid_rects=[]):
    """Return a random x that does not overlap existing rectangles"""
    attempts = 0
    while True:
        left = 60
        right = WIDTH - 60 - rect_width
        if right < left:
            right = left
        x = random.randint(left, right)
        rect = pygame.Rect(x, 0, rect_width, 120)
        overlap = any(rect.colliderect(r) for r in avoid_rects)
        if not overlap or attempts > 20:
            return x
        attempts += 1

def load_highscore():
    if os.path.exists(HIGH_SCORE_FILE):
        with open(HIGH_SCORE_FILE, "r") as f:
            try:
                return int(f.read())
            except:
                return 0
    return 0

def save_highscore(score):
    highscore = load_highscore()
    if score > highscore:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(score))

# -------------------- CLASSES --------------------
class MainCar:
    def __init__(self):
        self.image = main_car_img
        self.rect = self.image.get_rect(center=(WIDTH//2, HEIGHT-150))
        self.hit_count = 0
        self.glitch_timer = 0

    def move(self, keys):
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= CAR_SPEED
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += CAR_SPEED
        if keys[pygame.K_UP] and self.rect.top > 0:
            self.rect.y -= CAR_SPEED
        if keys[pygame.K_DOWN] and self.rect.bottom < HEIGHT:
            self.rect.y += CAR_SPEED

    def draw(self, surface):
        if self.glitch_timer > 0:
            # glitch effect with horizontal slices
            for i in range(0, self.rect.height, 10):
                offset_x = random.randint(-8, 8)
                slice_rect = pygame.Rect(0, i, self.rect.width, 10)
                surface.blit(self.image.subsurface(slice_rect), (self.rect.x + offset_x, self.rect.y + i))
            self.glitch_timer -= 1
        else:
            surface.blit(self.image, self.rect.topleft)

class Vehicle:
    def __init__(self, avoid_rects=[]):
        self.image = random.choice(vehicle_images)
        self.rect = self.image.get_rect(midtop=(random_x(self.image.get_width(), avoid_rects), random.randint(-600, -100)))
        self.x_drift = random.uniform(-1, 1)  # small horizontal drift

    def update(self, speed, other_vehicles=[]):
        self.rect.y += speed
        self.rect.x += self.x_drift

        # keep in screen
        if self.rect.left < 0 or self.rect.right > WIDTH:
            self.x_drift *= -1

        # repel from other vehicles
        for other in other_vehicles:
            if other is not self and self.rect.colliderect(other.rect.inflate(10, 10)):
                if self.rect.centerx < other.rect.centerx:
                    self.rect.x -= 2
                else:
                    self.rect.x += 2

        # respawn if out of screen
        if self.rect.top > HEIGHT:
            self.rect.y = random.randint(-300, -100)
            self.rect.x = random_x(self.image.get_width())
            self.image = random.choice(vehicle_images)
            self.x_drift = random.uniform(-1, 1)

    def draw(self, surface):
        surface.blit(self.image, self.rect.topleft)

class Coin:
    def __init__(self):
        self.image = random.choice(coin_images)
        self.rect = self.image.get_rect(midtop=(random_x(self.image.get_width()), -100))
        self.rotation = 0

    def update(self):
        self.rect.y += COIN_SPEED
        self.rotation = (self.rotation + 5) % 360
        self.image_rotated = pygame.transform.rotate(self.image, self.rotation)
        if self.rect.top > HEIGHT:
            self.rect.y = -random.randint(50, 300)
            self.rect.x = random_x(self.image.get_width())

    def draw(self, surface):
        surface.blit(self.image_rotated, self.rect.topleft)

# -------------------- GAME LOOP --------------------
def main():
    clock = pygame.time.Clock()
    run = True
    main_car = MainCar()
    vehicles = []
    avoid_rects = []

    # spawn vehicles without initial overlap
    for _ in range(5):
        vehicle = Vehicle(avoid_rects)
        vehicles.append(vehicle)
        avoid_rects.append(vehicle.rect)

    coins = [Coin() for _ in range(3)]
    score = 0
    vehicle_speed = VEHICLE_SPEED
    highscore = load_highscore()
    lane_offset = 0
    shake_timer = 0

    while run:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()

        # -------------------- EVENTS --------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_highscore(score)
                pygame.quit()
                sys.exit()

        main_car.move(keys)

        # -------------------- UPDATE --------------------
        vehicle_speed += SPEED_INCREMENT

        for vehicle in vehicles:
            vehicle.update(vehicle_speed, vehicles)
            if main_car.rect.colliderect(vehicle.rect):
                main_car.hit_count += 1
                main_car.glitch_timer = 15
                shake_timer = 10
                vehicle.rect.y = random.randint(-300, -100)
                vehicle.rect.x = random_x(vehicle.image.get_width())
                vehicle.x_drift = random.uniform(-1, 1)
                score = max(score-1, 0)
                if main_car.hit_count >= HITS_ALLOWED:
                    save_highscore(score)
                    run = False

        for coin in coins:
            coin.update()
            if main_car.rect.colliderect(coin.rect):
                score += 3
                coin.rect.y = -random.randint(50, 300)
                coin.rect.x = random_x(coin.image.get_width())

        # -------------------- DRAW --------------------
        offset_x, offset_y = (0, 0)
        if shake_timer > 0:
            offset_x = random.randint(-5, 5)
            offset_y = random.randint(-5, 5)
            shake_timer -= 1

        screen.fill(GRAY)

        # road lines (3 lanes)
        lane_height = 50
        lane_width = 10
        lane_positions = [WIDTH//4, WIDTH//2, WIDTH*3//4]
        for lane in lane_positions:
            for y in range(0, HEIGHT, lane_height*2):
                pygame.draw.rect(screen, WHITE, (lane - lane_width//2, (y + lane_offset) % HEIGHT, lane_width, lane_height))
        lane_offset += vehicle_speed

        # draw coins (not affected by shake)
        for coin in coins:
            coin.draw(screen)

        # draw vehicles with shake
        for vehicle in vehicles:
            screen.blit(vehicle.image, (vehicle.rect.x + offset_x, vehicle.rect.y + offset_y))

        # draw main car
        main_car.draw(screen)

        # score
        score_text = font.render(f"Score: {score}", True, YELLOW)
        screen.blit(score_text, (10, 10))
        high_text = font.render(f"Highscore: {max(highscore, score)}", True, YELLOW)
        screen.blit(high_text, (10, 40))

        pygame.display.update()

    # restart game
    main()

if __name__ == "__main__":
    main()
