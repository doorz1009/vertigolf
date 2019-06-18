import cocos
import cocos.layer as cl
import cocos.director as cd
import cocos.actions.move_actions as cmove
import cocos.collision_model as cm
import cocos.sprite as csp
import cocos.euclid as eu
import csv
import math
import xml.etree.ElementTree as et
import numpy
import numpy.linalg as la
import pyglet
from typing import List, Any

gameWindow = cd.director.init(width=1248, height=816)
bgLayer = cl.Layer()
game_layer = cl.Layer()
gravity = -0.2
tile_size = 48


class RubberBandLine(cocos.draw.Line):

    def __init__(self, x=0, y=0):
        super(RubberBandLine, self).__init__((0, 0), (0, 0), (0, 0, 0, 255), stroke_width=1)

    def update_start(self, start):
        self.start = start
        self.end = start

    def update_end(self, end):
        self.end = end

    def get_line_info(self):
        return (self.start, self.end)

    def snap(self):
        self.start = (0, 0)
        self.end = (0, 0)


class GravityAction(cmove.Move):

    def __init__(self, pos, force):
        super(GravityAction, self).__init__()
        # Get our local variables set from 
        self.x_velocity = (force[0][0] - force[1][0]) / 10
        self.y_velocity = (force[0][1] - force[1][1]) / 10
        self.start_pos = pos
        self.scheduled_to_remove = False

    def start(self):
        (x, y) = self.start_pos

        # self.target is the Node being animated by this Action
        self.target.position = (x, y)  # Start at top of window

    def step(self, dt):
        self.y_velocity += gravity
        (x, y) = self.target.position

        new_y_pos = y + self.y_velocity
        new_x_pos = x + self.x_velocity
        coll_info = self.target.handleCollisions((x, y), self.target.cshape.r,
                                                 ((x, y), (x + self.x_velocity, y + self.y_velocity)))

        if len(coll_info):
            print ('')

        # if ('horizontal' in coll_info[0]):
        #     if self.y_velocity != 0:
        #         self.y_velocity *= -0.5
        #     if self.y_velocity < 0.2:
        #         self.y_velocity = 0
        #
        #     if self.x_velocity != 0:
        #         self.x_velocity *= 0.999
        #     if self.x_velocity < 0.01:
        #         self.x_velocity = 0

        new_y_pos = y + self.y_velocity
        new_x_pos = x + self.x_velocity
        #
        # if ('vertical' in coll_info[0]):
        #     if self.x_velocity != 0:
        #         self.x_velocity *= -0.8
        #     if self.x_velocity ** 2 < 0.1:
        #         self.x_velocity = 0
        #
        #     new_x_pos = x + self.x_velocity

        # if 'vertical' in coll_info[0] and 'horizontal' in coll_info[0]:
        #     print('corner collision detected')

        self.target.position = (new_x_pos, new_y_pos)  # Set target's position.
        self.target.cshape.center = (new_x_pos, new_y_pos)  # Set target's position.

        if self.x_velocity == 0 and self.y_velocity == 0:
            self.target.stop()


