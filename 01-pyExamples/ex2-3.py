# 연습문제

#1. 
print("Python is easy!")

#2.
str = "Hello python"
print(str [0] )
print(str[-1])

#3
s = "Life is short, use Python"
print(s[15:])

#4
a = 'Python'
b = 'is fun'
print(a+b)

#5
s="Hi!"
print(s*3)

#6
print("I ate %d apples" %5)

#7
s = "banana"
print( s.count('a'))

#8
s = "hello"
print(s.find('e'))
print(s.index('e'))
print(s.find('z'))
print( s.index('z') )
try:
        print( s.index('z') ) 
except ValueError:  
        print("문자열을 찾을 수 없습니다.")

#9
s="apple,banana,grape"
print(s.split(','))

#10
s = "I love Java"
print(s.replace("java","Python"))