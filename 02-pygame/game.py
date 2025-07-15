import pygame
import random
import math
import sys

# 초기화
pygame.init()

# 화면 설정
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("탄막 슈팅 게임")

# 색상 정의
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
PINK = (255, 192, 203)

# 게임 설정
FPS = 60
clock = pygame.time.Clock()

class Item:
    def __init__(self, x, y, item_type):
        self.x = x
        self.y = y
        self.item_type = item_type  # 0: 크기 증가, 1: 속도 증가, 2: 발사 속도 증가, 3: 삼중 발사
        self.size = 15
        self.speed = 2
        self.collected = False
        
    def update(self):
        self.y += self.speed
        if self.y > SCREEN_HEIGHT + 20:
            self.collected = True
    
    def draw(self, screen):
        if not self.collected:
            colors = [GREEN, ORANGE, PINK, CYAN]
            pygame.draw.circle(screen, colors[self.item_type], (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size - 3)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 20
        self.speed = 5
        self.bullets = []
        self.shoot_delay = 0
        self.health = 3
        self.invulnerable = 0
        
        # 무기 강화 상태
        self.bullet_size = 3
        self.bullet_speed = 10
        self.shoot_speed = 5  # 낮을수록 빠른 발사
        self.triple_shot = False
        self.triple_shot_timer = 0
        
    def update(self):
        # 키 입력 처리
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.x > self.size:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < SCREEN_WIDTH - self.size:
            self.x += self.speed
        if keys[pygame.K_UP] and self.y > self.size:
            self.y -= self.speed
        if keys[pygame.K_DOWN] and self.y < SCREEN_HEIGHT - self.size:
            self.y += self.speed
            
        # 발사
        if keys[pygame.K_SPACE] and self.shoot_delay <= 0:
            if self.triple_shot:
                # 삼중 발사
                self.bullets.append(Bullet(self.x - 10, self.y - self.size, 0, -self.bullet_speed, YELLOW, self.bullet_size))
                self.bullets.append(Bullet(self.x, self.y - self.size, 0, -self.bullet_speed, YELLOW, self.bullet_size))
                self.bullets.append(Bullet(self.x + 10, self.y - self.size, 0, -self.bullet_speed, YELLOW, self.bullet_size))
            else:
                # 일반 발사
                self.bullets.append(Bullet(self.x, self.y - self.size, 0, -self.bullet_speed, YELLOW, self.bullet_size))
            self.shoot_delay = self.shoot_speed
            
        if self.shoot_delay > 0:
            self.shoot_delay -= 1
            
        if self.invulnerable > 0:
            self.invulnerable -= 1
            
        # 삼중 발사 타이머
        if self.triple_shot_timer > 0:
            self.triple_shot_timer -= 1
            if self.triple_shot_timer <= 0:
                self.triple_shot = False
            
        # 총알 업데이트
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.y < 0:
                self.bullets.remove(bullet)
    
    def upgrade_weapon(self, item_type):
        if item_type == 0:  # 크기 증가
            self.bullet_size = min(self.bullet_size + 1, 8)
        elif item_type == 1:  # 속도 증가
            self.bullet_speed = min(self.bullet_speed + 2, 20)
        elif item_type == 2:  # 발사 속도 증가
            self.shoot_speed = max(self.shoot_speed - 1, 2)
        elif item_type == 3:  # 삼중 발사
            self.triple_shot = True
            self.triple_shot_timer = 600  # 10초간 지속
    
    def draw(self, screen):
        # 무적 상태일 때 깜빡임 효과
        if self.invulnerable == 0 or self.invulnerable % 10 < 5:
            pygame.draw.circle(screen, BLUE, (int(self.x), int(self.y)), self.size)
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size - 3)
        
        # 총알 그리기
        for bullet in self.bullets:
            bullet.draw(screen)

class Enemy:
    def __init__(self, x, y, pattern_type=0):
        self.x = x
        self.y = y
        self.size = 15
        self.health = 3
        self.bullets = []
        self.shoot_timer = 0
        self.pattern_type = pattern_type
        self.angle = 0
        self.move_timer = 0
        
    def update(self):
        # 이동 패턴
        self.move_timer += 1
        if self.pattern_type == 0:  # 좌우 이동
            self.x += math.sin(self.move_timer * 0.05) * 2
        elif self.pattern_type == 1:  # 원형 이동
            self.x += math.cos(self.move_timer * 0.03) * 1.5
            self.y += math.sin(self.move_timer * 0.03) * 0.5
        
        # 화면 경계 처리
        if self.x < 0 or self.x > SCREEN_WIDTH:
            self.x = max(0, min(SCREEN_WIDTH, self.x))
            
        self.shoot_timer += 1
        
        # 탄막 패턴
        if self.shoot_timer % 30 == 0:  # 0.5초마다 발사
            if self.pattern_type == 0:
                self.circular_shot()
            elif self.pattern_type == 1:
                self.spread_shot()
            elif self.pattern_type == 2:
                self.spiral_shot()
                
        # 총알 업데이트
        for bullet in self.bullets[:]:
            bullet.update()
            if (bullet.x < -20 or bullet.x > SCREEN_WIDTH + 20 or 
                bullet.y < -20 or bullet.y > SCREEN_HEIGHT + 20):
                self.bullets.remove(bullet)
    
    def circular_shot(self):
        # 원형 탄막
        for i in range(8):
            angle = (i * 45 + self.angle) * math.pi / 180
            dx = math.cos(angle) * 3
            dy = math.sin(angle) * 3
            self.bullets.append(Bullet(self.x, self.y, dx, dy, RED, 4))
        self.angle += 22.5
    
    def spread_shot(self):
        # 플레이어 방향으로 확산 탄막
        for i in range(5):
            angle = (i - 2) * 15 * math.pi / 180
            dx = math.sin(angle) * 2
            dy = math.cos(angle) * 4
            self.bullets.append(Bullet(self.x, self.y, dx, dy, PURPLE, 5))
    
    def spiral_shot(self):
        # 나선형 탄막
        for i in range(3):
            angle = (self.angle + i * 120) * math.pi / 180
            dx = math.cos(angle) * 2
            dy = math.sin(angle) * 2
            self.bullets.append(Bullet(self.x, self.y, dx, dy, CYAN, 3))
        self.angle += 5
    
    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.size)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size - 3)
        
        # 총알 그리기
        for bullet in self.bullets:
            bullet.draw(screen)