class GameSprite(cocos.sprite.Sprite):
    """
    This class exists to provide several features shared by almost
    every game object.
    
    Each instance has the following:
    A unique identifier
    A motion vector to describe how the instances should move.
    A radius used to detect collisions with other GameSprite 
        instances
    A flag, shouldDie, used to signal when the instance should be
    removed from the game.
    
    Instances automatically move according to each instance's
    motion vector. Positions "wrap" meaning that if an instance moves 
    off the screen, it reappears on the opposite side of the screen.
    """
    next_unique_id = 1
    live_instances = {}  # map unique_id to instance with that id

    @staticmethod
    def handleCollisions(center, radius, vel):
        """ """
        objects = GameSprite.live_instances.values()
        coll_info = ['none', 100]
        ret_coll = []  # type: List[float]
        for sprite in objects:
            if sprite.type != 'ball':
                reflect_angle = sprite.detectCollision(sprite.cshape, center, radius, vel, False)
                if reflect_angle[0] != 'none':
                    ret_coll[len(ret_coll)] = reflect_angle
        return ret_coll

    def __init__(self, image, type, id=None, position=(0, 0), scale=1):
        """ """
        super(GameSprite, self).__init__(image, position, scale)
        if not id:
            self.id = GameSprite.next_unique_id
        else:
            self.id = id

        GameSprite.next_unique_id += 1
        self.type = type
        GameSprite.live_instances[self.id] = self

    @staticmethod
    def dist(line, center, radius):
        # Params:
        # center = (x, y) [tuple]
        # line = ((x1, y1), (x2, y2)) [tuple of tuples]
        x = center[0]   # type: int
        y = center[1]   # type: int
        x1 = line[0][0] # type: int
        x2 = line[1][0] # type: int
        y1 = line[0][1] # type: int
        y2 = line[1][1] # type: int

        if x1 == x2:
            # if x1 = x2 then we are dealing with a vertical line
            if (y1 + radius < y) or (y2 - radius > y):
                return radius + 1000
            else:
                minDist = min(math.sqrt((x - x1) ** 2 + (y - y1) ** 2),
                              math.sqrt((x - x2) ** 2 + (y - y2) ** 2),
                              abs(x - x1))
                return minDist

        else:
            # Otherwise we are dealing with a horizontal line
            if (x1 - radius > x) or (x2 + radius < x):
                return radius + 1000
            else:
                minDist = min(math.sqrt((x - x1) ** 2 + (y - y1) ** 2),
                              math.sqrt((x - x2) ** 2 + (y - y2) ** 2),
                              abs(y - y1))
                return minDist

    def euclDist(self, a, b):
        return numpy.sqrt(((a[0] - b[0])**2 + (a[1] - b[1])**2))

    def closestPlaceOnLine(self, line, point):
        x = point[0]
        y = point[1]
        x1 = line[0][0]
        x2 = line[1][0]
        y1 = line[0][1]
        y2 = line[1][1]

        A1 = float(y2 - y1)
        B1 = float(x2 - x1)
        C1 = (y2 - y1) * x1 + (x1 - x2) * y1
        C2 = -B1 * x + A1 * y
        det = A1 * A1 - -B1 * B1

        if det != 0:
            cx = (float)((A1 * C1 - B1 * C2) / det)
            cy = (float)((A1 * C2 - -B1 * C1) / det)
            return (cx, cy)
        else:
            cx = x
            cy = y
            return (cx, cy)

    def lineSegIntersect(self, line1, line2):
        # calculate line info for first line
        l1_x1 = line1[0][0]
        l1_x2 = line1[1][0]
        l1_y1 = line1[0][1]
        l1_y2 = line1[1][1]

        A1 = l1_y2 - l1_y1
        B1 = l1_x1 - l1_x2
        C1 = A1 * l1_x1 + B1 * l1_y1

        # calculate line info for second line
        l2_x1 = line2[0][0]
        l2_x2 = line2[1][0]
        l2_y1 = line2[0][1]
        l2_y2 = line2[1][1]

        A2 = l2_y2 - l2_y1
        B2 = l2_x1 - l2_x2
        C2 = A2 * l2_x1 + B2 * l2_y1

        det = A1 * B2 - A2 * B1
        if (det == 0):
            # // Lines are parallel
            return 'parallel'
        else:
            x = (B2 * C1 - B1 * C2) / det
            y = (A1 * C2 - A2 * C1) / det
            # Return where intersection will occur, determine if it is within radius later.
            return (x, y)

    def detectCollision(self, geom = ((0, 0), (0, 0)), center = (0.0, 0.0), r = 0, vel = (0.0, 0.0), is_hole = False):
        """ Returns True if and only if the receiver's circle 
            calculated using the receiver's position and radius 
            overlaps the circle calculated using the center and radius 
            arguments to this method.
            :param geom - n line segments represented as two points
        """
        if is_hole == False:
            for line in geom:
                a = self.lineSegIntersect(line, vel)
                b = self.closestPlaceOnLine(line, vel[1])
                c = self.closestPlaceOnLine(vel, line[0])
                d = self.closestPlaceOnLine(vel, line[1])
                p1 = self.closestPlaceOnLine(line, center)
                vel_abs = self.euclDist(vel[0], vel[1])
                p2 = (0.0, 0.0)
                if ((a != 'parallel' and self.euclDist(a, center) < vel_abs) or self.euclDist(b, vel[1]) < r or
                        self.euclDist(c, line[0]) < r or self.euclDist(d, line[1]) < r):
                    if (line[0][0] <= a[0] and a[0] <= line[1][0]) and \
                        (line[1][0] <= a[1] and a[1] <= line[1][1]):
                        vel_mod = vel / vel_abs
                        a_c = self.euclDist(a, center)
                        p1_c = self.euclDist(p1, center)
                        diff = a_c / p1_c
                        first_two = (r * (self.euclDist(a, center) / self.euclDist(p1, center)))
                        anti_vel_vect = first_two * vel_mod
                        p2 = a - anti_vel_vect
            top_line = self.closestPlaceOnLine(geom[0], center)
            bottom_line = self.closestPlaceOnLine(geom[2], center)
            right_line = self.closestPlaceOnLine(geom[1], center)
            left_line = self.closestPlaceOnLine(geom[3], center)
            coll_type = ''
            min_dist = 100
            if top_line < r or bottom_line < r:
                # Collision with horizontal surface
                coll_type += 'horizontal'
                min_dist = min(top_line, bottom_line)
            if right_line < r or left_line < r:
                # Collision with vertical surface
                coll_type += 'vertical'
                min_dist = min(min_dist, left_line, right_line)
            if coll_type == '':
                coll_type = 'none'
            return [coll_type, min_dist]


