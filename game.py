import pygame
import numpy as np
from random import randint
from time import sleep, perf_counter


pygame.init()

# The horizontal distance between two obstacles,
distance_between_obstacles = 300

# The minimum height of any part of an obstacle,
minimum_height = 100

# The vertical distance between lower and upper parts of an obstacle,
gap = 200


def random_color(start=100, end=200):
    r = randint(start, end)
    g = randint(start, end)
    b = randint(start, end)
    return r, g, b


def hypotenuse(Vector2D):
    # This function is only valid for two dimensions as the name of the parameter suggests.
    # np.hypot() can be used for three or more dimensions.
    x, y = Vector2D
    return (x ** 2 + y ** 2) ** 0.5


class Linear:
    def __init__(self):
        self.position = np.array((0, 0), dtype=float)
        self.velocity = np.array((0, 0), dtype=float)
        self.acceleration = np.array((0, 0.5), dtype=float)


class Text:
    def __init__(self, base_string, function, color=(255, 0, 0)):
        # base_string can be "FPS: " or "Score: " to represent the remaining part.
        self.base_string = base_string
        self.color = color
        # function is used to get the remaining part (It can be fps value or score etc.) of the string.
        # So {base_string + remaining} will be shown on the screen.
        self.function = function
        # Size of the font can be changed.
        self.font = pygame.font.SysFont("Helvetica", 32)

    def show(self, display, position, string=None):
        # If a string is given, use that. Otherwise, use the base_string and add the remaining part to it.
        if string is None:
            string = self.base_string
            remaining = self.function()
            # Check if the type of the remaining part is str. If not, Convert it to the str type before merging strings.
            if type(remaining) is str:
                string += remaining
            else:
                string += str(remaining)
        text = self.font.render(string, True, self.color)
        display.blit(text, position)


class Screen:
    def __init__(self, background_color=(100, 100, 100), resolution=(1000, 750)):
        self.background_color = background_color
        self.width, self.height = resolution
        self.display = pygame.display.set_mode(resolution)
        self.FPS = self.FPS()

    def fill(self, color=None):
        if color is None:
            color = self.background_color
        # fill the screen with specific color.
        self.display.fill(color)

    @staticmethod
    def update():
        # Update the whole window.
        pygame.display.flip()

    class FPS:
        def __init__(self):
            self.clock = pygame.time.Clock()
            self.text = Text(base_string="FPS: ", function=self.get)

        def set(self, value):
            self.clock.tick(value)

        def get(self):
            return int(self.clock.get_fps())  # clock.get_fps() returns a float.


class Score:
    def __init__(self):
        self.text = Text(base_string="Score: ", function=self.get)
        self.value = 0

    def add(self, value):
        self.value += value

    def get(self):
        return self.value


class Floor:  # Static Obstacle.
    def __init__(self, color=(0, 0, 0)):
        self.color = color
        self.x, self.y = 0, screen.height - 35
        self.width, self.height = screen.width, 35
    
    def draw(self):
        geometry = (self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen.display, self.color, geometry)
    
    def check_collision(self, bird):
        if bird.linear.position[1] + bird.radius > screen.height - self.height:
            return True
        else:
            return False


class Ceiling:  # Static Obstacle.
    def __init__(self, color=(0, 0, 0)):
        self.color = color
        self.x, self.y = 0, 0
        self.width, self.height = screen.width, 35

    def draw(self):
        geometry = (self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen.display, self.color, geometry)

    def check_collision(self, bird):
        if bird.linear.position[1] - bird.radius < self.height:
            return True
        else:
            return False


