import pygame
import sys

pygame.init()

WIDTH = 1200
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fly-in  (safe🐍)")

clock = pygame.time.Clock()

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    screen.fill((200, 200, 20))
    pygame.draw.line(
    screen,
    (255, 0, 0),
    (100, 100),
    (300, 100),
    5
)

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()
