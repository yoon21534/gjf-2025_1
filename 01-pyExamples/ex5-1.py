# ex5-1.py
# 파이썬 함수 (Function) : 수학적 함수가 아니라, 코드 모음에 이름을 붙여놓은 것.
# 용도
# 1. 코드 중복 제거
# 2. 코드 재활용
# 3. 모듈화, 간결화

# 함수 선언부 (정의)
# 함수 호출부 (실핼)

#함수의 4가지 패턴
# 1. 매개변수 X 반환값 X
def my_func():
    print("my_func() 함수 호출(실행)!")

my_func()

# 2. 매개변수 O 반환값 X
def my_func2( name  ):
    print(f"{name}님 환영합니다.")
my_func2("Tom")

# 3. 매개변수 X 반환값 O
def my_func3():
    print("my_func3 호출됨!")
    return 'John'
name2 = my_func3()
print(name2)

# 4. 매개변수 O 반환값 O
def my_func4(x,y):
    print('my_func4 호출됨!')
    return x + y 
sum = my_func4( 10,20 )
print(sum)

#매개변수 기본값
def show_message(message, sender="익명"):
    print(f"{message} {sender}" )
show_message("안녕하세요?", "발표자1")
show_message("안녕하세요?" )

#가변 인자 리스트 : 매개변수가 여러개
#함수 호출부의 입력값: 인자
#함수 선언부의 입력값: 매개변수 
def func_sum( *numbers ):
    sum = 0
    for num in numbers:
        sum += num
    return sum 

print(func_sum (1,2,3))
print(func_sum (1,2,3,4,5,6))

# 연습문제
# 1. 매개변수(정수형)가 2개이고, 반환값(정수형)이 1개인 func_multi 함수를 선언하고,
#    매개변수 2개를 곱한 값을 반환하는 함수를 실행하고 결과를 출력하세요.
#    입력값 : 10, 20
#    반환값 : 200
def func_multi( x, y ):
    return x * y
print( func_multi( 2, 3 ) )
# 2. 매개변수(문자열) 1개, 반환값 없는, func_hello 함수를 선언하고,
#    사람이름을 넣으면, "{사람이름}님 환영합니다"라고 출력하는 함수를 선언/실행 하시오.
#    입력값 : "Micle"
#    출력값 : "Micle님 환영합니다"
def func_hello( name ):
    return f"{name}님 환영합니다"
print( func_hello("Micle") )


# 3. 매개변수(리스트) 1개, 반환값(문자열) 1개인 func_list 함수를 선언하고,
#    매개변수의 모든 리스트를 연결한 문자열을 반환하고 출력하시오.
#    입력값 : ["사과","바나나","복숭아"]
#    출력값 : "사과바나나복숭아"
def func_list( fruits ):
    connect_str = ""
    for fruit in fruits:
        connect_str += fruit
    return connect_str
print( func_list( ["사과","바나나","복숭아"] ))

# 4. 매개변수로 정수 1개를 넣으면, 홀짝 여부를 반환(문자열)하는 함수를 선언하시오.
#    입력값 : 10
#    반환값 : "짝수"
def isEven( n ):
    # 조건부 표현식
    return "짝수" if n % 2 == 0 else "홀수"
print( isEven( 10 ) )
print( isEven( 11 ) )



# 5. 단어를 꺼꾸로 출력하는 함수를 선언하시오.
#    입력값 : "I like python!"
# #    반환값 : "!nohtyp ekil I"
def revers_str( input_string ):
    for i in range( len(input_string)-1, -1, -1 ):
        print( input_string[i], end="" )
revers_str("I like python!")






