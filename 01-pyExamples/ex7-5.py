# ex7-5.py

# 클래스 종합 예제

class Animal:
    def __init__(self, name):
        self.name = name
    def speak(self):
        print(f"{self.name}이 소리를 냅니다.")
    def move(self):
        print(f"{self.name}이 움직입니다.")

class Flyable:
    def fly(self):
        print(f"{self.name}이 납니다.")

class Swimmable:
    def swim(self):
        print(f"{self.name}이 헤엄칩니다.")

class Dog(Animal):
    def speak(self): # 오버라이딩
        print(f"{self.name}이 멍멍 짖는다.")

class Duck(Animal, Flyable, Swimmable): 
    def speak(self): # 오버라이딩
        print(f"{self.name}이 꽥꽥 소리칩니다.")
    def move(self):
        super().move() # 상속받은 부모의 클래스에 접근 super 예약어
        self.fly()
        self.swim()

# 현재 이 파일이 직접 실행 되었는가? 그때만 아래 코드를 수행한다.
if __name__ == "__main__":
    dog = Dog("바둑이")
    dog.speak()
    dog.move()
    duck = Duck("오리")
    duck.speak()
    duck.move()