# ex4-5.py
# 리스트와 반복문

fruits = ["사과", "바나나", "체리", "딸기"]
# 리스트의 모든 요소 출력(순환)
# 1. for in 구문
for fruit in fruits:
    print( fruit )

# 2. range() 함수
for i in range( len(fruits) ):
    print( fruits[i] )

# 3. enumerate() 함수
for index, fruit in enumerate(fruits):
    print(f'{index}, {fruit}')

#깃 테스트