# ex6-2
# CSV 파일 읽기/쓰기
# CSV (Comma seperated Value) : 엑셀,DB와 호환됨.
# ex)  번호 이름  학번
#       1  hong 0001
#       2  lee  0002
# 번호 이름  학번
# 1  hong 0001
# 2  lee  0002

import csv #scv 모듈(기본 라이브러리) 사용 

data = [
    ["이름", "나이", "도시"],
    ["홍길동",30,"서울"],
    ["김철수",25,"부산"],
    ["이영희",35,"수원"]
]

# csv로 저장하기
#newline='' : 줄간격 공백 제거 옵션.
with open("people.csv","w", newline='',encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(data)

print("CSV 파일 저장 완료")

#CSV 파일 읽어오기 
with open ("people.csv","r",encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        print(row)