class Obstacles:  # Dynamic Obstacle.
    def __init__(self):
        self.elements = []

    def draw_all(self):
        for obstacle in self.elements:
            obstacle.draw()

    def move_all(self):
        for obstacle in self.elements:
            obstacle.move()

    def create(self):
        # x should be equal to or higher than screen width, or it will appear suddenly on screen.
        # y should be 0 or the height value of the ceiling.
        x, y = screen.width, 0
        # Width is constant, height differs but it has a minimum and maximum values.
        width, height = 100, randint(minimum_height, screen.height - gap - minimum_height)
        #
        # Now, create the corners of lower part, gate and upper part.
        #
        # ----------A------B----------
        #           | upper|
        #           | part |
        #           |      |
        #           D------C
        #    v^^v   
        #   (Bird)>   gate   ->   ->
        #    ^vv^          
        #           E------F
        #           |      |
        #           | lower|
        #           | part |
        # ----------H-------G----------
        #
        A = [x, y]
        B = [x + width, y]
        C = [x + width, y + height]
        D = [x, y + height]
        E = [x, y + height + gap]
        F = [x + width, y + height + gap]
        G = [x + width, screen.height]
        H = [x, screen.height]
        upper_part = np.array([A, B, C, D], dtype=float)
        gate = np.array([D, C, F, E], dtype=float)
        lower_part = np.array([E, F, G, H], dtype=float)
        # Note that, to draw the polygons properly, their vertices
        # need to be in clockwise or counter-clockwise order.
        # pygame.draw.polygon() can be used to draw lower and upper parts.
        # But drawing polygons is more expensive than drawing rectangles.
        # So you might consider using pygame.draw.rect() for drawing.
        obstacle = Obstacle(upper_part, gate, lower_part)
        self.elements.append(obstacle)


class Obstacle:
    def __init__(self, upper_part, gate, lower_part, color=(0, 0, 0)):
        self.lower_part = lower_part
        self.gate = gate
        self.upper_part = upper_part
        self.linear = Linear()
        # linear.position won't be used since we are gonna use the corner points.
        # As default, set the linear velocity as Vector2D(-1, 0).
        self.linear.velocity[:] = (-3, 0)
        # or,
        # self.linear.velocity = np.array((-1 , 0), dtype=float)
        self.birds_passed = []  # The list of birds which passed this obstacle.
        self.color = color

    def draw(self):
        # If you want to improve the performance, use this function.
        # It uses pygame.draw.rect() instead of pygame.draw.polygon().
        #
        # Remember that,
        # A = [x, y],
        # C = [x + width, y + height],
        # So, (C - A) gives us [width, height of the upper part].
        #
        # The same can be considered for points E and G.
        # E = [x, y + gap + height],
        # G = [x + width, screen.height]
        # So, (G - E) gives us [width, height of the lower part].
        #
        A, C = self.upper_part[0], self.upper_part[2]
        pygame.draw.rect(screen.display, self.color, (A, C - A))
        E, G = self.lower_part[0], self.lower_part[2]
        pygame.draw.rect(screen.display, self.color, (E, G - E))

    def alternate_draw(self):
        # Draw the lower part,
        pygame.draw.polygon(screen.display, self.color, self.lower_part)
        # Draw the upper part,
        pygame.draw.polygon(screen.display, self.color, self.upper_part)

    def move(self):
        # Apply the velocity for all corners.
        self.lower_part += self.linear.velocity
        self.upper_part += self.linear.velocity
        #
        # Remove the obstacle from the obstacles.elements if it is out of view.
        #
        # -A------B---+-------------------------------------+-
        #  | upper|   |                                     | 
        #  | part |   |                                     |
        #  |      |   |                                     |
        #  D------C   |                                     |
        #             |                                     | 
        # Out of View |            (Game Window)            |
        #             |                                     |       
        #  D------F   |                                     |
        #  |      |   |                                     | 
        #  | lower|   |                                     |
        #  | part |   |                                     |
        # -H------G---+-------------------------------------+-
        #         .   .                                     .
        #         .   .                                     .
        #         v   v                                     v
        #        (x) (0)                             (screen.width)       
        #
        G = self.upper_part[2]
        x = G[0]
        if x < 0:
            obstacles.elements.remove(self)
        

    def check_pass(self, bird):
        #
        # Add 1 to the score if the bird passed the obstacle successfully.
        #
        # -A------B----------------- - - -
        #  | upper|                                         
        #  | part |                                        
        #  |      |                                        
        #  D------C                                        
        #               v^^v                                     
        #    gate      (Bird)>     
        #              .^vv^                                    
        #  D------F    .                                 
        #  |      |    .                                 
        #  | lower|    .                                 
        #  | part |    .                                 
        # -H------G----.------------ - - -
        #         .    .                                 
        #         .    .                                  
        #         v    v                                 
        #        (x)  (bird.linear.position[0] - bird.radius)
        #
        G = self.upper_part[2]
        x = G[0]
        if bird not in self.birds_passed:
            if x < bird.linear.position[0] - bird.radius:
                self.birds_passed.append(bird)
                score.add(1)

    def check_position(self):
        # This function is only applied for the last obstacle in the obstacles.elements.
        # If the horizontal distance between the point G and the screen width is less than
        # or equal to the distance_between_obstacles, then create a new obstacle.
        #          
        # -A------B--------------------------------------A------B-
        #  | upper|                                      | upper|
        #  | part |                                      | part |
        #  |      |                                      |      |
        #  D------C                                      D------C 
        #         .                                      .
        #         <~~~~~ distance_between_obstacles ~~~~~> 
        #         .                                      .      
        #  D------F                                      D------F
        #  |      |                                      |      |
        #  | lower|                                      | lower| 
        #  | part |                                      | part |
        # -H------G--------------------------------------H------G-
        #         .                                      .
        #         .                                      .
        #         v                                      v
        #        (x)                              (screen.width)
        #
        G = self.lower_part[2]
        x = G[0]
        if screen.width - x >= distance_between_obstacles:
            obstacles.create()

    def check_collision(self, bird):
        # Six different corners in total will be used to check collision.
        #
        # +-----------A-------+-----------+
        # .           | upper |           .
        # .    (1)    | part  |           . if bird is in the area (1), use the corners A, D & C.
        # .           |       |           .
        # . . . . . . D-------C           . if bird is in the area (2), use the corners D & E.
        # .           .       .           . 
        # .    (2)    .  (4)  .    (5)    . if bird is in the area (3), use the corners E, H & F.
        # .           .       .           . 
        # . . . . . . E-------F           . if bird is in the area (4), use the corners D, C, E & F.
        # .           |       |           .
        # .    (3)    | lower |           . if bird is in the area (5), use the corners C, & F.
        # .           | part  |           .
        # +-----------H-------+-----------+
        #
        A, B, C, D = self.upper_part
        E, F, G, H = self.lower_part
        if A[1] < bird.linear.position[1] < D[1] and C[0] > bird.linear.position[0] + bird.radius > A[0]:
            return True  # Area (1)
        elif E[1] < bird.linear.position[1] < H[1] and F[0] > bird.linear.position[0] + bird.radius > E[0]:
            return True  # Area (3)
        elif D[0] < bird.linear.position[0] < C[0] and bird.linear.position[1] - bird.radius < D[1]:
            return True  # Area (4)
        elif E[0] < bird.linear.position[0] < F[0] and bird.linear.position[1] + bird.radius > E[1]:
            return True  # Area (4)
        else:
            for corner in (D, E, C, F):
                difference = corner - bird.linear.position
                distance = hypotenuse(difference)
                if distance < bird.radius:
                    return True  # Area (2) or Area(5)
        return False                                                                                          


