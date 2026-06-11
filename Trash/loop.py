import serial
import time

# 💡 라즈베리파이 4의 UART 3 포트 오픈
try:
    ser = serial.Serial('/dev/ttyAMA3', baudrate=9600, timeout=1)
    print("🟢 UART 3 (/dev/ttyAMA3) 루프백 테스트 시작!")
except Exception as e:
    print(f"❌ 포트를 열 수 없습니다: {e}")
    exit()

try:
    while True:
        # 1. 보낼 데이터 준비 (0x01 딱 1바이트)
        tx_data = (1).to_bytes(1, byteorder='big')
        
        # 2. 데이터 전송 (TX 핀으로 나감)
        ser.write(tx_data)
        print(f"📤 보냄 (TX): {tx_data.hex().upper()}")
        
        # 잠시 하드웨어 신호가 돌아서 들어올 시간을 줍니다.
        time.sleep(0.1)
        
        # 3. 수신 버퍼 확인 및 데이터 읽기 (RX 핀으로 들어옴)
        if ser.in_waiting > 0:
            rx_data = ser.read(ser.in_waiting)
            print(f"📥 받음 (RX): {rx_data.hex().upper()}")
        else:
            print("❌ 수신된 데이터가 없습니다. (핀 연결을 확인하세요)")
            
        print("-" * 30)
        time.sleep(1) # 1초마다 반복

except KeyboardInterrupt:
    print("\n👋 테스트를 종료합니다.")
finally:
    ser.close()