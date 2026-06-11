import asyncio
import sys
import json
import websockets
import serial

# 독립 모듈 로드
from camera import CameraStreamer
from lidar import LidarReader
# 네오픽셀 제어용 인스턴스 로드
from led import led_controller 

# 노트북 중계 서버 주소 세팅
notebook_ip = "192.168.40.216" 
uri = f"ws://{notebook_ip}:8765"

# =====================================================
# 송신할 16진수(Hex) 바이트 데이터 정의
# =====================================================
HEX_BRAKE    = b'\x00'  # 스페이스바 및 STOP(키 떨어짐) 대응
HEX_FORWARD  = b'\x01'  # W 키 대응
HEX_BACKWARD = b'\x04'  # S 키 대응
HEX_LEFT     = b'\x02'  # A 키 대응
HEX_RIGHT    = b'\x03'  # D 키 대응
HEX_MODE_CHG = b'\x05'  # 자율주행 모드 변경 신호

# UART 3 포트 오픈 (/dev/ttyAMA3)
try:
    ser_ama3 = serial.Serial('/dev/ttyAMA3', baudrate=9600, timeout=0)
    print("🟢 UART 3 (/dev/ttyAMA3) 포트 정상 로드 완료!")
except Exception as e:
    print(f"❌ UART 3 포트를 열 수 없습니다: {e}")
    ser_ama3 = None

async def main_stream_loop():
    camera = CameraStreamer(width=640, height=480, quality=50)
    lidar = LidarReader(port='/dev/ttyS0', baudrate=115200)
    
    has_camera = False
    has_lidar = False

    print("🚀 메인 프로세스 가동 시작")

    while True:
        try:
            print(f"🔗 {uri} 중계 서버로 연결을 시도하는 중...")
            
            if not has_camera:
                has_camera = camera.start()
            if not has_lidar:
                has_lidar = lidar.connect()

            async with websockets.connect(uri) as websocket:
                print("🟢 중계 서버 연결 성공!")
                last_camera_time = 0
                
                while True:
                    current_time = asyncio.get_event_loop().time()
                    
                    # -------------------------------------------------------------
                    # [1] 중계 서버로부터 플러터 조종 명령 수신
                    # -------------------------------------------------------------
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=0.001)
                        
                        if isinstance(message, str):
                            cmd_value = None
                            try:
                                json_data = json.loads(message)
                                if isinstance(json_data, dict) and "command" in json_data:
                                    cmd_value = json_data["command"]
                            except json.JSONDecodeError:
                                cmd_value = message

                            if cmd_value and ser_ama3 and ser_ama3.is_open:
                                # LED 제어
                                if cmd_value == "LED_ON":
                                    await asyncio.to_thread(led_controller.led_on)
                                elif cmd_value == "LED_OFF":
                                    await asyncio.to_thread(led_controller.led_off)
                                
                                # 자율주행 모드 변경 처리
                                elif cmd_value in ["AUTO_ON", "AUTO_OFF"]:
                                    print(f"🤖 모드 변경: {cmd_value}")
                                    ser_ama3.write(HEX_MODE_CHG)
                                    await asyncio.sleep(0.05)
                                    ser_ama3.write(HEX_BRAKE)
                                
                                # STOP 신호 및 키 뗌 처리 (0.01초 딜레이 후 브레이크 송신)
                                elif cmd_value == "STOP":
                                    await asyncio.sleep(0.01) 
                                    ser_ama3.write(HEX_BRAKE)
                                    print("🛑 [UART3] STOP: 브레이크(0x00) 송신 완료")
                                
                                # 주행 명령 처리
                                else:
                                    packet_map = {
                                        "BRAKE": HEX_BRAKE,
                                        "FORWARD": HEX_FORWARD,
                                        "BACKWARD": HEX_BACKWARD, 
                                        "LEFT": HEX_LEFT, 
                                        "RIGHT": HEX_RIGHT
                                    }
                                    packet = packet_map.get(cmd_value, cmd_value.encode())
                                    ser_ama3.write(packet)
                                    print(f"📡 [UART3] {cmd_value} 송신 완료")

                    except asyncio.TimeoutError:
                        pass
                    
                    # -------------------------------------------------------------
                    # [2] 센서 데이터 송신 및 영상 스트리밍
                    # -------------------------------------------------------------
                    if ser_ama3 and ser_ama3.is_open and ser_ama3.in_waiting >= 4:
                        rx_data = ser_ama3.read(4)
                        if len(rx_data) == 4:
                            await websocket.send(json.dumps({
                                "temperature": rx_data[0], "humidity": rx_data[1],
                                "cds": rx_data[2], "gas": rx_data[3]
                            }))
                    
                    if has_lidar:
                        lidar_data = lidar.read_packet()
                        if lidar_data: await websocket.send(json.dumps(lidar_data))
                    
                    if has_camera and (current_time - last_camera_time >= 0.033):
                        frame = camera.get_frame()
                        if frame: await websocket.send(frame)
                        last_camera_time = current_time
                    
                    await asyncio.sleep(0.001)

        except Exception as e:
            print(f"⚠️ 연결 오류 발생: {e}")
            if ser_ama3 and ser_ama3.is_open: ser_ama3.write(HEX_BRAKE)
            await asyncio.sleep(3)

if __name__ == "__main__":
    try:
        asyncio.run(main_stream_loop())
    except KeyboardInterrupt:
        if ser_ama3 and ser_ama3.is_open: ser_ama3.close()
        sys.exit(0)