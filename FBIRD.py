import pygame
import neat
import time
import os
import random
pygame.font.init()

# Constants named in all capitals
WIN_WIDTH = 500
WIN_HEIGHT = 800

GEN = 0

# Scale size of objects by 2x for better visuals
# Load .png images into variables for future use
BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

# Font of the score
STAT_FONT = pygame.font.SysFont("comicsans", 50)


# Define bird object
class Bird:
    IMGS = BIRD_IMGS
    # in degrees, how much the bird will tilt when jumping
    MAX_ROTATION = 25
    # How fast we will rotate on each frame/movement
    ROT_VEL = 20
    # How long we will show each bird stance, to simulate the "flapping" of the bird
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        # Starting position of the bird
        self.x = x
        self.y = y
        # Initially, bird will start horizontally, so set tilt = 0
        self.tilt = 0
        # Keeps track of how many times move() was called until the bird jumps
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        # For determining if image of the bird should be changed, in the draw() function
        self.img_count = 0
        # The image of the bird being currently displayed
        self.img = self.IMGS[0]

    def jump(self):
        # Since top left corner of the window is defined as (0,0) and bottom right corner as (WIN_WIDTH, WIN_HEIGHT),
        # we must have negative velocity to go upwards
        # (right = positive, left = negative, up = negative, down = positive)
        self.vel = -10.5
        # We set this to 0 when the bird jumps, so variable d in the move function works as intended
        self.tick_count = 0
        # Updates self.height
        # In the function move, self.y is updated by the displacement formula, while self.height remains unchanged.
        # In this respect, we may compare the position of the bird previous to jumping, with its displacing position.
        # This helps us determine the tilt of the bird, depending on its action and movement.
        # Once the bird jumps, self.height is updated
        self.height = self.y

    def move(self):
        # Keeps track of how many "times" we moved since we last jumped
        self.tick_count += 1

        # Define displacement by acceleration formula: (V_i * t) + (1/2a * t^2)
        # When the bird jumps, self.vel = -10.5:
        # When self.tick_count = 1, d = -10.5 + 1.5 = -9, so the displacement of the bird will be 9 pixels upwards
        # When self.tick_count = 2, d = -15
        # When self.tick_count = 3 or self.tick_count = 4, d = -18
        # When self.tick_count >= 5, d = -15 -> -9 -> 0 -> 12 -> 27 (for each increase in
        # self.tick_count >= 5, respectively)
        # This pattern of displacement forms an arc-like shape for our bird's movement, after it has jumped
        d = self.vel*self.tick_count + 1.5*self.tick_count**2

        # Define terminal velocity by limiting displacement values, to cap the rate at which the bird falls
        if d >= 16:
            d = 16
        # For fine tuning the bird's movement when jumping to acquire desirable motion of the bird
        if d < 0:
            d -= 2

        # After calculating, and tuning the displacement, update the y position of the bird
        self.y = self.y + d

        # Define tilt of the bird
        # If bird is moving upwards, or is in the reasonable range of falling after the jump, bird is tilted upwards
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            # Bird will tilt to seem like it is nose-diving towards the ground when falling, as in the actual game
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    # Draws the bird according to its tilt status: Flapping when tilted upwards, Gliding when tilted downwards
    # win = window we are drawing the bird onto
    def draw(self, win):
        # Keeps track of bird visualization with tick-counter
        self.img_count += 1

        # Loop through bird images to simulate flapping of the bird, depending on the tick-counter
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        # If the bird is tilted downwards, it should not be flapping (intuitively)
        if self.tilt <= -80:
            self.img = self.IMGS[1]
            # To ensure self.img starts at self.IMGS[1], instead of skipping a frame and starting at self.IMGS[0]
            self.img_count = self.ANIMATION_TIME*2

        # Found from stackOverflow, rotating an image around its center
        # The function pygame.transform.rotate rotates our image from the top-left corner, so we must correct its
        # positioning so that it is rotated from its center.
        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft = (self.x, self.y)).center)
        # Blit function draws the given image, with its top-left defined on the given (x,y) coordinate parameter.
        win.blit(rotated_image, new_rect.topleft)

    # For pixel-perfect collision.
    # The function utilized below determines the pixel locations of the bird in a 2-D array,
    # and we will use this information for checking collision.
    # This is done so that we can most accurately determine collision boundaries between the game's elements,
    # instead of being satisfied with a rectangular boundary around it.
    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    # Size of gap between the top and bottom pipes
    GAP = 200
    # We are moving the background and its components, such as the pipes
    # towards the bird, to create the illusion of the bird moving.
    # The velocity of the pipe must be identical to the velocity of the base/"ground" for visual coherency
    VEL = 5

    # The y-value of our pipe will be randomized each time, so we only need the x-value of the pipes' starting positions
    def __init__(self, x):
        self.x = x
        self.height = 0

        # The y value of the top pipe's top-left coordinate
        self.top = 0
        # The y value of the bottom pipe's top-left coordinate
        self.bottom = 0
        # Image of the top pipe (bottom pipe flipped horizontally)
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        # Image of the bottom pipe
        self.PIPE_BOTTOM = PIPE_IMG

        # Determines if bird has passed the pipe successfully
        self.passed = False

        self.set_height()

    # Sets the height (just the top-left coordinates) of the top and bottom pipes
    def set_height(self):
        # Randomize the height of the pipe
        self.height = random.randrange(50, 450)
        # For pipes that appear from the top, we set the height at which the pipes' top-left coordinates should begin
        # from, and subtract the height of the pipe's image. In this respect, the pipe will begin from a negative
        # coordinate (off-screen from the top), and end at our target location.
        # ie: self.PIPE_TOP.get_height() = 640. So if self.height = 100, self.top = 100 - 640 = -540.
        #     Therefore, when it is drawn onto the window in function draw(), the pipe will be drawn
        #     off-screen, starting at y = -540, extending onto the screen by 100 pixels as intended.
        #     Note: As y -> -infinity, y moves upwards, as the top left of the window is defined as (0, 0)
        self.top = self.height - self.PIPE_TOP.get_height()
        # For pipes that appear from the bottom, we simply add the height of the pipe to the size of the gap
        # ie: self.height = 100, then self.bottom = 100 + 200 = 300. So the pipe will extend onto the screen by
        #     300 pixels as intended.
        #     Note: adding 200 to 100 will make the top-left coordinate of the bottom pipe be 200 pixels lower
        self.bottom = self.height + self.GAP

    # Moves the pipe towards the bird according to its velocity value
    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # Pipe collision check
    def collide(self, bird):
        # Receive mask object in the form of a 2-D array with exact pixel locations of the bird
        bird_mask = bird.get_mask()
        # Receive mask object in the form of a 2-D array with exact pixel locations of the top pipe and bottom pipe
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # Calculate the offset between the bird and the top pipe. We require this for the overlap() function used later.
        # An offset calculates the distance between one mask's top left corner and the calling mask's top left corner.
        # The calling mask's top left corner is considered to be the origin.
        # We can not have decimal values for the second parameter, so we round the bird.y value
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        # Similar procedure for the bird and the bottom pipe.
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Returns the point of collision(intersection) between the bird and the top/bottom pipe, using the
        # respective offsets calculated above. If there is no collision, it will return None
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        # If t_point or b_point is non-empty, we return True for collision. Otherwise, return False for avoidance
        if t_point or b_point:
            return True

        return False


