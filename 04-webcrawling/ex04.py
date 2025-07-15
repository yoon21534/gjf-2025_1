import requests
from bs4 import BeautifulSoup

url = "http://127.0.0.1:5500/04-webcrawling/test2.html"

html = requests.get(url).text 

# HTML 파싱(분석,추출)
soup = BeautifulSoup(html,'html.parser')

# 태그 접근 방법 
print(soup.title) # <title>예제 페이지</title>
print(soup.title.text) # 예제 페이지
print(soup.h1['id']) # title
print(soup.h1.text) # Hello BeautifulSoup
print(soup.p) # <p class="content">첫 번째 문단입니다.</p>
print(soup.p['class'][0])  # content
print(soup.p.text) # 첫 번째 문단입니다.
print(soup.find_all("p")[0].text) # 첫 번째 문단입니다.
print(soup.find_all("p")[1].text) # 두 번째 문단입니다.
print(soup.find_all('a')[0].text ) 
print(soup.find_all('a')[1].text ) 
print(soup.find_all('a')[0]['href']) 
print(soup.find_all('a')[1]['href']) 

print(soup.find('p')) # 첫 번째 p만 
print(soup.find_all('p')) # 리스트 p
print(soup.find('p', class_='content'))
print(soup.find('h1', id='title'))