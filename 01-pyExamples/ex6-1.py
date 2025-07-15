#  ec6-1 
# 파일 입출력

# 파일 생성하기

# w 쓰기, r 읽기 전용 , a 추가 
f = open("test1.txt", 'w', encoding='utf-8')
# 줄바꿈 특수문자 \n 
f.write('this is test file.\n  테스트파일 입니다')
f.close() # 파일닫기 

#파일 읽어오기
f = open("test1.txt", 'r', encoding='utf-8')
while True:
    line = f .readline()
    if not line:
        break
    print(line)
f.close()

f = open("test1.txt", 'r', encoding='utf-8') 
lines = f.readlines()
for line in lines:
    print( line.strip()) # strip() 좌우 공백 제거 
    f.close()

#파일 내용 추가
f = open ("test1.txt", "a", encoding='utf-8')
f.write("\n추가된 내용입니다.\n")
f.close()

#with문 사용 : close ()함수 생략 가능 
with open ("test1.txt", "a", encoding='utf-8') as f: 
    f.write("추가된 내용입니다.2\n")
#with문 종료시 자동으로 close ()호출됨. 
