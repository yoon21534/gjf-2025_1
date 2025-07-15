import pygame
import sys


pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("배경 음악과 효과음")

# 배경 음악
pygame.mixer.music.load("bgm.mp3")
pygame.mixer.music.play(-1)  # 무한 반복

# 효과음
sound = pygame.mixer.Sound("effect.wav")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                sound.play()

    screen.fill((0, 100, 200))
    pygame.display.update()