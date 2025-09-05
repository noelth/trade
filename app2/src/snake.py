import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Screen Dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)

# Game Settings
SPEED = 10

class Snake:
    def __init__(self):
        self.length = 1
        self.positions = [((SCREEN_WIDTH // 2), (SCREEN_HEIGHT // 2))]
        self.direction = random.choice([pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT])
        self.color = GREEN
        self.score = 0

    def get_head_position(self):
        return self.positions[0]

    def update(self):
        cur = self.get_head_position()
        x, y = cur

        if self.direction == pygame.K_UP:
            new_head = (x, y - GRID_SIZE)
        elif self.direction == pygame.K_DOWN:
            new_head = (x, y + GRID_SIZE)
        elif self.direction == pygame.K_LEFT:
            new_head = (x - GRID_SIZE, y)
        elif self.direction == pygame.K_RIGHT:
            new_head = (x + GRID_SIZE, y)

        if (new_head in self.positions[2:] or
            new_head[0] < 0 or new_head[0] >= SCREEN_WIDTH or
            new_head[1] < 0 or new_head[1] >= SCREEN_HEIGHT):
            return False

        self.positions.insert(0, new_head)
        
        if len(self.positions) > self.length:
            self.positions.pop()
        
        return True

    def render(self, surface):
        for p in self.positions:
            pygame.draw.rect(surface, self.color, (p[0], p[1], GRID_SIZE, GRID_SIZE))

    def handle_keys(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and self.direction != pygame.K_DOWN:
                    self.direction = pygame.K_UP
                elif event.key == pygame.K_DOWN and self.direction != pygame.K_UP:
                    self.direction = pygame.K_DOWN
                elif event.key == pygame.K_LEFT and self.direction != pygame.K_RIGHT:
                    self.direction = pygame.K_LEFT
                elif event.key == pygame.K_RIGHT and self.direction != pygame.K_LEFT:
                    self.direction = pygame.K_RIGHT

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.color = RED
        self.randomize_position()

    def randomize_position(self):
        self.position = (
            random.randint(0, GRID_WIDTH - 1) * GRID_SIZE,
            random.randint(0, GRID_HEIGHT - 1) * GRID_SIZE
        )

    def render(self, surface):
        pygame.draw.rect(surface, self.color, 
                         (self.position[0], self.position[1], GRID_SIZE, GRID_SIZE))

def draw_grid(surface):
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        for x in range(0, SCREEN_WIDTH, GRID_SIZE):
            pygame.draw.rect(surface, WHITE, (x, y, GRID_SIZE, GRID_SIZE), 1)

def main():
    # Initialize screen
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('Snake Game')
    
    # Initialize clock
    clock = pygame.time.Clock()
    
    # Create game objects
    snake = Snake()
    food = Food()
    
    # Font for score
    font = pygame.font.Font(None, 36)
    
    # Game loop
    game_over = False
    while not game_over:
        # Handle events
        snake.handle_keys()
        
        # Update game state
        if not snake.update():
            game_over = True
        
        # Check for food collision
        if snake.get_head_position() == food.position:
            snake.length += 1
            snake.score += 1
            food.randomize_position()
        
        # Drawing
        screen.fill(BLACK)
        draw_grid(screen)
        snake.render(screen)
        food.render(screen)
        
        # Render score
        score_text = font.render(f'Score: {snake.score}', True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # Update display
        pygame.display.update()
        
        # Control game speed
        clock.tick(SPEED)
    
    # Game over screen
    screen.fill(BLACK)
    game_over_text = font.render(f'Game Over! Score: {snake.score}', True, WHITE)
    text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    screen.blit(game_over_text, text_rect)
    pygame.display.update()
    
    # Wait before closing
    pygame.time.wait(2000)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
    