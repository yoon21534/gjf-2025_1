# ex03.py

import requests
from bs4 import BeautifulSoup

# pip install beautifulsoup4

# 라이브서버 test1.html 주소
url = "http://127.0.0.1:5500/04-webcrawling/test1.html"

html = requests.get(url).text 

# HTML 파싱(분석,추출)
soup = BeautifulSoup(html,'html.parser')

# H1 태그 내용 출력 
print( soup.find('h1').text )

