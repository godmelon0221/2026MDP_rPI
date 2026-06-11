import serial
import math

class LidarReader:
    def __init__(self, port='/dev/ttyS0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

    def connect(self):
        """📡 라이다 시리얼 포트 연결"""
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=0.1)
            print(f"📡 라이다 센서 연결 성공! (Port: {self.port})")
            return True
        except Exception as e:
            print(f"❌ 라이다 포트를 열 수 없습니다: {e}")
            return False

    def read_packet(self):
        """📐 데이터를 읽어서 X, Y 좌표를 포함한 JSON 규격 딕셔너리로 파싱"""
        if self.ser is None or self.ser.in_waiting == 0:
            return None
            
        try:
            # 시리얼 버퍼에서 한 줄 수신
            line = self.ser.readline().decode('utf-8', errors='ignore').strip()
            
            # 💡 [필독] 실제 사용하는 라이다 데이터 프로토콜 규격에 맞춰 파싱하세요.
            # 아래 값들은 연결 확인용 가상 샘플 데이터(더미)입니다.
            angle, distance = 180, 1500 
            
            # 삼각함수 기준 2D 평면 좌표(X, Y) 계산
            x = distance * math.cos(math.radians(angle))
            y = distance * math.sin(math.radians(angle))

            return {
                "type": "lidar",
                "angle": angle,
                "distance": distance,
                "x": round(x, 2),
                "y": round(y, 2)
            }
        except Exception as e:
            # 깨진 패킷이나 통신 튀는 에러는 유연하게 흘려보냄
            return None

    def disconnect(self):
        """🧹 시리얼 포트 닫기"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("📡 라이다 시리얼 포트가 닫혔습니다.")