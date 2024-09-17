import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import time as sys_time
from face_control import *
from constants import *


# Initialize Pygame and OpenGL
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF | OPENGL)

#screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), DOUBLEBUF)
# gluOrtho2D(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT)


# Initialize the eye and mouth
face = Face3()

running = True
clock = pygame.time.Clock()

# Set background color (R, G, B, Alpha)
test_bg = (1.0, 1.0, 1.0, 1.0)  # White background

while running:
    current_time = pygame.time.get_ticks() / 1000.0  # Get time in seconds

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # glClearColor(*test_bg)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # Update face
    face.update()

    pygame.display.flip()
    
    # time += 1.3  # Adjust time increment as needed
    clock.tick(FPS)  # Limit to FPS

pygame.quit()
