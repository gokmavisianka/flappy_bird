import pygame
import numpy as np
from random import randint


# The horizontal distance between two obstacles,
distance_between_obstacles = 300

# The minimum height of the any part of an obstacle,
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


class Floor:
    def __init__(self, color=(0, 0, 0)):
        self.color = color
    
    def draw(self):
        x, y = 0, screen.height
        width, height = screen.width, 1
        geometry = (x, y, width, height)
        pygame.draw.rect(screen.display, self.color, geometry)
    
    @staticmethod
    def check_collision(bird):
        if bird.position[1] + bird.radius > screen.height:
            return True
        else:
            return False


class Ceiling:
    def __init__(self, color(0, 0, 0)):
        self.x, self.y = 0,

    def draw(self):
        x, y = 0, 0
        width, height = screen.width, 1
        geometry = (x, y, width, height)
        pygame.draw.rect(screen.display, self.color, geometry)

    @staticmethod
    def check_collision(bird):
        if bird.position[1] - bird.radius < 0:
            return True
        else:
            return False


class Obstacles:
    def __init__(self):
        self.elements = []

    def draw_all(self):
        for obstacle in self.elements:
            obstacle.draw()

    def create(self):
        # x should be equal to or higher than screen width, or it will appear suddenly on screen.
        # y should be 0 or the height value of the ceiling.
        x, y = screen.width, 0
        # Width is constant, height differs but it has a minimum and maximum values.
        width, height = 100, randint(minimum_height, screen.height - gap - minimum_height)
        # Now, create the corners of lower part, gate and upper part.
        #
        # ----------A-------B----------
        #           | upper |
        #           | part  |
        #           |       |
        #           D-------C
        #    v^^v   
        #  >(Bird)>   >gate   ->   ->
        #    ^vv^          
        #           E-------F
        #           |       |
        #           | lower |
        #           | part  |
        # ----------H-------G----------
        #
        A = (x, y)
        B = (x + width, y)
        C = (x + width, y + height)
        D = (x, y + height)
        E = (x, y + height + gap)
        F = (x + width, y + height + gap),
        G = (x + width, screen.height)
        H = (x, screen.height)
        upper_part = np.array([A, B, C, D], dtype=float)
        gate = np.array([D, C, F, E], dtype=float)
        lower_part = np.array([E, F, G, H], dtype=float)
        # Note that, to draw the polygons properly, their vertices
        # need to be in clockwise or counter-clockwise order.
        # pygame.draw.polygon() will be used to draw lower and upper parts.
        # Drawing polygons is more expensive than drawing rectangles.
        # But using corner points (or vertices) makes our job easier.
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
        self.linear.velocity[:] = (-1, 0)
        # or,
        # self.linear.velocity = np.array((-1 , 0), dtype=float)
        self.color = color

    def draw(self):
        # Draw the lower part,
        pygame.draw.polygon(screen.display, self.color, self.lower_part)
        # Draw the upper part,
        pygame.draw.polygon(screen.display, self.color, self.upper_part)

    def move(self):
        # Apply the velocity for all corners.
        self.lower_part += self.linear.velocity
        self.upper_part += self.linear.velocity        

    def check_collision(self, bird):
        # Six different corners in total will be used to check collision.
        #
        # ------------A-------+ . . . . . +
        # .           | upper |           .
        # .    (1)    | part  |           . if bird is in the area (1), use the corners A & D.
        # .           |       |           .
        # . . . . . . D-------C           . if bird is in the area (2), use the corners D & E.
        # .           .       .           . 
        # .    (2)    .  (4)  .    (5)    . if bird is in the area (3), use the corners E & H.
        # .           .       .           . 
        # . . . . . . E-------F           . if bird is in the area (4), use the corners D, C, E & F.
        # .           |       |           .
        # .    (3)    | lower |           . if bird is in the area (5), use the corners C, & F.
        # .           | part  |           .
        # ------------H-------+ . . . . . +
        #
        A, B, C, D = self.upper_part
        E, F, G, H = self.lower_part
        if A[1] < bird.linear.position[1] < D[1] and bird.linear.position[0] + bird.radius > A[0]:
            return True  # Area (1)
        elif E[1] < bird.linear.position[1] < H[1] and bird.linear.position[0] + bird.radius > E[0]:
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


class Linear:
    def __init__(self):
        self.position = np.array((0, 0), dtype=float)
        self.velocity = np.array((0, 0), dtype=float)
        self.acceleration = np.array((0, -2.5), dtype=float)


class Bird:
    def __init__(self, position, radius):
        self.color = random_color()
        self.linear = Linear()
        self.linear.position[:] = position
        self.radius = radius
   