class GolfBall(GameSprite):

    def __init__(self, image, center):
        super(GolfBall, self).__init__(image, 'ball', None, center)
        self.position = center
        self.line = RubberBandLine()
        self.scale = 1
        self.cshape = cm.CircleShape(((center[0]), (center[1])), 8 * self.scale)
        self.schedule_to_stop = False

        self.do(GravityAction(self.position, (self.position, self.position)))

        gameWindow.push_handlers(self.on_mouse_press, self.on_mouse_drag, self.on_mouse_release)

    def does_contain_point(self, pos):
        return (
                (abs(pos[0] - self.cshape.center[0]) < self.cshape.r) and
                (abs(pos[1] - self.cshape.center[1]) < self.cshape.r))

    def on_mouse_press(self, x, y, buttons, modifiers):
        game_layer.add(self.line)
        px, py = cd.director.get_virtual_coordinates(x, y)
        if self.does_contain_point((px, py)):
            self.line.update_start((px, py))

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        px, py = cd.director.get_virtual_coordinates(x, y)
        if self.line.start != (0, 0) and self.line.end != (0, 0):
            self.line.update_end((px, py))

    def on_mouse_release(self, x, y, button, modifiers):
        if self.line.start != (0, 0) and self.line.end != (0, 0):
            line_info = self.line.get_line_info()
            self.line.snap()
            self.do(GravityAction(self.position, line_info))


class TerrainSprite(GameSprite):

    def __init__(self, image_id, position=(0, 0), is_hole=False):
        super(TerrainSprite, self).__init__(mapped_tileset[image_id], 'grass', None, position)
        self.position = position
        x = position[0]
        y = position[1]
        self.is_hole = is_hole

        if image_id == 20 or image_id == 27:
            self.cshape = None
        if image_id == 6:
            # self.cshape = rect(hole_geom)
            self.cshape = (((x - 24, y + 24), (x + 24, y + 24)),
                           ((x + 24, y + 24), (x + 24, y - 24)),
                           ((x - 24, y - 24), (x + 24, y - 24)),
                           ((x - 24, y + 24), (x - 24, y - 24)))
        else:
            # Line order:
            # top-left -> top-right
            # top-right V bottom-right
            # bottom-left -> bottom-right
            # top-left V bottom-left
            self.cshape = (((x - 24, y + 24), (x + 24, y + 24)),
                           ((x + 24, y + 24), (x + 24, y - 24)),
                           ((x - 24, y - 24), (x + 24, y - 24)),
                           ((x - 24, y + 24), (x - 24, y - 24)))


bg = pyglet.resource.image('Resources/golf_course.png')
bg_sprite = csp.Sprite(bg)
bg_sprite.scale = 0.75
bgLayer.add(bg_sprite)

tree = et.parse('Resources/Level1.tmx')
root = tree.getroot()
data = root.find('layer/data').text
data = data.replace('\n', '')
data_list = data.split(",")

tile_set = pyglet.resource.image('Resources/tiles_for_loading.png')
mapped_tileset = pyglet.image.ImageGrid(tile_set, 4, 7)

x = 24
y = 792
for tile_id in data_list:
    tid = int(tile_id)
    if tid != 0:
        if tid == 14:
            game_layer.add(GolfBall(mapped_tileset[tid - 1], ((x % 1248), (y % 816))))
        else:
            game_layer.add(TerrainSprite(tid - 1, ((x % 1248), (y % 816)), False))
    x += 48
    if (x - 24) % 1248 == 0:
        y -= 48

main_scene = cocos.scene.Scene(bgLayer, game_layer)
cocos.director.director.run(main_scene)
