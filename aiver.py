import enum
import pygame
import os
import math
import sys
import neat
from sys import exit
import random
import operator
import pickle

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
skyes = pygame.image.load ("assets/skyline.png")
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
        if self.rect.x <= bird_start_position[0] - 200:
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


class SkyLine(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = skyes
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
    x_pos_sky, y_pos_sky = 0, 0
    skies = pygame.sprite.Group()
    skies.add(SkyLine(x_pos_sky, y_pos_sky))
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
        if len(ground) <= 2:
            skies.add(SkyLine(win_width, y_pos_sky))

        # Draw - Pipes, Ground and Bird
        pipes.draw(window)
        ground.draw(window)
        skies.draw(window)
        for bird in Birdes:
            bird.draw(window)

        pipeObj = pipes.sprites()
        for i, bird in enumerate(Birdes):
            ge[i].fitness += 0.5
            pipe_index = 0
            if len(pipeObj) > 4:
                if bird_start_position[0] > operator.itemgetter(0)(pipeObj[0].rect.bottomright):
                    pipe_index = 2
                if bird_start_position[0] > operator.itemgetter(0)(pipeObj[2].rect.bottomright):
                    pipe_index = 4
                if bird_start_position[0] > operator.itemgetter(0)(pipeObj[4].rect.bottomright):
                    pipe_index = 6 
            for pp in pipeObj:
                if pp.pipe_type == 'bottom':
                    if bird_start_position[0] > pp.rect.midbottom[0] and not pp.passed:
                        pp.passed = True
                        bird.sprite.scoring()
                        scor += 1
                        ge[i].fitness += 20 * scor
            if len(pipeObj) > 0:
                pygame.draw.line(window, bird.sprite.color, bird.sprites()[0].rect.center, pipeObj[pipe_index].rect.bottomright, 2)
                pygame.draw.line(window, bird.sprite.color, bird.sprites()[0].rect.center, pipeObj[pipe_index + 1].rect.topright, 2)
                if pipeObj[pipe_index].rect.bottomright[0] > bird.sprites()[0].rect.center[0]:
                    a = distance(bird.sprites()[0].rect.center, pipeObj[pipe_index].rect.bottomright)
                    b = distance(bird.sprites()[0].rect.center, pipeObj[pipe_index + 1].rect.topright)
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
            collision_sky = pygame.sprite.spritecollide(bird.sprites()[0], skies, False)
            if collision_pipes or collision_ground or collision_sky:
                bird.sprite.alive = False
                ge[i].fitness -= 25
                remove(i)

        # Update - Pipes, Ground and Bird
        pipes.update()
        ground.update()
        skies.update()
        # Spawn Pipes
        if pipe_timer <= 0 and bird.sprite.alive:
            x_top, x_bottom = 550, 550
            y_top = random.randint(-600, -480)
            y_bottom = y_top + random.randint(110, 150) + bottom_pipe_image.get_height()
            pipes.add(Pipe(x_top, y_top, top_pipe_image, 'top'))
            pipes.add(Pipe(x_bottom, y_bottom, bottom_pipe_image, 'bottom'))
            pipe_timer = random.randint(180, 250)
        pipe_timer -= 1

        # Show Score
        score_text = font.render('Score: ' + str(round(scor)), True, pygame.Color(0, 0, 255))
        alive_text = font.render(f'Birdies Alive:  {str(len(Birdes))}', True, (255, 255, 255))
        genereation_text = font.render(f'Generation:  {pop.generation+1}', True, (0, 0, 0))
        window.blit(score_text, (20, 20))
        window.blit(genereation_text, (20, 35))
        window.blit(alive_text, (20, 50))
        window.blit(score_text, (20, 20))

        clock.tick(90)
        # print(pygame.time.get_ticks()/1000)
        pygame.display.update()

def loadingGame():
    global pop, game_stopped, pipe_timer
    # Draw Menu
    loadingGame()
    window.fill((0, 0, 0))
    window.blit(skyline_image, (0, 0))
    window.blit(ground_image, Ground(0, 520))
    window.blit(bird_images[0], (100, 250))
    window.blit(start_image, (win_width // 2 - start_image.get_width() // 2,
                              win_height // 2 - start_image.get_height() // 2))
    pygame.display.update()


def playNet(winner_net):
    global score, game_stopped, Birdes, ge, nets
    scor = 0
    # Instantiate Bird
    bird = pygame.sprite.GroupSingle()
    bird.add(Bird())
        
    # Setup Pipes
    pipe_timer = 0
    pipes = pygame.sprite.Group()

    # Instantiate Initial Ground
    x_pos_ground, y_pos_ground = 0, 520
    ground = pygame.sprite.Group()
    ground.add(Ground(x_pos_ground, y_pos_ground))
    x_pos_sky, y_pos_sky = 0, 0
    skies = pygame.sprite.Group()
    skies.add(SkyLine(x_pos_sky, y_pos_sky))
    run = True
    while run:
        # Quit
        quit_game()
        # Reset Frame
        window.fill((0, 0, 0))
        # Draw Background
        window.blit(skyline_image, (0, 0))
        # Spawn Ground
        if len(ground) <= 2:
            ground.add(Ground(win_width, y_pos_ground))
        if len(ground) <= 2:
            skies.add(SkyLine(win_width, y_pos_sky))

        # Draw - Pipes, Ground and Bird
        pipes.draw(window)
        ground.draw(window)
        skies.draw(window)
        bird.draw(window)

        pipeObj = pipes.sprites()
        pipe_index = 0
        if len(pipeObj) > 4:
            if bird_start_position[0] > operator.itemgetter(0)(pipeObj[0].rect.bottomright):
                pipe_index = 2
            if bird_start_position[0] > operator.itemgetter(0)(pipeObj[2].rect.bottomright):
                pipe_index = 4
            if bird_start_position[0] > operator.itemgetter(0)(pipeObj[4].rect.bottomright):
                pipe_index = 6 
        for pp in pipeObj:
            if pp.pipe_type == 'bottom':
                if bird_start_position[0] > pp.rect.midbottom[0] and not pp.passed:
                    pp.passed = True
                    bird.sprite.scoring()
                    scor += 1
        if len(pipeObj) > 0:
            pygame.draw.line(window, bird.sprite.color, bird.sprites()[0].rect.center, pipeObj[pipe_index].rect.bottomright, 2)
            pygame.draw.line(window, bird.sprite.color, bird.sprites()[0].rect.center, pipeObj[pipe_index + 1].rect.topright, 2)
            if pipeObj[pipe_index].rect.bottomright[0] > bird.sprites()[0].rect.center[0]:
                a = distance(bird.sprites()[0].rect.center, pipeObj[pipe_index].rect.bottomright)
                b = distance(bird.sprites()[0].rect.center, pipeObj[pipe_index + 1].rect.topright)
                inp = [bird.sprites()[0].rect.center[1], a, b]
        else:
            inp = [bird.sprites()[0].rect.center[1], distance(bird.sprites()[0].rect.center,[550, 265]), distance(bird.sprites()[0].rect.center,[550,380])]
        output = winner_net.activate(inp)
        if output[0] > 0.5:
            user_input = 1
        else:
            user_input = 0
        bird.update(user_input)
        collision_pipes = pygame.sprite.spritecollide(bird.sprites()[0], pipes, False)
        collision_ground = pygame.sprite.spritecollide(bird.sprites()[0], ground, False)
        collision_sky = pygame.sprite.spritecollide(bird.sprites()[0], skies, False)
        if collision_pipes or collision_ground or collision_sky:
            bird.sprite.alive = False
            break

        # Update - Pipes, Ground and Bird
        pipes.update()
        ground.update()
        skies.update()
        # Spawn Pipes
        if pipe_timer <= 0 and bird.sprite.alive:
            x_top, x_bottom = 550, 550
            y_top = random.randint(-600, -480)
            y_bottom = y_top + random.randint(110, 150) + bottom_pipe_image.get_height()
            pipes.add(Pipe(x_top, y_top, top_pipe_image, 'top'))
            pipes.add(Pipe(x_bottom, y_bottom, bottom_pipe_image, 'bottom'))
            pipe_timer = random.randint(180, 250)
        pipe_timer -= 1

        # Show Score
        score_text = font.render('Score: ' + str(round(scor)), True, pygame.Color(0, 0, 255))
        # alive_text = font.render(f'Birdies Alive:  {str(len(Birdes))}', True, (255, 255, 255))
        # genereation_text = font.render(f'Generation:  {pop.generation+1}', True, (0, 0, 0))
        window.blit(score_text, (20, 20))
        # window.blit(genereation_text, (20, 35))
        # window.blit(alive_text, (20, 50))
        clock.tick(60)
        # print(pygame.time.get_ticks()/1000)
        pygame.display.update()



def run(config_path):
    global pop, game_stopped, pipe_timer
    loadingGame()
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation, 
        config_path
    )

    pop = neat.Population(config)
    pipe_timer = 0
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    winner = pop.run(eval_genomes, 5)
    file = open('flapper.dat', 'wb')
    pickle.dump(winner, file)
    return winner


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config1.txt')
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation, 
        config_path
    )
    # run(config_path)
    fileo = open('flapper.dat', 'rb')
    winner = pickle.load(fileo)
    fileo.close()
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    playNet(winner_net)


