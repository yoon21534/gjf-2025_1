# ex8-1.py

# 예외 처리

# 예외(Exception, 에러, 오류) : 프로그램 중단이 될 수 있는 상황!

# 존재하지 않는 파일 열기
# f = open("없는파일", "r") # FileNotFoundError

# 0으로 나누기
# num = 0
# print( 5 / num )  # ZeroDivisionError

# 리스트 인덱스 오류
# a = [1, 2, 3]
# print( a[3] ) # IndexError

try:
    5/0
except ZeroDivisionError as e:
    print( e )    

try:
    5/0
except:
    print( "오류 발생!" )     

print("저는 살아 있습니다!")


try:
    age = int(input("나이를 입력하세요: "))
except:
    print("아라비아 숫자로 입력하세요.")
else: #오류가 없을때
    if age <= 18:
        print("미성년자입니다.")
    else:
        print("성인입니다.")

try: 
    f = open("없는파일", "r")
except:
    print("없는 파일 오류입니다.")
    f = None
finally: # 오류가 발생하든 안하든 실행되는 코드
    if f: # f객체가 생성되어 있다면,
        f.close()