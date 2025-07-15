# ex6-3
# pandas 라이브러리로 csv 파일 읽고 쓰기 
# pandas : 데이터분석에 특화된 라이브러리
#        : Data Frame 행열 2차원 데이터 처리에 매우 유용함. 
# 
# pandas 라이브러리 설치
# pip install pandas 
# py -m pip install pandas

import pandas as pd 


#데이터 프레임 생성
data = { 
    "이름": ["홍길동", "김철수", "이영희"],
    "나이": [30,25,35],
    "도시": ["서울","부산","수원"]
}
#데이터 프레임 객체 생성
df = pd.DataFrame( data )

#CSV 파일로 저장
df.to_csv("people_pandas.csv", index=False, encoding='utf-8')
print("CSV 파일 저장 완료")

# pandas로 csv파일 읽어 드리기
#  encoding="utf-8-sig : 유니코드 이모지 지원
df = pd.read_csv("people_pandas.csv", encoding="utf-8-sig")
print(df)
print("CSV 파일 읽기 완료")