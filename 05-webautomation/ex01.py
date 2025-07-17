# ex01.py

# 셀레니움 Lib와 크롬 드라이버 설치
# pip install selenium
# pip install webdriver_manager

from selenium import webdriver
import time

# 크롬 드라이버 경로 지정
driver = webdriver.Chrome()
driver.get("https://www.google.com")

print("브라우저가 열렸습니다.")
time.sleep(5)
driver.quit()