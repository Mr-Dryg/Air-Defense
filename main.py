import pygame
import os
from math import sin, cos, radians, degrees, pi, acos, asin, hypot, atan
from random import randint
import time

game_folder = os.path.dirname(__file__)
img_folder = os.path.join(game_folder, 'img')

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

v0 = 140
g = 10
dt = 1 / 50

def pro_arc(a, a_x, a_y):
    try:
        r1 = {(round(degrees(asin(a_y/a))) + 360) % 360, 180 - round(degrees(asin(a_y/a)))}
        r2 = {round(degrees(acos(a_x/a))), 360 - round(degrees(acos(a_x/a)))}
        r = r1 & r2
        for i in r:
            i = float(radians(i - 360))
            return i
    except ZeroDivisionError:
        return 0


class MovingObject(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.vx = self.v * cos(self.angle)
        self.vy = self.v * sin(self.angle)
    
    def update(self):
        if self.kind == 'Rocket':
            self.rect.centerx = self.x + self.vx * self.t
            self.rect.centery = self.y + self.vy * self.t
        elif self.kind == 'Bullet':
            self.rect.centerx = self.x + self.vx * self.t
            self.rect.centery = self.y - self.vy * self.t + g * self.t * self.t / 2
        self.t += dt


class Bullet(MovingObject):
    def __init__(self, gun):
        self.kind = 'Bullet'
        self.t = 0
        self.angle = gun.angle
        self.v = v0
        if self.angle == 90:
            self.x, self.y = gun.rect.midtop
        elif self.angle < 90:
            self.x, self.y = gun.rect.topright
            if self.angle < 45:
                self.y += 5
            elif self.angle > 45:
                self.x -= 5
        elif self.angle > 90:
            self.x, self.y = gun.rect.topleft
            if self.angle < 45 + 90:
                self.x += 5
            elif self.angle > 45 + 90:
                self.y += 5
        self.angle = radians(self.angle)

        self.img_folder = os.path.join(img_folder, 'Bullet')
        self.image = pygame.image.load(os.path.join(self.img_folder, 'bullet.png')).convert()
        self.image.set_colorkey(GREEN)
        self.rect = self.image.get_rect()
        self.rect.center = (self.x, self.y)
        MovingObject.__init__(self)


class Rocket(MovingObject):
    def __init__(self, w, aim):
        self.kind = 'Rocket'
        self.t = 0
        self.x = randint(0, w)
        self.y = randint(-100, -20)
        self.v = randint(80, 150)
        dx = aim.rect.centerx - self.x
        dy = aim.rect.centery - self.y
        self.angle = pro_arc(hypot(dx, dy), dx, dy)

        self.img_folder = os.path.join(img_folder, 'Rocket')
        self.image = pygame.image.load(os.path.join(self.img_folder, 'rocket.png')).convert()
        self.orig = self.image
        self.image.set_colorkey(GREEN)
        self.rect = self.image.get_rect()
        self.image = pygame.transform.rotate(self.orig, - degrees(self.angle))
        self.rect = self.image.get_rect(center = self.rect.center)
        self.rect.center = (self.x, self.y)
        MovingObject.__init__(self)


class Bunker(pygame.sprite.Sprite):
    def __init__(self, w, h):
        pygame.sprite.Sprite.__init__(self)
        self.img_folder = os.path.join(img_folder, 'ADS')
        self.image = pygame.image.load(os.path.join(self.img_folder, 'bunker.png')).convert()
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.midbottom = (w / 4, h)


class Cannon(pygame.sprite.Sprite):
    def __init__(self, position):
        pygame.sprite.Sprite.__init__(self)
        self.angle = 45
        self.img_folder = os.path.join(img_folder, 'ADS')
        self.image = pygame.image.load(os.path.join(self.img_folder, 'cannon.png')).convert()
        self.orig = self.image
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.image = pygame.transform.rotate(self.orig, self.angle)
        self.rect = self.image.get_rect(center = self.rect.center)
    
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.turn(1)
        elif keys[pygame.K_RIGHT]:
            self.turn(-1)

    def turn(self, dir):
        dir = dir / 1.5
        if 155 > self.angle + dir > 25:
            self.image = pygame.transform.rotate(self.orig, self.angle + dir)
            self.angle += dir
            self.rect = self.image.get_rect(center = self.rect.center)


class Protected_object(pygame.sprite.Sprite):
    def __init__(self, w, h, x=None):
        pygame.sprite.Sprite.__init__(self)
        self.img_folder = os.path.join(img_folder, 'Big Mushroom')
        self.image = pygame.image.load(os.path.join(self.img_folder, 'Big Mushroom_Single.png')).convert()
        self.rect = self.image.get_rect()
        self.rect.midbottom = (x or 2.5 * w / 4, h)


class Background(pygame.sprite.Sprite):
    def __init__(self, w, h):
        pygame.sprite.Sprite.__init__(self)
        self.img_folder = os.path.join(img_folder, 'horizon')
        self.image = pygame.image.load(os.path.join(self.img_folder, 'horizon.png')).convert()
        self.image = pygame.transform.scale(self.image, (w, h))
        self.rect = self.image.get_rect()
        self.rect.center = (w / 2, h / 2)


class Radar():
    def __init__(self, bunker, target):
        self.target = target
        self.x = bunker.rect.centerx
        self.y = bunker.rect.centery
        self.max_distance = 1500

    def scan(self, rockets):
        self.res = []
        n = 0
        for i, rocket in enumerate(rockets, start=1):
            dist = hypot(rocket.rect.centerx - self.x, rocket.rect.centery - self.y)
            if dist <= self.max_distance:
                try:
                    self.res.append((i - n, int(degrees(atan((rocket.rect.centerx - self.target.rect.centerx) / (rocket.rect.centery - self.target.rect.centery)))), int(dist)))
                except ZeroDivisionError:
                    self.res.append((i - n, 0, int(dist)))
            else:
                n += 1
        print('SCANNINIG:', ', '.join(str(el) for el in self.res))


if __name__ == '__main__':

    WIDTH = 1920
    HEIGHT = 1080
    FPS = 60

    # Создаем игру и окно
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    all_sprites = pygame.sprite.Group()
    target = Protected_object(WIDTH, HEIGHT)
    bunker = Bunker(WIDTH, HEIGHT)
    cannon = Cannon(bunker.rect.center)
    bg = Background(WIDTH, HEIGHT)
    radar = Radar(bunker, target)
    all_sprites.add(bg, cannon, bunker, target)

    bullets = []
    rockets = []

    time_rockets = None
    time_bullets = None

    # Цикл игры
    running = True
    while running:
        start = time.time()
        clock.tick(FPS)
        screen.fill(BLACK)

        for el in rockets:
            if el.rect.bottom > HEIGHT:
                rockets.remove(el)

        for bullet in bullets:
            for rocket in rockets:
                if pygame.Rect.colliderect(bullet.rect, rocket.rect):
                    rockets.remove(rocket)
                    bullets.remove(bullet)
                    bullet.kill()
                    rocket.kill()
                    break

        if time_rockets is None or time_rockets + 4 == round(time.time()):
            rocket = Rocket(WIDTH, target)
            all_sprites.add(rocket)
            rockets.append(rocket)
            time_rockets = round(time.time())

        radar.scan(rockets)

        # Ввод события
        for event in pygame.event.get():
            # выход из игры
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if time_bullets is None or time_bullets + 1.2 <= round(time.time(), 1):
                        bullet = Bullet(cannon)
                        all_sprites.add(bullet)
                        bullets.append(bullet)
                        time_bullets = round(time.time())

        # Обновление
        all_sprites.update()
        
        # Рендеринг
        all_sprites.draw(screen)
        # После отрисовки всего, переворачиваем экран
        pygame.display.flip()
