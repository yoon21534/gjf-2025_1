# ex3-5.py
# 이중반복문 : 반복문 안에 반복문이 들어가는 구조

for i in range (0,6) :
    print(f"i={i}")
    for j in range(0,6):
        print(f"j={j}", end=",") #구분자로 줄바꿈없음 
    print() #단순 줄바꿈 

# 구구단 출력 2단 ~ 9단
# 2 x 1 = 2 3 x 1 =3 ... 9 x 1 = 9
# 2 x 2 = 2 3 x 2 =6 ... 9 x 2 = 18
# ...
#                       9 x 9 = 81 
for dan in range (2, 10): 
    print(f"{dan}단")
    for num in range(1,10): 
        print(f"{dan} x {num} = {dan * num}")
    print()

# 별찍기
# N = 5, NxN 정사각형의 별을 출력한다.
# *****
# *****
# *****
# *****
# *****
# range( stop ) 5 => 0~4
# range( start, stop) 1, 5 => 1~4
# range( start, stop, step ) 1, 10, 2 => 1 3 5 7 9
N = 5
for i in range(N): # 0~4 5번
    for j in range(N):
        print("*", end="")
         
# *
# **
# ***
# ****
# *****