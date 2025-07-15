# ex4-1.py
# 리스트 List

#빈 리스트 
empty_list = []
print( empty_list )

numbers = [1, 2, 3, 4, 5]
mixed_list = ["apple", 123, 3.14, True ]
nested_list = [ [1,2], ["a","b"], [True, False]]

print( numbers [0]) # 0번째 인덱스 
print( numbers [:3] ) # [1, 2, 3] 0~2 인덱스 
print( numbers[1:]) # [2, 3, 4, 5] 1~마지막 인덱스 
print( numbers[::2]) # [1, 3, 5] 두 칸씩 인덱스 
print( numbers[::-1]) # [5, 4, 3, 2, 1] 역순으로 

#요소 변경
my_list = ["a", "b", "c" ] #인덱스 0,1,2
my_list[1] = "hello" 
print( my_list )
#my_list[3] = "d" # index out of range
my_list.append("d") #마지막에 추가하는거 
print(my_list) # [5, 4, 3, 2, 1]

my_list.insert(0, "z")
print(my_list) # ['z', 'a', 'hello', 'c', 'd']

other_list = ["x","y"]
my_list.extend( other_list )
print( my_list ) # ['z', 'a', 'hello', 'c', 'd', 'x', 'y']

#요소 삭제
my_list = ['a','b','c','d','e']
del my_list[2] # index 2의 'c' 삭제
print(my_list) # ['a', 'b', 'd', 'e']

my_list.remove('b')
print( my_list) # ['a', 'd', 'e']

my_list.clear() #모든 요소 삭제
print(my_list) 

#리스트의 길이(요소갯수)
print(len(  mixed_list))

socores = [85, 92, 78, 92, 65]
# 정렬 (오름차순) 
socores.sort()
print(socores)   # [65, 78, 85, 92, 97] 
socores.reverse()
print(socores) # [97, 92, 85, 78, 65]

print( socores.count(92))
print( socores.index(78))
numbers2 = 10, 20, 30 
print( numbers2)
#요소가 하나인 튜플은 쉼표 사용 
numbers3 = (5)      # 정수 5
numbers4 = (5, )    # 튜플
print ( numbers3 )
print ( numbers4 ) 

# 함수의 반환값으로 튜플 사용
def get_user_date()
    return "김철수" , 15, "서울: 

name,age city = get_user_data()
print(type(get_user_data()) )
print( name, age, city )
