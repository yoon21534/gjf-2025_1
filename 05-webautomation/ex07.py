# 네이버 뉴스 IT/과학 섹션 간단 크롤링

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import csv
from datetime import datetime

def crawl_naver_it_news():
    """네이버 IT/과학 뉴스 크롤링"""
    
    # Chrome 설정
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        print("🚀 네이버 IT/과학 뉴스 크롤링 시작...")
        
        # 1. 네이버 뉴스 메인 페이지 접속
        print("📰 네이버 뉴스 메인 페이지 접속 중...")
        driver.get("https://news.naver.com/")
        time.sleep(3)
        
        # 2. IT/과학 버튼 클릭
        print("💻 IT/과학 섹션으로 이동 중...")
        
        # 여러 방법으로 IT/과학 버튼 찾기
        selectors = [
            "//a[contains(text(), 'IT/과학')]",
            "//a[@href='/section/105']",
            "//*[contains(@class, 'nav')]//a[contains(text(), 'IT/과학')]",
            "//nav//a[contains(text(), 'IT/과학')]"
        ]
        
        button_clicked = False
        for selector in selectors:
            try:
                it_button = driver.find_element(By.XPATH, selector)
                it_button.click()
                print("✅ IT/과학 버튼 클릭 완료")
                time.sleep(3)
                button_clicked = True
                break
            except:
                continue
        
        if not button_clicked:
            # 모든 방법 실패시 직접 URL 이동
            print("⚠️ 버튼 클릭 실패, 직접 URL로 이동")
            driver.get("https://news.naver.com/section/105")
            time.sleep(3)
        
        # 뉴스 링크 수집
        news_list = []
        links = driver.find_elements(By.XPATH, "//a[contains(@href, '/article/')]")
        
        for i, link in enumerate(links[:10]):  # 상위 10개만
            try:
                title = link.text.strip()
                url = link.get_attribute('href')
                
                if title and url and len(title) > 10:  # 유효한 제목만
                    news_list.append({
                        'index': len(news_list) + 1,
                        'title': title,
                        'link': url,
                        'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    print(f"📰 [{len(news_list)}] {title[:50]}...")
            except:
                continue
        
        return news_list
        
    except Exception as e:
        print(f"❌ 에러: {e}")
        return []
    finally:
        driver.quit()

def save_csv(news_list):
    """CSV 파일 저장"""
    if not news_list:
        print("❌ 저장할 데이터가 없습니다.")
        return
    
    filename = f"it_news_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['index', 'title', 'link', 'time'])
        writer.writeheader()
        writer.writerows(news_list)
    
    print(f"✅ 저장완료: {filename} ({len(news_list)}개)")

def main():
    # 크롤링 실행
    news = crawl_naver_it_news()
    
    # 결과 출력
    if news:
        print(f"\n📊 총 {len(news)}개 뉴스 수집완료!")
        save_csv(news)
    else:
        print("❌ 뉴스를 가져올 수 없습니다.")

if __name__ == "__main__":
    main()