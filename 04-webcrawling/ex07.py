from bs4 import BeautifulSoup
import re
import urllib.request

result = ''

for i in range(1,23):
    #싱글로 둘러주기, 페이지 별료 page = 페이지번호 이므로 페이지 번호만 다르게 해서 다른 페이지의 내용도 긁어온다.
    list_url = 'https://home.ebs.co.kr/ladybug/board/6/10059819/oneBoardList?c.page='+str(i)+'&searchCondition=&searchConditionValue=0&searchKeywordValue=0&searchKeyword=&bbsId=10059819&'
    url = urllib.request.Request(list_url)
    f = urllib.request.urlopen(url).read().decode("utf-8")

    soup = BeautifulSoup(f, 'html.parser')

    review = soup.find_all('p', class_ = 'con')
    date = soup.find_all('span', class_ = 'date')

    # re : 정규식
    # zip : 두 리스트를 병렬로 순회하는 함수 [리뷰] [날짜]

    for i, k in zip(review, date):
        #re.sub(제거할 텍스트, 대체할 텍스트, 원본텍스트)
        result += k.text +' '+ re.sub('\n|\r', '', i.text) + '\n'
        #print(k.text +' '+ re.sub('\n', '', i.text) + '\n')

print(result)