# proj01.py

# 1인 개인 미니 프로젝트

# 간단한 계산기
# 콘솔 기반의 간단한 사칙연산이 가능한 계산기를 만들어 봅니다.
# 클래스로 설계하면 더 좋습니다.

# 입력/출력 예시

"""
=== 간단한 계산기 ===
1. 덧셈
2. 뺄셈
3. 곱셈
4. 나눗셈
5. 종료

선택하세요 (1-5): 1
첫 번째 숫자를 입력하세요: 10
두 번째 숫자를 입력하세요: 5
결과: 10.0 + 5.0 = 15.0

=== 간단한 계산기 ===
1. 덧셈
2. 뺄셈
3. 곱셈
4. 나눗셈
5. 종료

선택하세요 (1-5): 5
프로그램을 종료합니다.
"""

class Calulator:
    def __init__(self):
        pass
    def add(self, x, y ):
        return x + y
    def sub(self, x, y ):
        return x - y
    def mul(self, x, y ):
        return x * y
    def div(self, x, y ):
        if y == 0:
            return 0
        return x / y

if __name__ == "__main__":
    calc = Calulator()

    print('''
=== 간단한 계산기 ===
1. 덧셈
2. 뺄셈
3. 곱셈
4. 나눗셈
5. 종료

선택하세요 (1-5):
''')
    menu = int(input(""))
    num1 = int(input("첫번째 숫자: "))
    num2 = int(input("두번째 숫자: "))

    if menu == 1:
        result = Calulator().add(num1, num2)
        print( f"결과: {num1} + {num2} = {result}" )
    elif menu == 2:
        result = Calulator().sub(num1, num2)
        print( f"결과: {num1} - {num2} = {result}" )
    elif menu == 3:
        result = Calulator().mul(num1, num2)
        print( f"결과: {num1} * {num2} = {result}" )
    elif menu == 4:
        result = Calulator().div(num1, num2)
        print( f"결과: {num1} / {num2} = {result}" )    