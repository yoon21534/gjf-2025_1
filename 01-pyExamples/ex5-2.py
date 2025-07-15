
# ex5-2.py
# 종합 연습문제
# 숫자 맞추기 게임


import random 
ran_int=random.randint(1,20)
count = 1
while True:
    user_int = int(input('숫자 입력: '))
    if user_int < ran_int:
            print("너무 작아요")
            count += 1
    elif user_int > ran_int:
            print("너무 커요")
            count += 1
    else:
            print(f"정답입니다! {count}번 만에 맞췄습니다")