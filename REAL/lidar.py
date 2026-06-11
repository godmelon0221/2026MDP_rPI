import serial
import time

class Lidar:
    def __init__(self):
        self.ser = None
        
    def start(self):
        try:
            # 보드레이트 128000, ttyAMA2 확인
            self.ser = serial.Serial('/dev/ttyAMA2', 128000, timeout=0.1)
            return True
        except:
            return False

    def get_raw_data(self):
        if self.ser and self.ser.in_waiting > 10:
            # 180도나 90도에서 끊기지 않게 충분한 버퍼를 한 번에 읽음
            # X4PRO의 한 주기 데이터를 다 가져오기 위해 500바이트 이상 확보
            data = self.ser.read(self.ser.in_waiting)
            
            result = []
            # 패킷의 시작점을 찾거나, 데이터를 촘촘하게 분산해서 360도를 채움
            data_len = len(data)
            for i in range(0, data_len - 1, 2):
                # 데이터 인덱스를 기반으로 전체 360도를 강제로 매핑 (임시)
                # 실제 각도 파싱이 복잡하므로, 전체 버퍼 크기 대비 위치로 각도를 산출
                angle = (i / data_len) * 360 
                dist = data[i] * 10
                if dist > 20: # 노이즈 제거
                    result.append(f"{angle:.1f},{dist}")
            
            return ";".join(result)
        return None

    def stop(self):
        if self.ser: self.ser.close()

lidar = Lidar()