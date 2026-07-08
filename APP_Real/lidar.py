import serial
import math


class LidarReader:
    def __init__(self, port='/dev/ttyAMA4', baudrate=128000):
        self.port = port
        self.baudrate = baudrate
        self.ser = None

        # 한 바퀴 스캔을 모으기 위한 내부 버퍼
        self._scan_buffer = []
        self._last_angle = None

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            print(f"📡 라이다 연결 성공! (Port: {self.port})")
            return True
        except Exception as e:
            print(f"❌ 라이다 연결 실패: {e}")
            return False

    def _read_one_raw_packet(self):
        """
        시리얼에서 패킷 하나(보통 몇 도 구간)를 읽어서
        {"fsa_deg", "lsa_deg", "points": [...]} 형태로 반환.
        데이터 부족/헤더 못 찾음 등은 None 반환.
        """
        if self.ser is None or not self.ser.is_open:
            return None

        waiting = self.ser.in_waiting
        if waiting < 10:
            return None

        try:
            found = False
            for _ in range(100):
                if self.ser.in_waiting < 2:
                    return None
                b1 = self.ser.read(1)
                if b1 == b'\xAA':
                    b2 = self.ser.read(1)
                    if b2 == b'\x55':
                        found = True
                        break

            if not found:
                return None

            if self.ser.in_waiting < 8:
                return None

            header = self.ser.read(8)
            if len(header) < 8:
                return None

            lsn = header[1]
            fsa = (header[3] << 8 | header[2]) >> 1
            lsa = (header[5] << 8 | header[4]) >> 1

            if self.ser.in_waiting < lsn * 2:
                return None

            raw = self.ser.read(lsn * 2)
            if len(raw) < lsn * 2:
                return None

            fsa_deg = fsa / 64.0
            lsa_deg = lsa / 64.0
            if lsa_deg < fsa_deg:
                lsa_deg += 360.0
            angle_step = (lsa_deg - fsa_deg) / max(lsn - 1, 1)

            points = []
            for i in range(lsn):
                dist_raw = raw[i * 2] | (raw[i * 2 + 1] << 8)
                distance = dist_raw / 4.0
                angle = (fsa_deg + angle_step * i) % 360.0
                x = round(distance * math.cos(math.radians(angle)), 2)
                y = round(distance * math.sin(math.radians(angle)), 2)
                points.append({
                    "angle": round(angle, 1),
                    "distance": round(distance, 1),
                    "x": x,
                    "y": y
                })

            return {
                "fsa_deg": fsa_deg % 360.0,
                "points": points
            }

        except Exception as e:
            print(f"❌ 라이다 파싱 오류: {e}")
            return None

    def read_packet(self):
        """
        내부적으로 여러 번 호출되면서 패킷을 계속 누적하다가,
        한 바퀴(360도)가 완성되는 시점에만 전체 스캔을 반환함.
        완성되기 전이면 None을 반환하니, main.py의 while 루프에서
        계속 호출해주면 됨 (기존 구조 그대로 사용 가능).
        """
        raw_packet = self._read_one_raw_packet()
        if raw_packet is None:
            return None

        current_start_angle = raw_packet["fsa_deg"]

        # 한 바퀴 완성 감지: 새 패킷의 시작각이 이전 패킷보다 "뒤로" 넘어갔으면
        # (예: 350도 -> 5도) 한 바퀴 다 돈 것으로 판단
        wrapped = (
            self._last_angle is not None
            and current_start_angle < self._last_angle - 180  # 큰 폭으로 감소 = wrap
        )

        if wrapped and len(self._scan_buffer) > 0:
            # 한 바퀴 완성된 스캔을 반환
            full_scan = self._scan_buffer
            print(f"📡 [Full Scan] 360도 완성! 총 {len(full_scan)}개 포인트")

            # 새 바퀴 시작을 위해 버퍼 초기화 (지금 들어온 패킷부터 새로 시작)
            self._scan_buffer = list(raw_packet["points"])
            self._last_angle = current_start_angle

            return {"type": "lidar", "points": full_scan}

        # 아직 한 바퀴 안 끝났으면 버퍼에 누적만 하고 None 반환
        self._scan_buffer.extend(raw_packet["points"])
        self._last_angle = current_start_angle
        return None

    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("📡 라이다 포트 닫힘")