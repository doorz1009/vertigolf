import cocos
import csv
import pyglet

gameWindow = cocos.director.director.init(width=1024, height=768)
bgLayer = cocos.layer.Layer()
gameLayer = cocos.layer.Layer()

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

class GolfBall(cocos.sprite.Sprite):

    line = RubberBandLine()

    def __init__(self, image):
        super(GolfBall, self ).__init__(image)

        gameWindow.push_handlers(self.on_mouse_press, self.on_mouse_drag, self.on_mouse_release)

    def does_contain_point(self, pos):
        return (
           (abs(pos[0] - self.position[0]) < self.image.width/2) and
           (abs(pos[1] - self.position[1]) < self.image.width/2))

    def on_mouse_press(self, x, y, buttons, modifiers):
        gameLayer.add(self.line)
        px, py = cocos.director.director.get_virtual_coordinates (x, y)
        if self.does_contain_point((px, py)):
            self.line.update_start((px, py))
    
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        px, py = cocos.director.director.get_virtual_coordinates (x, y)
        if self.line.start != (0, 0) and self.line.end != (0, 0):
            self.line.update_end((px, py))

    def on_mouse_release(self, x, y, button, modifiers):
        line_info = self.line.get_line_info()
        self.line.snap()

bg = pyglet.resource.image('Resources/golf_course.png')
bg_sprite = cocos.sprite.Sprite(bg)
bg_sprite.scale = 0.75
bgLayer.add(bg_sprite)

ball = pyglet.resource.image('Resources/golf_ball.png')
ball_sprite = GolfBall(ball)
ball_sprite.position = 900, 100
ball_sprite.scale = 0.1

grass = pyglet.resource.image('Resources/grass.png')

with open('level.dat') as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=",")
    for row in csv_reader:
        grass_sprite = cocos.sprite.Sprite(grass)
        grass_sprite.position = int(row[0]), int(row[1])
        grass_sprite.rotation = int(row[2])
        grass_sprite.scale = 0.25
        gameLayer.add(grass_sprite)

gameLayer.add(ball_sprite)

main_scene = cocos.scene.Scene (bgLayer, gameLayer)
cocos.director.director.run (main_scene)