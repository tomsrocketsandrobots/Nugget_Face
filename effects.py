from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from constants import *
import numpy as np

class ScanLineEffect:
    def __init__(self, line_thickness=0.005, spacing=0.02):
        self.line_thickness = line_thickness  # Thickness of each scan line
        self.spacing = spacing  # Space between the lines

    def draw_scan_lines(self):
        glColor4f(0.0, 0.0, 0.0, 0.3)  # Set scan line color and opacity (semi-transparent black)
        glLineWidth(self.line_thickness)

        glBegin(GL_LINES)
        y_pos = 1.0  # Start from the top of the screen in NDC
        while y_pos > -1.0:
            glVertex2f(-1.0, y_pos)
            glVertex2f(1.0, y_pos)
            y_pos -= self.spacing  # Move down by the spacing value
        glEnd()

import random
class WanderingScanLineEffect(ScanLineEffect):
    def __init__(self, line_thickness=2, spacing=0.05, wander_amount=0.1, wander_speed=1.0):
        super().__init__(line_thickness, spacing)
        self.wander_amount = wander_amount  # Maximum vertical displacement
        self.wander_speed = wander_speed  # Speed of wandering effect
        
        
    def draw_scan_lines(self, time):
        # glColor4f(0.0, 0.0, 0.0, 0.3)  # Set scan line color and opacity (semi-transparent black)
        # glLineWidth(self.line_thickness)
        # glBegin(GL_LINES)
        y_pos = 1.0  # Start from the top of the screen in NDC
        vertical_offset = np.sin(time * self.wander_speed + y_pos * 10) * self.wander_amount
        
        num_lines = int(1/self.spacing)
        x = np.linspace(1, -1, num_lines)
        space_dither = np.sin(2*np.pi/num_lines*x*80)
        space_dither_mag = 0.4
        y_pos_vals = x + space_dither*space_dither_mag
        
        thickness_dither = self.line_thickness
        
        time_dither = np.sin(2*np.pi*time*0.5)
        line_alpha = time_dither*0.8+1.0
        pass
    
        
        # plt.plot(x, y_pos_vals)
        # plt.savefig('plot.png')  # Save as a file instead of showing it
        
        for y_pos in y_pos_vals:
            # line_alpha = 10*dither_val
            # line_alpha = random.randrange(1, 100)/100.0
            glLineWidth(thickness_dither)
            glBegin(GL_LINES)
            glColor4f(0.0, 0.0, 0.0, line_alpha)  # Set scan line color and opacity (semi-transparent black)
            # Calculate a vertical wander offset based on time (sinusoidal or random movement)
            
            # vertical_offset = time * self.wander_speed + y_pos * 10
            # Apply the vertical offset to the scan line position
            glVertex2f(-1.0, y_pos + vertical_offset)
            glVertex2f(1.0, y_pos + vertical_offset)

            glEnd()


import numpy as np
from OpenGL.GL import *

class VignetteEffect:
    def __init__(self, radius=0.3, max_alpha=1.0, color=(0.0, 0.0, 0.0, 0.5)):
        self.radius = radius
        self.color = color
        self.max_alpha = max_alpha
        self.vignette_texture = None
        self.texture_size = 512  # Size of the vignette texture

    def generate_vignette_texture(self):
        """Generates the vignette and stores it in a texture."""
        # Create the vignette texture
        self.vignette_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.vignette_texture)

        # Define the texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # Allocate texture memory
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.texture_size, self.texture_size, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)

        # Create a framebuffer to render to the texture
        framebuffer = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.vignette_texture, 0)

        # Set up the viewport to match the texture size
        glViewport(0, 0, self.texture_size, self.texture_size)

        # Clear the framebuffer
        glClear(GL_COLOR_BUFFER_BIT)

        # Draw the vignette (onto the texture)
        self.draw_vignette()

        # Unbind the framebuffer
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        # Reset the viewport to the window size
        glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

    def draw_vignette(self):
        """Draws four rectangles (top, bottom, left, right) that overlap and create a vignette effect."""
        # Draw the vignette along the top
        bottom_of_top = 1-self.radius
        glBegin(GL_QUADS)
        glColor4f(self.color[0], self.color[1], self.color[2], self.max_alpha)  # Top-right
        glVertex2f(1.0, 1.0)

        glColor4f(self.color[0], self.color[1], self.color[2], self.max_alpha)  # Top-left
        glVertex2f(-1.0, 1.0)
        
        glColor4f(self.color[0], self.color[1], self.color[2], 0.0)  # Bottom-left
        glVertex2f(-1.0, bottom_of_top)
        
        glColor4f(self.color[0], self.color[1], self.color[2], 0.0)  # Bottom-right
        glVertex2f(1.0, bottom_of_top)
        glEnd()

        # Draw the vignette along the bottom
        top_of_bottom = -1+self.radius
        glBegin(GL_QUADS)
        glColor4f(self.color[0], self.color[1], self.color[2], 0.0)  # Top-right
        glVertex2f(1, top_of_bottom)

        glColor4f(self.color[0], self.color[1], self.color[2], 0.0)  # Top-left
        glVertex2f(-1.0, top_of_bottom)
        
        glColor4f(self.color[0], self.color[1], self.color[2], self.max_alpha)  # Bottom-left
        glVertex2f(-1.0, -1.0)
        
        glColor4f(self.color[0], self.color[1], self.color[2], self.max_alpha)  # Bottom-right
        glVertex2f(1.0, -1.0)
        glEnd()

        # Draw the vignette along the left
        right_of_left = -1+self.radius
        glBegin(GL_QUADS)
        glColor4f(self.color[0], self.color[1], self.color[2], 0.0)  # Top-right
        glVertex2f(right_of_left, 1.0)

        glColor4f(self.color[0], self.color[1], self.color[2], self.max_alpha)  # Top-left
        glVertex2f(-1.0, 1.0)
        
        glColor4f(self.color[0], self.color[1], self.color[2], self.max_alpha)  # Bottom-left
        glVertex2f(-1.0, -1.0)
        
        glColor4f(self.color[0], self.color[1], self.color[2], 0.0)  # Bottom-right
        glVertex2f(right_of_left, -1)
        glEnd()

        # Draw the vignette along the right
        left_of_right = 1-self.radius
        glBegin(GL_QUADS)
        glColor4f(self.color[0], self.color[1], self.color[2], self.max_alpha)  # Top-right
        glVertex2f(1.0, 1.0)

        glColor4f(self.color[0], self.color[1], self.color[2], 0.0)  # Top-left
        glVertex2f(left_of_right, 1.0)
        
        glColor4f(self.color[0], self.color[1], self.color[2], 0.0)  # Bottom-left
        glVertex2f(left_of_right, -1.0)
        
        glColor4f(self.color[0], self.color[1], self.color[2], self.max_alpha)  # Bottom-right
        glVertex2f(1.0, -1)
        glEnd()

    def overlay_vignette(self):
        """Overlays the vignette texture onto the scene."""
        if self.vignette_texture is None:
            self.generate_vignette_texture()  # Generate the vignette texture once

        # Enable texturing
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.vignette_texture)

        # Draw a full-screen quad with the vignette texture
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0); glVertex2f(-1.0, -1.0)
        glTexCoord2f(1.0, 0.0); glVertex2f(1.0, -1.0)
        glTexCoord2f(1.0, 1.0); glVertex2f(1.0, 1.0)
        glTexCoord2f(0.0, 1.0); glVertex2f(-1.0, 1.0)
        glEnd()

        glDisable(GL_TEXTURE_2D)


