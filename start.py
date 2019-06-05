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

class GolfBall(csp.Sprite):

    def __init__(self, center_x, center_y):
        ball = pyglet.resource.image('Resources/golf_ball.png')
        super(GolfBall, self ).__init__(ball)
        self.position = center_x, center_y
        self.line = RubberBandLine()
        self.scale = 0.1
        self.cshape = cm.CircleShape(eu.Vector2(center_x, center_y), ball.width/ (2 / self.scale))

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

class TerrainSprite(csp.Sprite):

    def __init__(self, image, position=(0,0)):
        super(TerrainSprite, self).__init__(image)
        self.position = position


bg = pyglet.resource.image('Resources/golf_course.png')
bg_sprite = csp.Sprite(bg)
bg_sprite.scale = 0.75
bgLayer.add(bg_sprite)

ball = pyglet.resource.image('Resources/golf_ball.png')
ball_sprite = GolfBall(900, 100)
ball_sprite.position = 900, 100
ball_sprite.scale = 0.1

grass = pyglet.resource.image('Resources/grass.png')


tree = et.parse('Resources/Level1.tmx')
root = tree.getroot()
data = root.find('layer/data').text
data = data.replace('\n', '')
data_list = data.split(",")

tile_set = pyglet.resource.image('Resources/grassTileSet.png')
mapped_tileset = pyglet.image.ImageGrid(tile_set, 4, 7)


x = 24
y = 792
for tile_id in data_list:
    tid = int(tile_id)
    if tid:
        converted_id = (7 * (4 - (tid / 7))) - (7 - (tid % 7))
        print(str(converted_id) + ' at (' + str(x % 1248) + ','+ str(y % 816) + ')')
        # print(str(tid) + '\t' + str(converted_id) + ' \tx:' + str(x % 1248) + ' \ty:' + str(y % 816))
        game_layer.add(TerrainSprite(mapped_tileset[tid - 1], ((x % 1248), (y % 816))))
    x += 48
    if x % 1272 == 0:
        y -= 48

# with open('level.dat') as csv_file:
#     csv_reader = csv.reader(csv_file, delimiter=",")
#     for row in csv_reader:
#         grass_sprite = csp.Sprite(grass)
#         grass_sprite.position = int(row[0]), int(row[1])
#         grass_sprite.rotation = int(row[2])
#         grass_sprite.scale = 0.25
#         game_layer.add(grass_sprite)

game_layer.add(ball_sprite)

main_scene = cocos.scene.Scene(bgLayer, game_layer)
cocos.director.director.run (main_scene)