# ex08.py
# https://www.hankyung.com/globalmarket/news-globalmarket
# 한경글로벌 마켓의 뉴스 기사 타이틀 10개 / image url을 출력하시오.

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def crawl_hankyung_news():
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        print("한경글로벌 마켓 뉴스 크롤링 시작...")
        driver.get("https://www.hankyung.com/globalmarket/news-globalmarket")

        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="contents"]//ul[contains(@class,"list_basic")]/li')))
        
        articles = driver.find_elements(By.XPATH, '//*[@id="contents"]//ul[contains(@class,"list_basic")]/li')[:10]

        for idx, article in enumerate(articles, start=1):
            title_elem = article.find_element(By.XPATH, './/a[contains(@class,"tit")]')
            title = title_elem.text.strip()

            img_elem = article.find_element(By.XPATH, './/img')
            img_url = img_elem.get_attribute("src")

            print(f"{idx}. {title}")
            print(f"   이미지 URL: {img_url}\n")

    except Exception as e:
        print("에러 발생:", e)
    finally:
        driver.quit()

if __name__ == "__main__":
    crawl_hankyung_news()
