# XPATH로 시가총액, PER, PBR 가져오기 (심플 + 캡차 회피)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def setup_driver():
    """캡차 회피 Chrome 드라이버 설정"""
    options = Options()
    
    # 캡차 회피 옵션
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=options)
    
    # 자동화 탐지 회피
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def get_value_by_xpath(driver, xpath, name):
    """XPATH로 값 가져오기"""
    try:
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        value = element.text.strip()
        print(f"✅ {name}: {value}")
        return value
    except Exception as e:
        print(f"❌ {name} 추출 실패: {e}")
        return None

print("🚀 주식 정보 XPATH 값 가져오기 시작")

# 드라이버 설정
driver = setup_driver()

try:
    # 삼성전자 주식 페이지 접속
    print("🌐 삼성전자 페이지 접속 중...")
    driver.get("https://finance.naver.com/item/main.naver?code=005930")
    time.sleep(3)
    
    print("📊 주식 정보 추출 중...")
    
    # 각 정보의 XPATH 정의
    xpaths = {
        "시가총액": '//*[@id="_market_sum"]',
        "PER": '//*[@id="_per"]',
        "PBR": '//*[@id="_pbr"]',
        "배당수익률": '//*[@id="tab_con1"]/div[4]/table/tbody[2]/tr[3]/td',
        "목표주가": '//*[@id="tab_con1"]/div[3]/table/tbody/tr[1]/td/em'
    }
    
    # 각 정보 가져오기
    results = {}
    for name, xpath in xpaths.items():
        value = get_value_by_xpath(driver, xpath, name)
        results[name] = value
    
   

except Exception as e:
    print(f"❌ 오류 발생: {e}")
    input("Enter 키로 종료...")

finally:
    driver.quit()
    print("🔒 브라우저 종료")