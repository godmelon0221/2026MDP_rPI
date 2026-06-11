import serial
import time
import sys

# UART 3 포트 세팅 (/dev/ttyAMA3)
UART_PORT = '/dev/ttyAMA3'
BAUDRATE = 9600

print("=========================================")
print(f"📡 {UART_PORT} 포트 수신 테스트를 시작합니다.")
print("=========================================")

try:
    # 데이터가 들어올 때까지 대기하지 않도록 timeout=0(Non-blocking)으로 설정
    ser = serial.Serial(UART_PORT, baudrate=BAUDRATE, timeout=0)
    print(f"🟢 {UART_PORT} 포트가 성공적으로 열렸습니다!")
    print("📥 STM32로부터 데이터를 기다리는 중... (종료하려면 Ctrl+C)")
    print("-----------------------------------------")
except Exception as e:
    print(f"❌ {UART_PORT} 포트를 열 수 없습니다. 에러명: {e}")
    print("💡 팁: 'ls /dev/ttyAMA*' 명령어로 포트가 활성화되어 있는지 확인하세요.")
    sys.exit(1)

try:
    while True:
        # 현재 수신 버퍼에 쌓여 있는 바이트 수 확인
        waiting_bytes = ser.in_waiting
        
        # 우리가 원하는 센서 패킷 크기(4바이트) 이상 쌓였을 때 작동
        if waiting_bytes >= 4:
            # 정확히 4바이트만 읽어옴
            rx_data = ser.read(4)
            
            # 읽어온 데이터의 길이가 정확히 4바이트인지 다시 한번 체크
            if len(rx_data) == 4:
                temp = rx_data[0]
                hum = rx_data[1]
                cds = rx_data[2]
                gas = rx_data[3]
                
                # 1. 보기 좋게 파싱된 센서값 출력
                print(f"📥 [수신 성공] 온도: {temp}℃ | 습도: {hum}% | 조도: {cds}% | 가스레벨: {gas}")
                
                # 2. (디버깅용) 들어온 순수 바이너리/헥사 데이터도 같이 출력
                # print(f"   └─ Raw Hex: {rx_data.hex().upper()}")
            else:
                print(f"⚠️ 데이터 유실 발생 (4바이트 미만 수신): {len(rx_data)} bytes")
                
        # CPU 과점유를 막기 위해 0.01초씩 쉬어줍니다.
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n👋 사용자에 의해 테스트가 종료되었습니다.")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("🧹 UART 포트를 안전하게 닫았습니다.")