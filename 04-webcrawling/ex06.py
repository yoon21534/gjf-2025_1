# csv(json) 파일로 크롤링한 결과를 저장하기
# .csv 콤마로 구분된 텍스트 데이터
# .json Key-Value 형태의 텍스트 데이터
# 번호, 이름, 나이 
# 1, 홍길동, 30 
# 2, 사임당, 35 

import requests
from bs4 import BeautifulSoup
import csv
import json
import datetime

def fetch_articles(url='https://news.ycombinator.com/'):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    articles = soup.select('.titleline > a')
    
    data = []
    for a in articles:
        title = a.text.strip()
        link = a['href'].strip()
        data.append({'title': title, 'link': link})
    
    return data

def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['title', 'link'])
        writer.writeheader()
        writer.writerows(data)

def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    print("📰 Hacker News 기사 크롤링 중...")
    data = fetch_articles()

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    csv_file = f'hn_news_{today}.csv'
    json_file = f'hn_news_{today}.json'

    save_to_csv(data, csv_file)
    save_to_json(data, json_file)

    print(f"✅ CSV 저장 완료: {csv_file}")
    print(f"✅ JSON 저장 완료: {json_file}")
    print(f"📊 총 {len(data)}개의 기사를 수집했습니다.")

if __name__ == "__main__":
    main()