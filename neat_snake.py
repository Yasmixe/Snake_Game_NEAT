import pygame
import sys
import random
import neat
import os

pygame.init()

sw, sh = 800, 800
block_size = 50
screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Snake with AI")
clock = pygame.time.Clock()

# Font initialization
font = pygame.font.Font(None, 36)


class Snake:
    def __init__(self):
        self.x, self.y = block_size, block_size
        self.xdir = 1
        self.ydir = 0
        self.head = pygame.Rect(self.x, self.y, block_size, block_size)
        self.body = [pygame.Rect(self.x - block_size, self.y, block_size, block_size)]
        self.dead = False
        self.score = 0  # Initialize score

    def update(self):
        global apple
        for square in self.body:
            if self.head.x == square.x and self.head.y == square.y:
                self.dead = True
            if self.head.x not in range(0, sw) or self.head.y not in range(0, sh):
                self.dead = True

        if self.dead:
            self.score -= 1  # Decrease score when dead
            if self.score < -10:  # Limit score to -10 (or any other limit you want)
                self.score = -10
            self.x, self.y = block_size, block_size
            self.head = pygame.Rect(self.x, self.y, block_size, block_size)
            self.body = [
                pygame.Rect(self.x - block_size, self.y, block_size, block_size)
            ]
            self.xdir = 1
            self.ydir = 0
            self.dead = False
            apple = Apple()

        self.body.append(self.head)
        for i in range(len(self.body) - 1):
            self.body[i].x, self.body[i].y = self.body[i + 1].x, self.body[i + 1].y
        self.head.x += self.xdir * block_size
        self.head.y += self.ydir * block_size
        self.body.remove(self.head)


class Apple:
    def __init__(self):
        self.x = int(random.randint(0, sw) / block_size) * block_size
        self.y = int(random.randint(0, sh) / block_size) * block_size
        self.rect = pygame.Rect(self.x, self.y, block_size, block_size)

    def update(self):
        pygame.draw.rect(screen, "red", self.rect)


def drawGrid():
    for x in range(0, sw, block_size):
        for y in range(0, sh, block_size):
            rect = pygame.Rect(x, y, block_size, block_size)
            pygame.draw.rect(screen, "#3c3c3b", rect, 1)


def get_matrix_16x16(snake, apple):
    matrix = [[0] * 16 for _ in range(16)]  # Initialize a 16x16 matrix with zeros

    # Calculate indices relative to the snake's head
    head_x_index = snake.head.x // block_size
    head_y_index = snake.head.y // block_size

    # Fill the matrix with information about snake body and apple
    for i in range(-8, 8):
        for j in range(-8, 8):
            x = head_x_index + i
            y = head_y_index + j

            if 0 <= x < 16 and 0 <= y < 16:
                if x == apple.x // block_size and y == apple.y // block_size:
                    matrix[i + 8][j + 8] = 2  # Mark the cell containing the apple
                elif any(
                    x == b.x // block_size and y == b.y // block_size
                    for b in snake.body
                ):
                    matrix[i + 8][j + 8] = 1  # Mark the cell containing snake body
                else:
                    matrix[i + 8][j + 8] = 0  # Mark an empty cell

    return matrix


def eval_genomes(genomes, config):
    for genome_id, genome in genomes:
        net = neat.nn.FeedForwardNetwork.create(genome, config)
        score = run_game(genome, net)
        genome.fitness = score  # Assign the score obtained by the snake


def run_game(genome, net):
    global snake, apple
    score = 0  # Initialize score
    snake = Snake()
    apple = Apple()
    while not snake.dead:
        # Get 16x16 matrix around the snake's head
        matrix = get_matrix_16x16(snake, apple)

        # Flatten matrix for input
        input_data = [item for sublist in matrix for item in sublist]
        input_data.extend(
            [snake.xdir, snake.ydir, snake.score]
        )  # Include direction and score as input

        # Ensure input matches the expected number of inputs in the NEAT configuration
        if len(input_data) != 256 + 3:
            raise ValueError(f"Expected 259 inputs, got {len(input_data)}")

        output = net.activate(input_data)

        direction = output.index(max(output))

        if direction == 0:
            snake.ydir = 1
            snake.xdir = 0
        elif direction == 1:
            snake.ydir = -1
            snake.xdir = 0
        elif direction == 2:
            snake.ydir = 0
            snake.xdir = 1
        elif direction == 3:
            snake.ydir = 0
            snake.xdir = -1

        snake.update()
        screen.fill("black")
        drawGrid()
        apple.update()
        pygame.draw.rect(screen, "green", snake.head)
        for square in snake.body:
            pygame.draw.rect(screen, "green", square)
        if snake.head.x == apple.x and snake.head.y == apple.y:
            snake.body.append(pygame.Rect(square.x, square.y, block_size, block_size))
            apple = Apple()
            score += 1  # Increase score when eating apple

        # Draw score on the screen
        score_text = font.render(f"Score: {snake.score}", True, pygame.Color("white"))
        screen.blit(score_text, (10, 10))

        pygame.display.update()
        clock.tick(10)

    return score


def run(config_file):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_file,
    )
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    p.run(eval_genomes, 10)


if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
