"""Simple pygame visualization scaffold for the sample project."""

import pygame
import sys

pygame.init()

WIDTH: int = 1200
HEIGHT: int = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fly-in  (safe🐍)")

clock = pygame.time.Clock()

running: bool = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    screen.fill((200, 200, 100))
    color = (255, 10, 0)
    position = (WIDTH // 2, HEIGHT // 3)
    radius = 300
    pygame.draw.rect(screen, (255,255,255), (30,30,1340,740), width=3 )
    pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()
