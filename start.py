import cocos
import cocos.layer as cl
import cocos.director as cd
import cocos.collision_model as cm
import cocos.sprite as csp
import cocos.euclid as eu
import csv
import pyglet.resource as pr

gameWindow = cd.director.init(width=1024, height=768)
bgLayer = cl.Layer()
gameLayer = cl.Layer()

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

class GolfBall(csp.Sprite):

    line = RubberBandLine()

    def __init__(self, image, center_x, center_y):
        super(GolfBall, self ).__init__(image)
        self.position = center_x, center_y
        self.scale = 0.1
        self.cshape = cm.CircleShape(eu.Vector2(center_x, center_y), image.width/ (2 / self.scale))

        gameWindow.push_handlers(self.on_mouse_press, self.on_mouse_drag, self.on_mouse_release)

    def does_contain_point(self, pos):
        return (
            (abs(pos[0] - self.cshape.center[0]) < self.cshape.r) and
            (abs(pos[1] - self.cshape.center[1]) < self.cshape.r))

    def on_mouse_press(self, x, y, buttons, modifiers):
        gameLayer.add(self.line)
        px, py = cd.director.get_virtual_coordinates (x, y)
        if self.does_contain_point((px, py)):
            self.line.update_start((px, py))
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        px, py = cd.director.get_virtual_coordinates (x, y)
        if self.line.start != (0, 0) and self.line.end != (0, 0):
            self.line.update_end((px, py))

    def on_mouse_release(self, x, y, button, modifiers):
        line_info = self.line.get_line_info()
        self.line.snap()

class TerrainSprite(csp.Sprite):

    def __init__(self, image, center_x, center_y, hieght, width):
        super(TerrainSprite, self).__init__()


bg = pr.image('Resources/golf_course.png')
bg_sprite = csp.Sprite(bg)
bg_sprite.scale = 0.75
bgLayer.add(bg_sprite)

ball = pr.image('Resources/golf_ball.png')
ball_sprite = GolfBall(ball, 900, 100)
ball_sprite.position = 900, 100
ball_sprite.scale = 0.1

grass = pr.image('Resources/grass.png')

with open('level.dat') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=",")
    for row in csv_reader:
        grass_sprite = csp.Sprite(grass)
        grass_sprite.position = int(row[0]), int(row[1])
        grass_sprite.rotation = int(row[2])
        grass_sprite.scale = 0.25
        gameLayer.add(grass_sprite)

gameLayer.add(ball_sprite)

main_scene = cocos.scene.Scene (bgLayer, gameLayer)
cocos.director.director.run (main_scene)