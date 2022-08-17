import enum
import pygame
import os
import math
import sys
import neat
from sys import exit
import random

pygame.init()
clock = pygame.time.Clock()

# Window
win_height = 720
win_width = 551
window = pygame.display.set_mode((win_width, win_height))

# Images
bird_images = [pygame.image.load("assets/bird_down.png"),
               pygame.image.load("assets/bird_mid.png"),
               pygame.image.load("assets/bird_up.png")]
skyline_image = pygame.image.load("assets/background.png")
ground_image = pygame.image.load("assets/ground.png")
top_pipe_image = pygame.image.load("assets/pipe_top.png")
bottom_pipe_image = pygame.image.load("assets/pipe_bottom.png")
game_over_image = pygame.image.load("assets/game_over.png")
start_image = pygame.image.load("assets/start.png")

# Game
scroll_speed = 1
bird_start_position = (100, 250)
score = 0
font = pygame.font.SysFont('Segoe', 26)
game_stopped = True


class Bird(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = bird_images[0]
        self.rect = self.image.get_rect()
        self.rect.center = bird_start_position
        self.image_index = 0
        self.vel = 0
        self.flap = False
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.alive = True
        self.points = 0

    def scoring(self):
        self.points += 1

    def update(self, user_input):
        # Animate Bird
        if self.alive:
            self.image_index += 1
        if self.image_index >= 30:
            self.image_index = 0
        self.image = bird_images[self.image_index // 10]

        # Gravity and Flap
        self.vel += 0.5
        if self.vel > 7:
            self.vel = 7
        if self.rect.y < 500:
            self.rect.y += int(self.vel)
        if self.vel == 0:
            self.flap = False

        # Rotate Bird
        self.image = pygame.transform.rotate(self.image, self.vel * -7)

        # User Input
        if user_input and not self.flap and self.rect.y > 0 and self.alive:
            self.flap = True
            self.vel = -7


class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, image, pipe_type):
        pygame.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y
        self.enter, self.exit, self.passed = False, False, False
        self.pipe_type = pipe_type

    def update(self):
        # Move Pipe
        self.rect.x -= scroll_speed
        if self.rect.x <= -win_width:
            self.kill()
          
class Ground(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = ground_image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = x, y

    def update(self):
        # Move Ground
        self.rect.x -= scroll_speed
        if self.rect.x <= -win_width:
            self.kill()


def distance(pos_a, pos_b):
    dx = pos_a[0]-pos_b[0]
    dy = pos_a[1]-pos_b[1]
    return math.sqrt(dx**2+dy**2)

def remove(index):
    Birdes.pop(index)
    ge.pop(index)
    nets.pop(index)


def quit_game():
    # Exit Game
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

def scores(p):
    global score
    for pp in  p:
        if pp.pipe_type == 'bottom':
            if bird_start_position[0] > pp.rect.topleft[0] and not pp.passed:
                pp.enter = True
            if bird_start_position[0] > pp.rect.topright[0] and not pp.passed:
                pp.exit = True
            if pp.enter and pp.exit and not pp.passed:
                pp.passed = True
                score += 1
                
genNo = 0
# Game Main Method
def eval_genomes(genomes, config):
    global score, game_stopped, Birdes, ge, nets
    scor = 0
    # Instantiate Bird
    Birdes = []
    ge =[]
    nets = []
    for genome_id, genome in genomes:
        bird = pygame.sprite.GroupSingle()
        bird.add(Bird())
        Birdes.append(bird)
        genome.fitness = 0  
        ge.append(genome)
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        nets.append(net)
    
    # Setup Pipes
    pipe_timer = 0
    pipes = pygame.sprite.Group()

    # Instantiate Initial Ground
    x_pos_ground, y_pos_ground = 0, 520
    ground = pygame.sprite.Group()
    ground.add(Ground(x_pos_ground, y_pos_ground))
    run = True
    while run and len(Birdes)> 0:
        # Quit
        quit_game()
        # Reset Frame
        window.fill((0, 0, 0))
        # Draw Background
        window.blit(skyline_image, (0, 0))
        # Spawn Ground
        if len(ground) <= 2:
            ground.add(Ground(win_width, y_pos_ground))
        # Draw - Pipes, Ground and Bird
        pipes.draw(window)
        ground.draw(window)
        for bird in Birdes:
            bird.draw(window)

        pipeObj = pipes.sprites()

        for i, bird in enumerate(Birdes):
            ge[i].fitness += 0.01
            for pp in pipeObj:
                if pp.pipe_type == 'bottom':
                    if bird_start_position[0] > pp.rect.topleft[0] and not pp.passed:
                        pp.passed = True
                        bird.sprite.scoring()
                        scor += 1
            if len(pipeObj) > 0:
                pygame.draw.line(window, bird.sprite.color, bird.sprites()[0].rect.center, pipeObj[scor * 2].rect.bottomright, 2)
                pygame.draw.line(window, bird.sprite.color, bird.sprites()[0].rect.center, pipeObj[(scor * 2) + 1].rect.topright, 2)
                if pipeObj[scor * 2].rect.x > bird.sprites()[0].rect.center[0]:
                    a = distance(bird.sprites()[0].rect.center, pipeObj[scor * 2].rect.bottomright)
                    b = distance(bird.sprites()[0].rect.center, pipeObj[(scor * 2) + 1].rect.topright)
                    inp = [bird.sprites()[0].rect.center[1], a, b]
            else:
                inp = [bird.sprites()[0].rect.center[1], distance(bird.sprites()[0].rect.center,[550, 265]), distance(bird.sprites()[0].rect.center,[550,380])]
            output = nets[i].activate(inp)
            if output[0] > 0.5:
                user_input = 1
            else:
                user_input = 0
            bird.update(user_input)
            collision_pipes = pygame.sprite.spritecollide(bird.sprites()[0], pipes, False)
            collision_ground = pygame.sprite.spritecollide(bird.sprites()[0], ground, False)
            if collision_pipes or collision_ground:
                bird.sprite.alive = False
                ge[i].fitness -= 5
                remove(i)

        # Update - Pipes, Ground and Bird
        pipes.update()
        ground.update()
        # Spawn Pipes
        if pipe_timer <= 0 and bird.sprite.alive:
            x_top, x_bottom = 550, 550
            y_top = random.randint(-600, -480)
            y_bottom = y_top + random.randint(80, 150) + bottom_pipe_image.get_height()
            pipes.add(Pipe(x_top, y_top, top_pipe_image, 'top'))
            pipes.add(Pipe(x_bottom, y_bottom, bottom_pipe_image, 'bottom'))
            pipe_timer = random.randint(180, 250)
        pipe_timer -= 1

        # Show Score
        score_text = font.render('Time: ' + str(round(scor)), True, pygame.Color(255, 255, 255))
        alive_text = font.render(f'Birdies Alive:  {str(len(Birdes))}', True, (255, 255, 255))
        genereation_text = font.render(f'Generation:  {pop.generation+1}', True, (255, 255, 255))
        window.blit(score_text, (20, 20))
        window.blit(genereation_text, (20, 35))
        window.blit(alive_text, (20, 50))
        window.blit(score_text, (20, 20))

        clock.tick(90)
        # print(pygame.time.get_ticks()/1000)
        pygame.display.update()


def run(config_path):
    global pop, game_stopped, pipe_timer
    # Draw Menu
    window.fill((0, 0, 0))
    window.blit(skyline_image, (0, 0))
    window.blit(ground_image, Ground(0, 520))
    window.blit(bird_images[0], (100, 250))
    window.blit(start_image, (win_width // 2 - start_image.get_width() // 2,
                                  win_height // 2 - start_image.get_height() // 2))


    pygame.display.update()


    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation, 
        config_path
    )

    pop = neat.Population(config)
    pipe_timer = 0
    winner = pop.run(eval_genomes, 2000)
    return winner


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config1.txt')
    run(config_path)
