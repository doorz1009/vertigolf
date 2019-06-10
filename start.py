import cocos
import cocos.layer as cl
import cocos.director as cd
import cocos.actions.move_actions as cmove
import cocos.collision_model as cm
import cocos.sprite as csp
import cocos.euclid as eu
import csv
import xml.etree.ElementTree as et
import pyglet

gameWindow = cd.director.init(width=1248, height=816)
bgLayer = cl.Layer()
game_layer = cl.Layer()
gravity = -0.2
tile_size = 48

class RubberBandLine(cocos.draw.Line):
    
    def __init__(self, x=0, y=0):
        super(RubberBandLine, self).__init__((0, 0), (0, 0), (0, 0, 0, 255), stroke_width = 1)

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
        print(str(self.x_velocity))
        print(str(self.y_velocity))
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

        self.target.position = (new_x_pos, new_y_pos)     # Set target's position.

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
    live_instances = {} # map unique_id to instance with that id

    @staticmethod
    def handleCollisions():
        """ """
        objects = GameSprite.live_instances.values()
        for object in objects:
            for other_object in objects:
                if other_object.id != object.id and object.type == 'ball' and\
                        object.isHitByCircle(other_object.position,\
                        other_object.cshape):
                    object.onCollision(other_object)
    @staticmethod

    def __init__(self, image, type, id=None, position=(0, 0), scale=1):
        """ """
        super( GameSprite, self ).__init__( image, position, scale)
        if not id:
            self.id = GameSprite.next_unique_id
        else:
            self.id = id
        
        GameSprite.next_unique_id += 1
        self.type = type
        GameSprite.live_instances[self.id] = self
    
    def detectCollision(self, geom, center, r, is_hole):
        """ Returns True if and only if the receiver's circle 
            calculated using the receiver's position and radius 
            overlaps the circle calculated using the center and radius 
            arguments to this method. 
        """
        if is_hole == False:
            top_line = self.dist(geom[0], center, r)
            bottom_line = self.dist(geom[2], center, r)
            right_line = self.dist(geom[1], center, r)
            left_line = self.dist(geom[3], center, r)
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

    def __init__(self, image_id, position=(0,0), is_hole=False):
        super(TerrainSprite, self).__init__(mapped_tileset[image_id], 'grass', None, position)
        self.position = position
        x = position[0]
        y = position[1]
        self.is_hole = is_hole

        if image_id == 20 or image_id == 27:
            self.cshape = None
        if image_id == 6:
            # self.cshape = rect(hole_geom)
            self.cshape = (((x-24, y+24), (x +24, y + 24)),\
                           ((x + 24, y + 24), (x + 24, y-24)),\
                           ((x - 24, y - 24), (x + 24, y-24)),\
                           ((x - 24, y + 24), (x - 24, y - 24)))
        else:
            # Line order:
            # top-left -> top-right
            # top-right V bottom-right
            # bottom-left -> bottom-right
            # top-left V bottom-left
            self.cshape = (((x - 24, y + 24), (x + 24, y + 24)),\
                           ((x + 24, y + 24), (x + 24, y - 24)),\
                           ((x - 24, y - 24), (x + 24, y - 24)),\
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
cocos.director.director.run (main_scene)