class Bullet:
    def __init__(self, x, y, dx, dy, color, size):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.size = size
        
    def update(self):
        self.x += self.dx
        self.y += self.dy
        
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

class Game:
    def __init__(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)
        self.enemies = []
        self.items = []
        self.score = 0
        self.level = 1
        self.enemy_spawn_timer = 0
        self.item_spawn_timer = 0
        self.game_over = False
        self.font = pygame.font.Font(None, 36)
        
    def spawn_enemy(self):
        if len(self.enemies) < 3:
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = random.randint(50, 150)
            pattern = random.randint(0, 2)
            self.enemies.append(Enemy(x, y, pattern))
    
    def spawn_item(self):
        if len(self.items) < 2 and random.random() < 0.3:  # 30% 확률로 아이템 생성
            x = random.randint(50, SCREEN_WIDTH - 50)
            y = -20
            item_type = random.randint(0, 3)
            self.items.append(Item(x, y, item_type))
    
    def check_collisions(self):
        # 플레이어 총알과 적 충돌
        for bullet in self.player.bullets[:]:
            for enemy in self.enemies[:]:
                if (abs(bullet.x - enemy.x) < enemy.size + bullet.size and
                    abs(bullet.y - enemy.y) < enemy.size + bullet.size):
                    self.player.bullets.remove(bullet)
                    enemy.health -= 1
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        self.score += 100
                        # 적 처치 시 아이템 드롭 확률
                        if random.random() < 0.2:  # 20% 확률
                            item_type = random.randint(0, 3)
                            self.items.append(Item(enemy.x, enemy.y, item_type))
                    break
        
        # 적 총알과 플레이어 충돌
        if self.player.invulnerable == 0:
            for enemy in self.enemies:
                for bullet in enemy.bullets[:]:
                    if (abs(bullet.x - self.player.x) < self.player.size + bullet.size and
                        abs(bullet.y - self.player.y) < self.player.size + bullet.size):
                        enemy.bullets.remove(bullet)
                        self.player.health -= 1
                        self.player.invulnerable = 120  # 2초 무적
                        if self.player.health <= 0:
                            self.game_over = True
                        break
        
        # 아이템과 플레이어 충돌
        for item in self.items[:]:
            if (abs(item.x - self.player.x) < self.player.size + item.size and
                abs(item.y - self.player.y) < self.player.size + item.size):
                self.player.upgrade_weapon(item.item_type)
                self.items.remove(item)
    
    def update(self):
        if not self.game_over:
            self.player.update()
            
            # 적 스폰
            self.enemy_spawn_timer += 1
            if self.enemy_spawn_timer >= 180:  # 3초마다
                self.spawn_enemy()
                self.enemy_spawn_timer = 0
            
            # 아이템 스폰
            self.item_spawn_timer += 1
            if self.item_spawn_timer >= 300:  # 5초마다
                self.spawn_item()
                self.item_spawn_timer = 0
            
            # 적 업데이트
            for enemy in self.enemies:
                enemy.update()
            
            # 아이템 업데이트
            for item in self.items[:]:
                item.update()
                if item.collected:
                    self.items.remove(item)
            
            # 충돌 검사
            self.check_collisions()
            
            # 레벨 업
            if self.score >= self.level * 1000:
                self.level += 1
    
    def draw(self, screen):
        screen.fill(BLACK)
        
        if not self.game_over:
            self.player.draw(screen)
            for enemy in self.enemies:
                enemy.draw(screen)
            for item in self.items:
                item.draw(screen)
            
            # UI 그리기
            score_text = self.font.render(f"Score: {self.score}", True, WHITE)
            level_text = self.font.render(f"Level: {self.level}", True, WHITE)
            health_text = self.font.render(f"Health: {self.player.health}", True, WHITE)
            
            # 무기 강화 상태 표시
            weapon_text = self.font.render(f"Bullet: {self.player.bullet_size} | Speed: {self.player.bullet_speed} | Fire: {self.player.shoot_speed}", True, WHITE)
            triple_text = self.font.render("TRIPLE SHOT!", True, CYAN) if self.player.triple_shot else None
            
            screen.blit(score_text, (10, 10))
            screen.blit(level_text, (10, 50))
            screen.blit(health_text, (10, 90))
            screen.blit(weapon_text, (10, 130))
            if triple_text:
                screen.blit(triple_text, (10, 170))
        else:
            # 게임 오버 화면
            game_over_text = self.font.render("GAME OVER", True, RED)
            final_score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
            restart_text = self.font.render("Press R to restart", True, WHITE)
            
            screen.blit(game_over_text, (SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50))
            screen.blit(final_score_text, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2))
            screen.blit(restart_text, (SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 50))

def main():
    game = Game()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game.game_over:
                    game = Game()  # 게임 재시작
        
        game.update()
        game.draw(screen)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()