class Base:
    # The velocity of the base/"ground" must be identical to the velocity of the pipe for visual coherency
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    # We know where the x-value of the base/ground should start at, so we only need the height of the base
    def __init__(self, y):
        self.y = y
        # Our image of the base is not very long, so we will circulate a second copy image that follows the first.
        # As soon as the first base moves fully off-screen, it will circulate to the second base's initial position,
        # forming a loop of 2 base images continuously.
        # In this respect, the first base begins at x = 0, while the second follows at x = width of base img
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        # When the first base's end has reached the edge of the window, its self.x1 should be -self.WIDTH.
        # Hence, when the binary operation results in a negative value, we know that the base is off-screen, and it
        # may be circulated to the back of the queue.
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH
        # Similar principle for second base
        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


# "Draw" the background image, then draw the pipes, score, and bird on top of it
def draw_window(win, birds, pipes, base, score, gen):
    # Draw the background
    win.blit(BG_IMG, (0, 0))

    # Draw the pipe
    for pipe in pipes:
        pipe.draw(win)

    # Draw the score
    # Note: render(text, antialias, color, background=None)
    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    # Use text.get_width() so the score always stays on the screen/window, regardless of its "length"
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
    win.blit(text, (10, 10))

    # Draw the base, bird, and update the display
    base.draw(win)
    for bird in birds:
        bird.draw(win)
    pygame.display.update()


