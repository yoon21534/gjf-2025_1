import requests

url = "https://www.vnaver.com"

# http 응답은 4가지 형태 
# 1. html 파일
# 2. json
# 3. xml
# 4. file파일 (bin) 다운로드 

response = requests.get(url)

print(response.text)

# pip install requests
#  관리자 권한으로 콘솔 열기
#  py -m pip install requests
#  python.exe -m pip install --upgrade pip
