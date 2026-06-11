import serial
import time

# 라즈베리 파이의 기본 UART 포트 설정
# 설정을 변경했다면 /dev/ttyS0 또는 /dev/ttyAMA0로 바꿔야 할 수도 있습니다.
SERIAL_PORT = '/dev/serial0' 
BAUD_RATE = 115200 # 가장 안정적인 속도로 테스트

def uart_loopback_test():
    try:
        # 시리얼 포트 열기 (timeout을 주어 데이터가 안 올 때 무한 대기 방지)
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
        print(f"🚀 UART 루프백 테스트 시작: {SERIAL_PORT} @ {BAUD_RATE}")
        
        # 핀이 연결되었는지 확인하기 위해 수신 버퍼 비우기
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        test_messages = ["Hello RPi", "UART Test 123", "Loopback OK"]

        for msg in test_messages:
            # 1. 데이터 송신 (문자열 -> 바이트 + 줄바꿈 문자 추가)
            send_data = (msg + "\n").encode('utf-8')
            ser.write(send_data)
            print(f"\n[송신] -> {msg}")

            # 2. 잠시 대기 (데이터가 물리적으로 돌아올 시간)
            time.sleep(0.1)

            # 3. 데이터 수신 확인
            if ser.in_waiting > 0:
                # 줄바꿈 문자가 올 때까지 읽기
                received_data = ser.readline().decode('utf-8').strip()
                print(f"[수신] <- {received_data}")
                
                if msg == received_data:
                    print("✅ 결과: 일치 (통신 정상)")
                else:
                    print("❌ 결과: 불일치 (데이터 오염)")
            else:
                print("⚠️ 결과: 응답 없음 (핀 연결이나 설정을 확인하세요)")

        ser.close()
        print("\n테스트 종료.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    uart_loopback_test()