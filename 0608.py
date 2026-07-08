import serial
import time

ser = serial.Serial('/dev/ttyAMA4', 128000, timeout=1)
print(f"✅ 포트 열림: {ser.name}")

while True:
    waiting = ser.in_waiting
    if waiting > 0:
        data = ser.read(min(waiting, 64))
        print(f"📡 {waiting}바이트 수신: {data.hex()}")
    else:
        print("⚠️ 데이터 없음 (0바이트)")
    time.sleep(0.5)