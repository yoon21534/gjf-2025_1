# 파이썬의 주요 데이터 타입

# 숫자 number
# 정수형 : int
age = 30
year = 2025
print(age)
print(year )
print(type(age))

# 실수형 : float
pi = 3.141592
print(pi)
print(type(pi))

# 복소수형 : complex 
c1 = 3 + 4j
print(type(c1))
print(c1.real) #실수부
print(c1.imag) #허수부 

# 문자열 String
string1 = 'Hello, Python!'
string2 = "Hello, Python!"
print( type(string1))
print(len(string1)) # 문자열 길이

# 리스트 List - 여러 값을 순서대로 저장하는 시퀀스(순차적) 자료형
mylist = [1,2,'hello',3.14, True]
print( type(mylist))
print(mylist[0])
print(mylist[2])
mylist.append('new')
print(mylist)

# 튜플 Tuple - 리스트이면서 변경불가한 자료형 
mytuple = (10,20,'apple',False)
print( type(mytuple))
print(mytuple[2])
mytuple.append( 'NEW') # 불가
print(mytuple)

# 딕셔너리 Dictionary - key와 값(value)의 쌍으로 이루어진 비순차형 자료형
person = {'name':'alice','age':30.'city':'seoul'}
print(person['name'])
print(person['age'])
print(person['city'])
print(person)
print(person.keys())
print(person.values())

# 소괄호 ()
# 함수
print("123")
mytuple2 = (10.20)
# 중괄호  {}
mydic2 = {'ket':'value'} #딕셔너리
# 대괄호 []
mylist2 = [30,40] # 리스트 



# 세트 Set - 중복되지 않는 요소들로 이루어진 비순차형 자료형
myset = {1,2,3,2,1}
print(myset)


# 불리언 Boolean
is_true = True
print(type(is_true))

# 값없음 Nonetype - none 이라는 단일 값을 가짐. 변수 초기화시 많이 사용
result= None
prin( type(result) )
if result == none:
    print( '결과값이 없음' ) 