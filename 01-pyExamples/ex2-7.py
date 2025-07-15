# ex2-7.py

# 사용자 입력 input ()함수
name = input ('이름을 입력하세요:')

# 형식화된 출력문
print(f'입력받은 이름은 {name}입니다.')

print( '입력받은 이름은 ' + name + '입니다.')

# 연습문제
#1. 
a =  input ('정수 1 입력: ')
b = input('정수 2 입력: ')
x = (int(a))
y = (int(b))
print( 10*x + y )

#2 
a = input ( '철수 주사위 점수: ')
b = input ( '영희 주사위 점수: ')
x = (int(a))
y = (int(b))

if (x+y)%2==0:
    print(True)
else:
    print(False)


