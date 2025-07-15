# ex7-6-main.py

# 파이썬 모듈 시스템

# 모듈 임포트
import ex7_6_mod # 파일이름에 - 대시는 안됨. .py 확장자를 뺌.

print( ex7_6_mod.add(10, 20) )
print( ex7_6_mod.sub(10, 20) )

print( ex7_6_mod.PI )

print( ex7_6_mod.Math().solv( 5 ) )

# from절
from ex7_6_mod import add, sub

print( add(10, 20) )