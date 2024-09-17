from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import time as sys_time
import random
from effects import *
from constants import *

DEFAULT_ANALOG_MODE = False
EYE_RADIUS_X = 0.28
EYE_RADIUS_Y = 0.33
PUPIL_RADIUS = 0.17
WAVELET_PERIOD = 4.0
NUM_EYE_SEGMENTS = 13
NUM_SMILE_EYE_SEGMENTS = 6
LINE_WIDTH_THICK = 26
LINE_WIDTH_MEDIUM = 18
LINE_WIDTH_THIN = 8
EYE_MOVE_DURATION = 150
BLINK_FRAMES = 8  # Number of frames to complete a blink
DITHER_MAG = 0.04
SMILE_MAX = 1.3
SMILE_MIN = -1.3

def ease_in_out(t):
    # Quadratic ease-in-out function
    if t < 0.5:
        return 2 * t * t
    return -1 + (4 - 2 * t) * t

def ease_in(t):
    # Quadratic ease-in
    return t * t

def ease_out(t):
    # Quadratic ease-out
    return t * (2 - t)

def drawTestRectangle():
        glBegin(GL_QUADS)
        glColor3f(1.0, 0.0, 0.0)  # Red color
        glVertex2f(-0.5, -0.5)
        glVertex2f(0.5, -0.5)
        glVertex2f(0.5, 0.5)
        glVertex2f(-0.5, 0.5)
        glEnd()
        
