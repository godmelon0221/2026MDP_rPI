import serial
import time

# UART 4 설정 (핀 24:TX, 21:RX)
# /dev/ttyAMA1은 환경에 따라 ttyAMA2일 수 있으니 확인 후 수정하세요.
try:
    ser = serial.Serial('/dev/ttyAMA4', 9600, timeout=0.1)
except Exception as e:
    print(f"시리얼 포트 연결 실패: {e}")
    ser = None

def get_gps_data():
    """
    GPS 모듈로부터 NMEA 문장 한 줄을 읽어 반환합니다.
    데이터가 없거나 오류 발생 시 None을 반환합니다.
    """
    if ser is None or not ser.is_open:
        return None

    try:
        if ser.in_waiting > 0:
            # 한 줄을 읽고 디코딩 (오류 무시 설정)
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            # 유의미한 데이터(NMEA 문장)인 경우만 반환
            if line.startswith('$'):
                return line
        return None
    except Exception as e:
        print(f"데이터 읽기 오류: {e}")
        return None

# --- 사용 예시 ---