class StaticNoiseEffect:
    def __init__(self, noise_intensity=0.1, noise_opacity=0.3, num_dots=500):
        """
        noise_intensity: controls how much of the screen is affected by static (0.0 to 1.0)
        noise_opacity: transparency of the noise (0.0 fully transparent, 1.0 fully opaque)
        num_dots: number of dots to render for the static effect
        """
        self.noise_intensity = noise_intensity
        self.noise_opacity = noise_opacity
        self.num_dots = num_dots

    def draw_static(self):
        """Draws random static noise as small dots scattered across the screen."""
        glPointSize(2)  # Set the size of the noise points

        glBegin(GL_POINTS)
        for _ in range(self.num_dots):
            # Randomly position each noise point within the screen's normalized device coordinates (NDC)
            x = random.uniform(-1.0, 1.0)
            y = random.uniform(-1.0, 1.0)

            # Randomly choose between black and white static points
            color = random.choice([(1.0, 1.0, 1.0), (0.0, 0.0, 0.0)])

            # Apply the color and set its opacity
            glColor4f(color[0], color[1], color[2], self.noise_opacity)

            # Draw the point
            glVertex2f(x, y)

        glEnd()


class GridEffect:
    def __init__(self, grid_size=0.03, line_thickness=1.5, line_color=(0.0, 0.0, 0.0, 0.8), texture_size=512):
        self.grid_size = grid_size
        self.line_thickness = line_thickness
        self.line_color = line_color
        self.texture_size = texture_size
        self.grid_texture = None

    def draw_grid(self):
        """Draws a grid over the screen with lines spaced by grid_size."""
        glColor4f(*self.line_color)
        glLineWidth(self.line_thickness)

        # Draw vertical lines
        glBegin(GL_LINES)
        x_pos = -1.0
        while x_pos <= 1.0:
            glVertex2f(x_pos, -1.0)
            glVertex2f(x_pos, 1.0)
            x_pos += self.grid_size
        glEnd()

        # Draw horizontal lines
        glBegin(GL_LINES)
        y_pos = -1.0
        while y_pos <= 1.0:
            glVertex2f(-1.0, y_pos)
            glVertex2f(1.0, y_pos)
            y_pos += self.grid_size
        glEnd()

    def generate_grid_texture(self):
        """Renders the grid once to a texture."""
        self.grid_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.grid_texture)

        # Define the texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.texture_size, self.texture_size, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)

        # Create a framebuffer to render to the texture
        framebuffer = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, framebuffer)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.grid_texture, 0)

        # Check if the framebuffer is complete
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("Framebuffer is not complete!")
            glBindFramebuffer(GL_FRAMEBUFFER, 0)
            return

        # Set up the viewport to match the texture size
        glViewport(0, 0, self.texture_size, self.texture_size)

        # Clear the framebuffer and draw the grid onto the texture
        glClear(GL_COLOR_BUFFER_BIT)
        self.draw_grid()

        # Unbind the framebuffer and reset viewport
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)

        # Unbind texture
        glBindTexture(GL_TEXTURE_2D, 0)

    def overlay_grid(self):
        """Draws the grid overlay from the texture."""
        if self.grid_texture is None:
            self.generate_grid_texture()

        # Enable texturing and bind the grid texture
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.grid_texture)

        # Draw the texture as a fullscreen quad
        glColor4f(1.0, 1.0, 1.0, 1.0)  # Set color to white
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 0.0)
        glVertex2f(-1.0, -1.0)

        glTexCoord2f(1.0, 0.0)
        glVertex2f(1.0, -1.0)

        glTexCoord2f(1.0, 1.0)
        glVertex2f(1.0, 1.0)

        glTexCoord2f(0.0, 1.0)
        glVertex2f(-1.0, 1.0)
        glEnd()

        glDisable(GL_TEXTURE_2D)
        