class Eye:
    def __init__(self, x_center, y_center, x_radius=EYE_RADIUS_X, y_radius=EYE_RADIUS_Y, pupil_radius_x=PUPIL_RADIUS, pupil_radius_y=PUPIL_RADIUS):
        # self.window_width = window_width
        # self.window_height = window_height
        self.x_radius_nom = x_radius# convert_radius_to_ndc(x_radius)
        self.y_radius_nom = y_radius#convert_radius_to_ndc(y_radius)
        self.pupil_radius_x = pupil_radius_x#convert_radius_to_ndc(pupil_radius)
        self.pupil_radius_y = pupil_radius_y
        
        self.x_center_nom, self.y_center_nom = x_center, y_center#convert_to_ndc(x_center, y_center)
        self.eye_target_x = self.x_center_nom
        self.eye_target_y = self.y_center_nom
        self.pupil_x = 0
        self.pupil_y = 0
        self.dX_values = []
        self.dY_values = []
        self.frame_count = 0
        self.eye_delay_frames = 12
        self.movement_complete = False
        self.blinking = False  # Flag to track if the eye is blinking
        self.blink_frame_count = 0  # Track the blink frame progress
        self.dither_magnitude = DITHER_MAG # Amount of dithering (can be adjusted)
        self.dither_frequency = 0.05  # Frequency of dithering
        self.pupil_offset_scaling = 0.5  # Scaling factor for pupil offset
        self.lower_bound = 0
        self.boundary_color = (0.0, 1.0, 1.0)
        self.pupil_color = (0.0, 1.0, 1.0)
        self.smile_val = -0.1
        
    def update(self):
        if self.smile_val > SMILE_MAX*0.25:
            self.draw_smiling_eye()
        elif self.smile_val < SMILE_MIN*.3:
            self.draw_sleeping_eye()
        else:
            self.draw_eye()
            # 
        # self.draw_pupil()
        
        
    def apply_dithering(self, time):
        # Add small random dithering to the eye when stationary
        dither_x = np.sin(time * self.dither_frequency) * self.dither_magnitude * (np.random.random() - 0.5)
        dither_y = np.sin(time * self.dither_frequency) * self.dither_magnitude * (np.random.random() - 0.5)
        return dither_x, dither_y
    
    def set_pupil_position(self, offset_x, offset_y):
        # This method already calculates if the pupil goes out of bounds, so we use it later
        eye_x = self.x_center_nom
        eye_y = self.y_center_nom
        proposed_x = eye_x + offset_x
        proposed_y = eye_y + offset_y
        x_relative = (proposed_x - eye_x) / self.x_radius_nom
        y_relative = (proposed_y - eye_y) / self.y_radius_nom

        if (x_relative ** 2 + y_relative ** 2) <= 1:
            self.pupil_x = offset_x
            self.pupil_y = offset_y
        else:
            angle = np.arctan2(offset_y, offset_x)
            self.pupil_x = self.x_radius_nom * np.cos(angle)
            self.pupil_y = self.y_radius_nom * np.sin(angle)
            
    def start_blink(self):
        """Start a blinking animation."""
        if not self.blinking:
            self.blinking = True
            self.blink_frame_count = 0
        
    def blink(self):
        """Handle the blink animation over multiple frames."""
        if self.blinking:
            # Calculate blink progress (0.0 to 1.0)
            progress = self.blink_frame_count / (BLINK_FRAMES // 2)

            if self.blink_frame_count <= BLINK_FRAMES // 2:
                # Closing phase: reduce the y-radius
                ease_val = (1 - ease_in_out(progress))
                self.y_radius_nom = EYE_RADIUS_Y * ease_val
                self.pupil_radius_y = PUPIL_RADIUS * ease_val
            else:
                ease_val = ease_in_out(progress - 1)
                # Opening phase: restore the y-radius
                self.y_radius_nom = EYE_RADIUS_Y * ease_val
                self.pupil_radius_y = PUPIL_RADIUS * ease_val

            # Increment the blink frame count
            self.blink_frame_count += 1

            # End the blink when the animation is complete
            if self.blink_frame_count >= BLINK_FRAMES:
                self.blinking = False
                self.y_radius_nom = EYE_RADIUS_Y  # Fully restore the y-radius
                
    def set_target_position(self, x, y, duration_ms):
        self.eye_target_x = x
        self.eye_target_y = min(y, 1.0 - 2*self.y_radius_nom)
        self.eye_move_duration = duration_ms / 1000.0  # Convert to seconds

        # Calculate total number of frames for the movement
        total_frames = int(self.eye_move_duration * FPS)
        
        # Reset frame count and movement flag
        self.frame_count = 0
        self.movement_complete = False

        # Calculate the total distance to move in both x and y directions
        total_x_distance = x - self.x_center_nom
        total_y_distance = y - self.y_center_nom

        # Pre-calculate dX and dY values for each frame, using the ease-in-out function
        self.dX_values = []
        self.dY_values = []

        for frame in range(total_frames):
            # Progress ratio (between 0 and 1) for the current frame
            t = frame / total_frames
            ease_t = ease_in_out(t)  # Apply ease-in-out function

            # Calculate the position offset for this frame
            dX = total_x_distance * ease_t
            dY = total_y_distance * ease_t

            self.dX_values.append(dX)
            self.dY_values.append(dY)


    def move_eye(self, time):
        if self.frame_count < len(self.dX_values) and not self.movement_complete:
            # Apply the pre-calculated dX and dY to the pupil
            dX_pupil = self.dX_values[self.frame_count]
            dY_pupil = self.dY_values[self.frame_count]
            self.set_pupil_position(dX_pupil, dY_pupil)

            # Apply the delayed movement to the eye
            eye_index = max(0, self.frame_count - self.eye_delay_frames)
            dX_eye = self.dX_values[eye_index]
            dY_eye = self.dY_values[eye_index]
            self.x_center_nom += dX_eye
            self.y_center_nom += dY_eye

            # Increment frame count
            self.frame_count += 1
        else:
            # Ensure the eye and pupil reach their exact target positions
            self.x_center_nom = self.eye_target_x
            self.y_center_nom = self.eye_target_y

            # Calculate relative position considering lower bound of the eye
            relative_x = (self.x_center_nom - EYE_RADIUS_X)# / (1 - 2 * EYE_RADIUS_X)
            relative_y = (self.y_center_nom - self.lower_bound)# / (1 - self.lower_bound - EYE_RADIUS_Y)

            # Map relative positions to pupil offset with scaling factor
            pupil_offset_x = (relative_x - 0.4) * self.x_radius_nom * 2 * self.pupil_offset_scaling
            pupil_offset_y = (relative_y - 0.5) * self.y_radius_nom * 2 * self.pupil_offset_scaling

            # Ensure pupil stays within the eye bounds
            self.set_pupil_position(pupil_offset_x, pupil_offset_y)

            # Mark the movement as complete to stop further updates
            self.movement_complete = True

            # Apply dithering once the movement is complete
            dither_x, dither_y = self.apply_dithering(time)
            self.x_center_nom += dither_x
            self.y_center_nom += dither_y
        
    def draw_filled_circle(self, color, radius, xpos, ypos, segments = NUM_EYE_SEGMENTS):
        glColor3f(*color)
        glBegin(GL_TRIANGLE_FAN)
        theta = 2 * np.pi / segments
        cos_vals = np.cos(np.arange(segments + 1) * theta)
        sin_vals = np.sin(np.arange(segments + 1) * theta)
        for i in range(segments + 1):
            x = radius * cos_vals[i]
            y = radius * sin_vals[i]
            glVertex2f(xpos + x, ypos + y)
        glEnd()
        
    def draw_filled_ellipse(self, color, x_radius, y_radius, x_pos, y_pos, segments = NUM_EYE_SEGMENTS):
        glColor3f(*color)
        glBegin(GL_TRIANGLE_FAN)
        theta = 2 * np.pi / segments
        cos_vals = np.cos(np.arange(segments + 1) * theta)
        sin_vals = np.sin(np.arange(segments + 1) * theta)
        for i in range(segments + 1):
            x = x_radius * cos_vals[i]
            y = y_radius * sin_vals[i]
            glVertex2f(x_pos + x, y_pos + y)
        glEnd()
        
     
    def set_pupil_position(self, normalized_direction_x, normalized_direction_y):
        # Scale the normalized direction by the eye's dimensions
        self.pupil_x = normalized_direction_x * self.x_radius_nom * 0.85  # Slightly smaller to stay inside the eye
        self.pupil_y = normalized_direction_y * self.y_radius_nom * 0.85
   
    def draw_eye(self):
        self.blink()
        # Draw the outer cyan ellipse (larger ellipse for the thick line effect)
        outer_x_radius = self.x_radius_nom
        outer_y_radius = self.y_radius_nom
        self.draw_filled_ellipse(self.boundary_color, outer_x_radius, outer_y_radius, self.x_center_nom, self.y_center_nom)  # Cyan color

        # Draw the inner black ellipse (to simulate the thick line effect)
        inner_x_radius = outer_x_radius * 0.85  # Slightly smaller radius for the black ellipse
        inner_y_radius = outer_y_radius * 0.85
        self.draw_filled_ellipse((0.0, 0.0, 0.0), inner_x_radius, inner_y_radius, self.x_center_nom, self.y_center_nom)  # Black color

        #draw the pupil
        pupil_x = self.x_center_nom + self.pupil_x
        pupil_y = self.y_center_nom + self.pupil_y
        self.draw_filled_ellipse(self.pupil_color, self.pupil_radius_x, self.pupil_radius_y, pupil_x, pupil_y)

    def draw_smiling_eye(self):
        self.blinking = False
        self.blink_frame_count = 0
        self.y_radius_nom = EYE_RADIUS_Y
        self.pupil_radius_y = PUPIL_RADIUS

	# Draw the outer cyan ellipse (larger ellipse for the thick line effect)
        outer_x_radius = self.x_radius_nom*1.0
        outer_y_radius = self.y_radius_nom/4
        self.draw_filled_ellipse(self.boundary_color, outer_x_radius, outer_y_radius, self.x_center_nom, self.y_center_nom, NUM_SMILE_EYE_SEGMENTS)  # Cyan color

        # Draw the inner black ellipse (to simulate the thick line effect)
        inner_x_radius = outer_x_radius*0.9 # Slightly smaller radius for the black ellipse
        inner_y_radius = outer_y_radius*1.2
        self.draw_filled_ellipse((0.0, 0.0, 0.0), inner_x_radius, inner_y_radius, self.x_center_nom, self.y_center_nom-0.07, NUM_SMILE_EYE_SEGMENTS)  # Black color
    
    def draw_sleeping_eye(self):
        self.blinking = False
        self.blink_frame_count = 0
        self.y_radius_nom = EYE_RADIUS_Y
        self.pupil_radius_y = PUPIL_RADIUS

	# Draw the outer cyan ellipse (larger ellipse for the thick line effect)
        outer_x_radius = self.x_radius_nom*1.0
        outer_y_radius = self.y_radius_nom/4
        self.draw_filled_ellipse(self.boundary_color, outer_x_radius, outer_y_radius, self.x_center_nom, self.y_center_nom, NUM_SMILE_EYE_SEGMENTS)  # Cyan color

        # Draw the inner black ellipse (to simulate the thick line effect)
        inner_x_radius = outer_x_radius*0.9 # Slightly smaller radius for the black ellipse
        inner_y_radius = outer_y_radius*1.2
        self.draw_filled_ellipse((0.0, 0.0, 0.0), inner_x_radius, inner_y_radius, self.x_center_nom, self.y_center_nom+0.07, NUM_SMILE_EYE_SEGMENTS)  # Black color
class Mouth:
    def __init__(self):
        self.width = 1
        self.height = 1
        self.wavelet_center_x = 0.5
        self.wavelet_center_y = 0.3
        self.noise_level = 0.2  # Default noise level
        self.open_val = 1.0
        self.smile_val = -0.1
        self.x1_scale = 0.7
        self.x2_scale = 0.9
        self.y1_scale = 0.3
        self.y2_scale = 0.2
        
    def wavelet(self, x, time, scale=1.0, frequency=1.0, amplitude=1.0):
        # Add some noise to the amplitude or position
        noise = np.random.uniform(-self.noise_level, self.noise_level)
        wave = (scale * np.sinc(x) * amplitude * np.sin(frequency * x + time)) + noise
        smile_quad = (self.smile_val * x * x)
        return wave+smile_quad

    def sawtooth_wave(self, x, period=WAVELET_PERIOD):
        x_mod = x % period
        # Add noise to the sawtooth wave
        noise = np.random.uniform(-self.noise_level, self.noise_level)
        return 2 * (x_mod / period) - 1 + noise

    def wavelet_sharp(self, x, time, scale=1.0, frequency=1.0, amplitude=1.0):
        # Add noise to the sharp wavelet
        noise = np.random.uniform(-self.noise_level, self.noise_level)
        wave = (scale * np.sinc(x) * amplitude * self.sawtooth_wave(x, 1 / frequency)) + noise
        smile_quad = (self.smile_val * x * x)
        return wave+smile_quad
    
    def set_mouth_open_val(self, v):
        mouth_max = 1.5
        mouth_min = 0.1
        self.open_val = max(min(v, mouth_max), mouth_min)
    
    def set_smile_val(self, v):
        self.smile_val = max(min(v, SMILE_MAX), SMILE_MIN)
        
    def draw_mouth(self, time):
        rear_wave_offset = 1.5
        
        amp1 = np.sin(2 * np.pi * time / 4) + 0.2
        amp2 = np.sin(2 * np.pi * (time + rear_wave_offset) / 4) + 0.15
        
        glColor3f(0.0, 1.0, 1.0)
        glLineWidth(LINE_WIDTH_MEDIUM)
        glBegin(GL_LINE_STRIP)
        for x in np.linspace(-10, 10, 1000):
            y = self.wavelet_sharp(x, time, scale=1.0, frequency=3.0, amplitude=amp1)
            glVertex2f(x * self.x1_scale + self.wavelet_center_x, y * self.y1_scale*self.open_val + self.wavelet_center_y)
        glEnd()
        
        glColor3f(0.8, 0.8, 0.8)
        glLineWidth(LINE_WIDTH_THIN)
        glBegin(GL_LINE_STRIP)
        for x in np.linspace(-10, 10, 1000):
            y = self.wavelet(x, 0.5*time + rear_wave_offset, scale=1.0, frequency=3.0, amplitude=amp2)
            glVertex2f(x * self.x2_scale + self.wavelet_center_x, y * self.y2_scale*self.open_val + self.wavelet_center_y)
        glEnd()

    def set_wavelet_center(self, x_center, y_center):
        self.wavelet_center_x = x_center
        self.wavelet_center_y = y_center

    def set_noise_level(self, level):
        self.noise_level = level
 
class Face3:
    def __init__(self):
        # Initialize two eyes, one on the left and one on the right
        x_offset = 0.5  # Horizontal distance between the eyes
        y_position = 0.75

        self.left_eye = Eye(0.0 - x_offset, y_position, x_radius=EYE_RADIUS_X*1.1, y_radius=EYE_RADIUS_Y*0.8)
        self.right_eye = Eye(0.0 + x_offset, y_position)
        
        self.mouth = Mouth()
        self.eye_lower_bound = self.mouth.wavelet_center_y + EYE_RADIUS_Y + .01  # Buffer to ensure no overlap
        self.last_look_time = 0
        self.eye_radius_x = EYE_RADIUS_X
        self.eye_radius_y = EYE_RADIUS_X
        
        self.mid_bound = 0.2
        self.lelb = -1+self.eye_radius_x
        #left eye right bound
        self.lerb = -self.mid_bound-self.eye_radius_x
        #right eye right bound
        self.rerb = 1-self.eye_radius_x
        #right eye left bound
        self.relb = self.mid_bound+self.eye_radius_x
        
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.scanline_effect = WanderingScanLineEffect()
        self.vignette_effect = VignetteEffect()
        self.static_effect = StaticNoiseEffect()
        self.grid_effect = GridEffect()
        
        self.analog_mode_flag = DEFAULT_ANALOG_MODE
        
    def set_mode_to_analog(self):
        self.analog_mode_flag = True
        
    def set_mode_to_digital(self):
        self.analog_mode_flag = False
           
    def set_eye_target_position(self, x, y, duration_ms):
        # Ensure eyes don't cross over each other by maintaining a minimum distance
        left_eye_target_x = min(max(x, self.lelb), self.lerb)
        right_eye_target_x = max(min(x, self.rerb), self.relb)
        self.left_eye.set_target_position(left_eye_target_x, y, duration_ms)
        self.right_eye.set_target_position(right_eye_target_x, y, duration_ms)
        
    def set_smile_val(self, val):
        self.mouth.set_smile_val(val)
        self.left_eye.smile_val = val
        self.right_eye.smile_val = val
    
    def random_look(self, current_time):
        if self.last_look_time == 0:
            self.last_look_time = current_time
            return
        else:
            delta_time = current_time - self.last_look_time
            # Every few seconds, move the eyes to a new random position
            if delta_time >= random.randrange(10, 70)/10:  # Random interval
                random_x = random.randint(-10, 10)/10
                random_y = random.randint(0, 10)/10#float(random.randint(self.eye_lower_bound, WINDOW_HEIGHT - EYE_RADIUS_Y))/WINDOW_HEIGHT
                self.set_eye_target_position(random_x, random_y, EYE_MOVE_DURATION)
                # Update the time of the last movement
                self.last_look_time = current_time
            if delta_time >= random.randrange(30, 80)/10:  # Random interval
                self.left_eye.start_blink()
                
            if delta_time >= random.randrange(30, 100)/10:  # Random interval
                self.right_eye.start_blink()
                    # Move and update both eyes
        self.left_eye.move_eye(current_time)
        self.right_eye.move_eye(current_time)
    
    def draw_sleeping_face(self):
        pass
    def render_face(self):

        current_time = sys_time.time()
        self.random_look(current_time)

        self.left_eye.update()
        self.right_eye.update()

        # Make the mouth's X center follow the midpoint between both eyes
        midpoint_x = (self.left_eye.x_center_nom + self.right_eye.x_center_nom) / 2
        # self.mouth.set_mouth_open_val(2)
        self.mouth.set_wavelet_center(midpoint_x*2.5, -0.3)
        self.mouth.draw_mouth(current_time * 20)
        
        self.set_smile_val(-np.sin(0.5* current_time)*0.45)
        
        self.vignette_effect.overlay_vignette()
        self.scanline_effect.draw_scan_lines(current_time)
        if self.analog_mode_flag:
            #analog version
            self.static_effect.draw_static()
        else:
            #digital version
            self.grid_effect.overlay_grid()
            
    def update(self):
        self.render_face()

        