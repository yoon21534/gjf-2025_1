# ex7-3.py
# 생성자 함수 : 클래스 객체가 생성될 때 자동 호출되는 함수
# 용도 : 내부 변수 초기화

class Car:
    def __init__(self):
        print("생성자 함수 자동 호출됨.")
        pass # 아무 수행도 하지 않음을 기술

car = Car()

# 생성자 함수를 통한 클래스 변수 초기화
class VoltCar:
    # brand = ""
    # color = ""
    def __init__(self, brand, color):
        self.brand = brand
        self.color = color
    
    def info(self):
        print( f"{self.brand}, {self.color}")

vc = VoltCar("테슬라", "블루")
vc.info()