import pygame
import random
import sys
import time

# Function to display the initial input screen
def display_initial_input_screen(screen, font):
    input_box = pygame.Rect(screen_width // 2 - 100, screen_height // 2 - 20, 200, 40)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = False
    text = ''
    done = False

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode

        screen.fill((30, 30, 30))
        txt_surface = font.render(text, True, color)
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(screen, color, input_box, 2)
        pygame.display.flip()

    return text

# Function to get player image based on evolution stage and key pressed
def get_player_image(evolution_stage, key):
    if key == 'q':
        return neuron_q_image if evolution_stage == 0 else neuronpop_q_image if evolution_stage == 1 else mouse_q_image
    elif key == 'w':
        return neuron_w_image if evolution_stage == 0 else neuronpop_w_image if evolution_stage == 1 else mouse_w_image

# Function to update player rank file
def update_rank_file(player_name, score):
    with open("player_ranks.txt", "a") as file:
        file.write(f"{player_name}: {score}\n")

# Function to run the game
def run_game(player_name):
    player_speed = 12.5
    player_pos = [screen_width // 2, screen_height - 200]
    last_player_image = neuron_q_image
    neurons = []
    neuron_fall_speed = 5
    collected_neurons = 0
    evolution_stage = 0
    moving_left = False
    moving_right = False

    running = True
    start_time = time.time()
    game_duration = 120  # Duration in seconds

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    moving_left = True
                    last_player_image = get_player_image(evolution_stage, 'q')
                elif event.key == pygame.K_w:
                    moving_right = True
                    last_player_image = get_player_image(evolution_stage, 'w')
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_q:
                    moving_left = False
                elif event.key == pygame.K_w:
                    moving_right = False

        if moving_left and player_pos[0] > 0:
            player_pos[0] -= player_speed
        if moving_right and player_pos[0] < screen_width - 200:
            player_pos[0] += player_speed

        if random.randint(1, 20) == 1:
            neurons.append([random.randint(0, screen_width - 50), 0])

        for neuron in neurons:
            neuron[1] += neuron_fall_speed
            if neuron[1] >= screen_height:
                neurons.remove(neuron)

        for neuron in neurons:
            if neuron[1] >= player_pos[1] and player_pos[0] < neuron[0] < player_pos[0] + 200:
                neurons.remove(neuron)
                collected_neurons += 1
                if collected_neurons >= 20 and evolution_stage == 0:
                    evolution_stage = 1
                elif collected_neurons >= 40 and evolution_stage == 1:
                    evolution_stage = 2

        screen.blit(background_image, (0, 0))
        if last_player_image:
            screen.blit(last_player_image, (player_pos[0], player_pos[1]))
        for neuron in neurons:
            screen.blit(neuron_falling_image, (neuron[0], neuron[1]))

        remaining_time = max(0, game_duration - int(time.time() - start_time))
        if remaining_time == 0:
            running = False
            print(f"Player {player_name} collected {collected_neurons} neurons.")
            update_rank_file(player_name, collected_neurons)
        else:
            timer_surface = font.render(f'Time Left: {remaining_time}', True, (255, 255, 255))
            screen.blit(timer_surface, (10, 10))

        points_surface = font.render(f'Points: {collected_neurons}', True, (255, 255, 255))
        points_rect = points_surface.get_rect(topright=(screen_width - 10, 10))
        screen.blit(points_surface, points_rect)

        pygame.display.flip()
        clock.tick(30)

# Initialize Pygame and create window
pygame.init()
screen_width = 1500
screen_height = 1000
screen = pygame.display.set_mode((screen_width, screen_height))
font = pygame.font.Font(None, 32)
pygame.display.set_caption("Neuron Catcher")

# Load and scale images
background_image = pygame.image.load('images/happylab2.jpg')
background_image = pygame.transform.scale(background_image, (screen_width, screen_height))
neuron_q_image = pygame.image.load('images/neuronhappy_q.png')
neuron_q_image = pygame.transform.scale(neuron_q_image, (200, 200))
neuron_w_image = pygame.image.load('images/neuronhappy_w.png')
neuron_w_image = pygame.transform.scale(neuron_w_image, (200, 200))
neuronpop_q_image = pygame.image.load('images/brain_q.png')
neuronpop_q_image = pygame.transform.scale(neuronpop_q_image, (200, 200))
neuronpop_w_image = pygame.image.load('images/brain_w.png')
neuronpop_w_image = pygame.transform.scale(neuronpop_w_image, (200, 200))
mouse_q_image = pygame.image.load('images/mouse_walking_q.png')
mouse_q_image = pygame.transform.scale(mouse_q_image, (200, 200))
mouse_w_image = pygame.image.load('images/mouse_walking_w.png')
mouse_w_image = pygame.transform.scale(mouse_w_image, (200, 200))
neuron_falling_image = pygame.image.load('images/babyneuron.png')
neuron_falling_image = pygame.transform.scale(neuron_falling_image, (50, 50))

clock = pygame.time.Clock()

# Main loop for the entire program
try:
    while True:
        player_name = display_initial_input_screen(screen, font)
        run_game(player_name)
finally:
    pygame.quit()
