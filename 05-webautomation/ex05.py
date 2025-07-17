from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

driver = webdriver.Chrome()
driver.get("https://nid.naver.com/nidlogin.login")
time.sleep(2)


# 아이디 입력(XPATH)
login = driver.find_element(By.XPATH,'//*[@id="id"]').click()
driver.find_element(By.XPATH,'//*[@id="id"]').send_keys('id')
time.sleep(2)

# 비밀번호 입력(XPATH)
password = driver.find_element(By.XPATH,'//*[@id="pw"]').click()
driver.find_element(By.XPATH,'//*[@id="pw"]').send_keys('password')
time.sleep(2)

# 로그인 버튼 클릭(XPATH)
login_button = driver.find_element(By.XPATH,'//*[@id="log.login"]').click()

time.sleep(10)