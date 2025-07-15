# ex3-4.py
#연습문제 
# 자판기 프로그램(무한루프)을 작성하시오.
# 사용자가 1을 입력하면, "콜라가 나옵니다"
# 2를 입력하면 "사이다가 나옵니다"
# 3을 입력하면 "오렌지쥬스가 나옵니다"
# 콜라의 잔고는 3개
# 사이다의 잔고는 2개
# 오렌지의 잔고는 4개 입니다.
# 잔고 소진시 "콜라(사이다,오렌지쥬스) 잔고가 떨어졌습니다." 라고 출력하시오.

stock_cola = 3
stock_cider = 2
stock_juice = 4
while True:
    menu = int( input('콜라(1) 사이다(2) 오렌지쥬스(3): ') )
    if menu == 1:
        if stock_cola <= 0:
            print("콜라 잔고가 떨어졌습니다")
            continue
        print("콜라가 나옵니다")
        stock_cola -= 1
    elif menu == 2:
        if stock_cider <= 0:
            print("사이다 잔고가 떨어졌습니다")
            continue
        print("사이다가 나옵니다")
        stock_cider -= 1
    elif menu == 3:
        if stock_juice <= 0:
            print("오렌지쥬스 잔고가 떨어졌습니다")
            continue
        print("오렌지쥬스가 나옵니다")
        stock_juice -= 1
    elif menu == 10:
        print("자판기 프로그램을 종료합니다.")
        break
    else:
        print("메뉴번호를 확인해 주세요~")

# 연습문제
# 텍스트 야구게임(무한루프)을 작성하시오.
# 투수는 공을 던지는데, 스트라이크 확률이 70%이고, 볼 확률이 30%입니다.
# 투수가 공을 계속 던졌을 때 볼 카운트(스트라이크와 볼)을 출력하시오.
# 확률은 rand.randint()함수를 이용합니다.
# 출력 예시
# 1번 송구: 스트라이크   - 1스트라이크 0볼
# 2번 송구: 볼          - 1스트라이크 1볼
# 3번 송구: 스트라이크  - 2스트라이트 1볼
# 4번 송구: 스트라이크   -3스트라이크 1볼 - 스트라이크 아웃!
# 게임끝
import random
ball_type = o # 0 ball 1 strike
ball_count = 0
srike_count = 0

while True:
    ball = random.randint(0, 100)+1 # 1~100까지의 랜덤 수 
    if ball <= 70:
        ball_type = 1 
    else:
        ball_type = 0 #ball
    if ball_type == 1 :
        strike_count += 1
        print(f"{count}번째 송구: 스트라이크")
    else:
        ball_count += 1
        print(f"{count}번째 송구: 볼")
    count += 1