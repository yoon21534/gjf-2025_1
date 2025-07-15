import pygame
import sys

# 초기화
pygame.init()

# 화면 크기 설정
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("기본 창 띄우기")

# 메인 루프
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    screen.fill((255, 255, 255))  # 흰색 배경
    pygame.display.update()