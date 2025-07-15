# ex4-4.py
# 세트 set (집합)
# 중복되지 않는 요소를 가지며, 비순차적인 집합 특성을 갖는 데이터 구조 
# 합집합, 교집합, 차집합 

set_0 = { 1, 2, 3, 3 }
set_1 = set ([1,2,3])
set_2 = set( "Hello")
set_3 = set()
print(set_0) # {1, 2, 3}
print(set_1) # {1, 2, 3}
print(set_2) # {'H', 'o', 'e', 'l'}
print(set_3) # set()

#인덱스를 이용하려면 리스트로 타입 변경한다
list_0 = list (set_0)
print( list_0 )
print( list_0[0] )

list_10 = [10, 20, 30 ]
set_10 = set( list_10 )
print( set_10 )

# 집합연산
s1 = set ([1,2,3,4,5,6])
s2= set ([4,5,6,7,8,9])
# 교집합(공통요소)
print ( s1 & s2)
print(s1.intersection(s2))
# 합집합 (전체요소)
print(s1 | s2  ) # 세로바 SHIFT + 원
print( s1.union(s2))
# 차집합 (서로 다른 요소)
print( s1 - s2 ) #{1, 2, 3}
print( s2 - s1 ) # {8, 9, 7}
print(s1.difference(s2)) #{1, 2, 3}

# 요소 추가 
s3 = set([1,2])
s3.add(3)
print(s3)

s3.update([4,5,6])
print(s3)

#요소 삭제 
s3.remove(3)
print( 3 )

# 연습문제
# 두 반의 학생 중 수학을 좋아하는 사람만 추출
math = set(["철수", "영희", "민수"])
science = set(["영희", "지민", "민수"])
# 수학과 과학 모두 좋아하는 학생을 출력하시오
# 수학 또는 과학 중 한 과목이라도 좋아하는 학생
# 수학은 좋아하지만 과학은 좋아하지 않는 학생
print(math & science)
print(math.intersection(science))
print(math | science )
print( math - science )