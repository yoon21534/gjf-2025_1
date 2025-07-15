# 연산자

#연산자 우선순위 
print( 10 -2 * 4 /2 )

# 1. **         거듭제곱 
# 2. * / // %   곱셈, 나눗셈
# 3. + -        덧셈, 뺼셈
# 4. == != > ?  비교연산자
# 5. not        부정연산자
# 6. and        AND로직
# 7. or         OR로직

a = 10
b = 3
print( a ** b ) # 10*10*10 = 1000

# 비교연산자 : 결과는 True/False로 나온다.
a = 5
b = 3
print( a == b) # 같은가
print( a != b) #같지않은가
print( a > b) #A가 더 큰가 . 초과
print( a < b) #더 작은가 . 미만
print( a <= b) # a가 b보다 같거나 작은가 . 이하
print( a >= b) # 같거나 큰가 . 이상

# 논리연산자 : 부정,AND,OR  / 결과는 True/False로 나온다.
c = True
d = False
print( not c )
print( c or d )
print( c and d )

# or 로직 :~이거나, ~또는, ~일수도, 둘중 하나
print( True or True )
print( True or False )
print( False or True )
print( False or False )
# and 로직 : ~이고, ~이면서, 둘다
print( True and True )
print( True and False )
print( False and True )
print( False and False )