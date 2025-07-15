# ex7-2.py

# 계산기 기능 구현 - 함수

# global 영역
result1 = 0 

def add(num):  #함수 안에서 선언(생성)된 변수는 바깥쪽(global)에서 볼수 없음.    
    # add 함수영역
    global result1
    result1 += num
    return result1  # 함수안에서 선언된 변수는 함수종료시 함께 종료됨.

print( add( 10 ) ) # 10
print( add( 10 ) ) # 20

def sub( num ):
    global result1
    result1 -= num
    return result1

print( sub(10) )
print( sub(10) )

# 계산기 기능 구현 - 클래스
class Calc:
    result = 0
    def add(self, num):
        self.result += num
    def sub(self, num):
        self.result -= num

calc = Calc()
calc.add( 10 )
print( calc.result )
calc.add( 10 )
print( calc.result )
calc.sub( 10 )
print( calc.result )
calc.sub( 10 )
print( calc.result )

# 연습문제
# 당근농장을 클래스로 구현해 봅니다.
# 클래스이름 Farm이라고 하고,
# 내부변수는 carret_number = 0으로 초기화 하고
# plant( num )함수를 실행하며, num 수만큼 carret_number가 증가합니다.
# 당근을 10개 생산하고 현재 공근의 당근갯수를 출력하시오
class Farm:
    carret_number = 0
    def plant( self, num ):
        self.carret_number += num

farm = Farm()
farm.plant( 10 )
print( farm.carret_number )