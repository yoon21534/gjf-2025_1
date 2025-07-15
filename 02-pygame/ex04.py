import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((640, 480))
pygame.display.set_caption("FPS & 충돌 감지")

clock = pygame.time.Clock()

player = pygame.image.load("character.png")
enemy = pygame.image.load("enemy.png")
player = pygame.transform.scale(player, (player.get_width() // 5, player.get_height() // 5))
enemy = pygame.transform.scale(enemy, (enemy.get_width() // 5, enemy.get_height() // 5))

px, py = 100, 100
ex, ey = 300, 200
speed = 5

# 반짝거림 효과 변수
blink_timer = 0
blink_duration = 60  # 1초간 반짝거림 (60프레임)
blink_interval = 5   # 5프레임마다 깜빡임

while True:
    clock.tick(60)  # 초당 60프레임 유지

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        px -= speed
    if keys[pygame.K_RIGHT]:
        px += speed
    if keys[pygame.K_UP]:
        py -= speed
    if keys[pygame.K_DOWN]:
        py += speed

    # 충돌 체크
    player_rect = player.get_rect(topleft=(px, py))
    enemy_rect = enemy.get_rect(topleft=(ex, ey))

    if player_rect.colliderect(enemy_rect):
        if blink_timer == 0:  # 처음 충돌 시에만 타이머 시작
            blink_timer = blink_duration
        print("충돌!")
    
    # 반짝거림 타이머 감소
    if blink_timer > 0:
        blink_timer -= 1

    screen.fill((30, 30, 30))
    
    # 반짝거림 효과: 타이머가 활성화되어 있고 깜빡임 간격에 따라 표시/숨김
    if blink_timer == 0 or (blink_timer // blink_interval) % 2 == 0:
        screen.blit(player, (px, py))
        # 플레이어 테두리선 그리기 (초록색)
        pygame.draw.rect(screen, (0, 255, 0), player_rect, 2)
    
    screen.blit(enemy, (ex, ey))
    # 적 테두리선 그리기 (빨간색)
    pygame.draw.rect(screen, (255, 0, 0), enemy_rect, 2)
    
    pygame.display.update()