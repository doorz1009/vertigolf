import cocos
import csv
import pyglet

bgLayer = cocos.layer.Layer()
gameLayer = cocos.layer.Layer()

layer = cocos.layer.Layer()

bg = pyglet.resource.image('Resources/golf_course.png')
bg_sprite = cocos.sprite.Sprite(bg)
bg_sprite.scale = 0.75
bgLayer.add(bg_sprite)

ball = pyglet.resource.image('Resources/golf_ball.png')
ball_sprite = cocos.sprite.Sprite(ball)
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