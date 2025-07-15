# : 코멘트(주석) 단축키 CTRL + / 
# : 설명글이며 실행이 안됨. 
print("hello python") #
print('hello python') #

#/ print() 함수 : 콘솔(표준출력창)에 텍스트를 출력한다. '랑 " 같음 (문자열시작).

#정수형 
a = 123 #대입연산자는 =은 오른쪽값을 왼쪽에 덮어쓰기. 
print(a)
c = -123
print(c)

#실수형 (소숫점있음)
b = 3.14  
print(b)
# 지수형 표현 
d=4.24E10 # 10의 10승
print(d)

# 1o진수 0~9 10
# 8진수 0~7 10
e = 0o10 #8진수 8
print(e)

# 16진수 0~9  a b c d e f 10
f = 0x10
print(f)

# 사칙연산 
a = 3 # a 변수 재사용
b = 4 # b 변수 재사용
print( a + b )
print( a - b )
print( a * b )
print( a / b )

print( a // b) # 나눗셈의 정수 몫 (소숫점은 버림) 0.75 -> 0
print( a % b ) # 나눗셈의 나머지 3 