class Bird:
    def __init__(self, position, radius):
        self.color = random_color()
        self.linear = Linear()
        self.linear.position[:] = position
        self.radius = radius
    
    def draw(self):
        pygame.draw.circle(screen.display, self.color, self.linear.position, self.radius)

    def jump(self):
        self.linear.velocity[1] = -9

    def update(self):
        self.linear.velocity += self.linear.acceleration
        self.linear.position += self.linear.velocity


class Keyboard:
    @staticmethod
    def update():
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                # Press 'Space' to jump.
                if event.key == pygame.K_SPACE:
                    bird.jump()
                # Press 'Q' to quit.
                elif event.key == pygame.K_q:
                    pygame.quit()
                    quit()


screen = Screen()
bird = Bird(position=(150, 350), radius=30)
obstacles = Obstacles()
obstacles.create()
floor = Floor()
ceiling = Ceiling()
keyboard = Keyboard()
score = Score()

while True:
    screen.fill()
    obstacles.move_all()
    obstacles.draw_all()
    obstacles.elements[-1].check_position()
    ceiling.draw()
    floor.draw()
    bird.update()
    bird.draw()
    if floor.check_collision(bird) or ceiling.check_collision(bird):
        print("Collision!")
    for obstacle in obstacles.elements[:2]:
        obstacle.check_pass(bird)
        if obstacle.check_collision(bird):
            print("Collision!")
    keyboard.update()
    screen.FPS.set(60)
    screen.FPS.text.show(screen.display, position=(0, 0))
    score.text.show(screen.display, position=(0, screen.height - 37))
    screen.update()
        
