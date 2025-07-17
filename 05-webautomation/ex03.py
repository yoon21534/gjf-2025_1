# 안정적인 Chrome 자동화 (캡차 회피 포함)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random

def random_delay(min_sec=1, max_sec=3):
    """랜덤한 시간 대기"""
    delay = random.uniform(min_sec, max_sec)
    print(f"  대기 중... ({delay:.1f}초)")
    time.sleep(delay)

def setup_chrome_driver():
    """Chrome 드라이버 설정"""
    print("Chrome 드라이버 설정 중...")
    
    chrome_options = Options()
    
    # 캡차 회피 설정
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User-Agent 설정
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # 안정성을 위한 옵션들
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--window-size=1200,800")
    
    # 브라우저 창을 닫지 않도록 설정
    chrome_options.add_experimental_option("detach", True)
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ Chrome 드라이버 생성 성공!")
        
        # navigator.webdriver 속성 숨기기
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
        
    except Exception as e:
        print(f"❌ Chrome 드라이버 생성 실패: {e}")
        return None

def main():
    driver = None
    
    try:
        # 드라이버 설정
        driver = setup_chrome_driver()
        if not driver:
            print("드라이버를 생성할 수 없습니다.")
            return
        
        # Google 접속
        print("\n🌐 Google 접속 중...")
        driver.get("https://www.google.com")
        random_delay(2, 4)
        
        # 페이지 로딩 확인
        wait = WebDriverWait(driver, 10)
        
        # 검색창 찾기
        print("🔍 검색창 찾는 중...")
        try:
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
            print("✅ 검색창 찾기 성공!")
        except:
            # 다른 방법으로 검색창 찾기
            search_box = driver.find_element(By.CSS_SELECTOR, "input[title='검색']")
        
        # 검색어 입력
        search_text = "Python Selenium 자동화"
        print(f"⌨️  '{search_text}' 입력 중...")
        
        # 천천히 타이핑
        for char in search_text:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        
        random_delay(1, 2)
        
        # 엔터 키 또는 검색 버튼 클릭
        print("🔍 검색 실행...")
        search_box.send_keys(Keys.RETURN)
        
        # 검색 결과 대기
        random_delay(3, 5)
        
        # 검색 결과 확인
        try:
            results = driver.find_elements(By.CSS_SELECTOR, "h3")
            print(f"\n📊 검색 결과 ({len(results)}개):")
            
            for i, result in enumerate(results[:5], 1):
                if result.text.strip():
                    print(f"  {i}. {result.text}")
        except Exception as e:
            print(f"검색 결과 가져오기 실패: {e}")
        
        print(f"\n⏰ 100초 후 자동 종료됩니다...")
        print("   수동으로 종료하려면 Ctrl+C를 누르세요.")
        
        # 긴 대기 시간
        for i in range(100, 0, -10):
            print(f"   남은 시간: {i}초")
            time.sleep(10)
        
    except KeyboardInterrupt:
        print("\n⛔ 사용자가 중단했습니다.")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("상세 오류 정보:")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            print("🔒 브라우저를 열어둡니다. 수동으로 닫으세요.")
            # driver.quit()는 호출하지 않음 (브라우저를 열어둠)

if __name__ == "__main__":
    print("=== Chrome 자동화 시작 ===")
    main()
    print("=== 프로그램 종료 ===")