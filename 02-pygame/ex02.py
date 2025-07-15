import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("이미지 표시하기")

# 이미지 로드 (같은 폴더에 'character.png'가 있어야 함)
character = pygame.image.load("./02-pygame/character.png")
# 캐릭터 사이즈를 작게 조절 (원본의 1/5 크기로)
character = pygame.transform.scale(character, (character.get_width() // 5, character.get_height() // 5))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    screen.fill((0, 0, 0))  # 검은 배경
    screen.blit(character, (0, 0))  # 이미지 위치
    pygame.display.update()