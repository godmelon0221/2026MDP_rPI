import serial
import time

# ⚠️ [중요] 아까 ls 명령어 결과에 ttyAMA1이 없었기 때문에, 
# UART3이 ttyAMA2나 ttyAMA4 등으로 매핑되었을 확률이 높습니다.
# 만약 코드를 실행했는데 데이터가 안 올라오면 이 경로를 "/dev/ttyAMA2" 등으로 변경해 보세요!
SERIAL_PORT = "/dev/ttyAMA3" 
BAUD_RATE = 9600  # GPS 모듈의 기본 통신 속도

try:
    # 시리얼 포트 열기
    ser = serial.Serial(SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)
    print(f"[{SERIAL_PORT}] 포트를 성공적으로 열었습니다.")
    print("UART3를 통해 들어오는 GPS RAW 데이터를 출력합니다... (종료: Ctrl+C)")
    print("------------------------------------------------------------------")
    
    while True:
        # 버퍼에 읽을 데이터가 있는지 확인
        if ser.in_waiting > 0:
            # 한 줄 단위로 읽어와서 문자열로 디코딩 (깨지는 문자는 무시)
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            # 빈 줄이 아니라면 그대로 프린트
            if line:
                print(line)
                
        # CPU 과부하 방지를 위한 미세한 대기
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n사용자에 의해 테스트가 종료되었습니다.")
except Exception as e:
    print(f"\n오류 발생: {e}")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
        print("시리얼 포트가 안전하게 닫혔습니다.")