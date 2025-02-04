import pygame
import random
import time

# Initialize Pygame
pygame.init()

# Screen dimensions
screen_width = 900
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)

# Player attributes
player_width = 50
player_height = 50
player_x = screen_width // 2
player_y = screen_height - player_height - 10
player_speed = 0.5

# Star attributes
star_width = 30
star_height = 30
star_speed = 0.95
star_x = random.randint(0, screen_width - star_width)
star_y = -star_height


# Game variables
score = 0
font = pygame.font.SysFont(None, 55)

# Function to draw the player
def draw_player(x, y):
    pygame.draw.rect(screen, black, [x, y, player_width, player_height])

# Function to draw the star
def draw_star(x, y):
    pygame.draw.rect(screen, red, [x, y, star_width, star_height])

# Function to display the score
def show_score(score):
    text = font.render("Score: " + str(score), True, black)
    screen.blit(text, [0, 0])

# Main game loop
running = True
while running:
    screen.fill(white)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Player movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player_x > 0:
        player_x -= player_speed
    if keys[pygame.K_RIGHT] and player_x < screen_width - player_width:
        player_x += player_speed

    # Move star
    star_y += star_speed
    
    # Check if star is caught by player
    if player_y < star_y + star_height and player_y + player_height > star_y:
        if player_x < star_x + star_width and player_x + player_width > star_x:
            score += 1
            star_x = random.randint(0, screen_width - star_width)
            star_y = -star_height
    
    # Reset star if it goes off the screen
    if star_y > screen_height:
        star_x = random.randint(0, screen_width - star_width)
        star_y = -star_height

    # Draw everything
    draw_player(player_x, player_y)
    draw_star(star_x, star_y)
    show_score(f'{score}')
    
    pygame.display.update()
    if score ==100:
        pygame.display.quit()

# Quit Pygame


pygame.display.quit()