def main(genomes, config):
    global GEN
    GEN += 1
    # i'th index data of all three lists corresponds to the same i'th bird
    # ie: nets[0], ge[0], birds[0] -> same bird information
    nets = []
    ge = []
    birds = []

    # Initialize neural networks, birds, and its information
    # We need _, g in the for loop statement since genomes are a tuple of (int: genome_id, obj: genome)
    # We are only worried about the genome object itself in manipulation
    for _, g in genomes:
        # Create neural network according to NEAT and the config information for each genome(bird)
        net = neat.nn.FeedForwardNetwork.create(g, config)
        # Append created network to list of networks
        nets.append(net)
        # Create and append bird object
        birds.append(Bird(230, 350))
        # Set initial fitness to 0
        g.fitness = 0
        # Append actual genome to list of genomes
        ge.append(g)

    '''
    # Create the bird, with its starting position at (230, 350)
    bird = Bird(230, 350)
    '''
    # Create base, with its y coordinate at 730. Note: (the bottom of the window is 800)
    base = Base(730)
    # Create pipe, with its x coordinate at 600. Since the right end of the window is 500, pipes will start off-screen
    # in the respective direction, to be moving towards the left. If we want the pipes to be generated closer together,
    # we simply change the Pipe parameter to be of lesser value (Also on line 331).
    pipes = [Pipe(600)]

    # Display empty window
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

    # Define clock
    clock = pygame.time.Clock()
    # Define score
    score = 0

    run = True
    while run:
        # Set tick at most 30 every second to keep consistent rate at which the loop progresses.
        # This is done to regularize the speed of the game and visualization.
        # If we wanted to train the model at a faster speed, we would set a higher tick rate.
        clock.tick(30)

        # Check if game should quit
        for event in pygame.event.get():
            # If red x on the top right of our window is pressed, the game will quit
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            # All birds have same x position
            # If bird has passed a pipe, we change the observing obstacle to be the next upcoming pipe
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        # If there are no birds left, we terminate the generation
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            # Add a bit of fitness score to encourage moving forward
            ge[x].fitness += 0.1

            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height),
                                       abs(bird.y - pipes[pipe_ind].bottom)))

            # Output neurons are in the form of a list. We only have one output neuron, so we may use output[0]
            if output[0] > 0.5:
                bird.jump()

        # For checking if a pipe should be added to be circulated onto the screen/window
        add_pipe = False
        # For storing list of pipes to be removed
        rem = []

        # Manage pipes
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    # If bird collides with pipe, lower its fitness score
                    ge[x].fitness -= 1
                    # Remove bird object and the correspondent information/network
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                # Check if pipe has passed the bird. If so, we need to generate another pipe
                # to be circulated onto the window
                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            # If the pipe is off the screen, store pipe in list rem to be removed
            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        # Add pipe if necessary
        if add_pipe:
            score += 1
            for g in ge:
                # Encourage genomes(birds) that pass through pipes, rather than getting far into the level randomly
                # Since we remove any genomes and its information/network when it hits a pipe, we assume any genome
                # being manipulated at this stage has not hit a pipe.
                g.fitness += 5
            pipes.append(Pipe(600))

        # Remove necessary pipes
        for r in rem:
            pipes.remove(r)

        for x, bird in enumerate(birds):
            # Check if bird has hit the ground (Height of the "base" is set at 730)
            # Check if bird simply jumps off the screen and penalize
            if bird.y + bird.img.get_height() > 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN)


# NEAT (NeuroEvolution of Augmenting Topologies)

def run(config_path):
    # Config parameters consist of [] headers in config-feedforward.txt file, and the path
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)
    # Population
    p = neat.Population(config)

    # Output for assessment
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    # Calls the main function 50 times. We use the main function to determine fitness
    winner = p.run(main,50)

if __name__ == "__main__":
    # Stores current directory
    local_dir = os.path.dirname(__file__)
    # Retrieve exact path of config file
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)