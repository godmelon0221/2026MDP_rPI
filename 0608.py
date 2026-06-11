import asyncio
import sys
import json
import websockets
import serial

# 독립 모듈 로드
from camera import CameraStreamer
from lidar import LidarReader

# 노트북 중계 서버 주소 세팅
notebook_ip = "192.168.40.216" 
uri = f"ws://{notebook_ip}:8765"

# =====================================================
# 💡 [자유 수정 영역] 송신할 16진수(Hex) 바이트 데이터 정의
# =====================================================
HEX_BRAKE    = b'\x00'  # 💡 스페이스바 대응 0x00 추가
HEX_FORWARD  = b'\x01'
HEX_BACKWARD = b'\x02'
HEX_LEFT     = b'\x03'
HEX_RIGHT    = b'\x04'
# =====================================================

# UART 3 포트 오픈
try:
    ser_ama3 = serial.Serial('/dev/ttyAMA3', baudrate=9600, timeout=0.1)
    print("🟢 UART 3 (/dev/ttyAMA3) 포트 정상 로드 완료!")
except Exception as e:
    print(f"❌ UART 3 포트를 열 수 없습니다: {e}")
    ser_ama3 = None

async def main_stream_loop():
    print(f"{uri} 중계 서버로 연결을 시도하는 중...")
    
    camera = CameraStreamer(width=640, height=480, quality=50)
    lidar = LidarReader(port='/dev/ttyS0', baudrate=115200)
    
    has_camera = camera.start()
    has_lidar = lidar.connect()
    
    try:
        async with websockets.connect(uri) as websocket:
            print("🟢 중계 서버 연결 성공! 실시간 데이터 하이브리드 스트리밍 시작")
            
            last_camera_time = 0
            
            while True:
                current_time = asyncio.get_event_loop().time()
                
                # -------------------------------------------------------------
                # 📥 중계 서버로부터 플러터 조종 명령 수신 처리
                # -------------------------------------------------------------
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.001)
                    
                    if isinstance(message, str):
                        if message != "STOP":
                            print(f"⌨️ 키 눌림 감지! 서버 수신 데이터: {message}")
                            
                            if ser_ama3 and ser_ama3.is_open:
                                if message == "BRAKE":
                                    packet = HEX_BRAKE
                                    ser_ama3.write(packet)
                                    print(f"📡 [UART3 송신] BRAKE -> {packet.hex().upper()}")

                                elif message == "FORWARD":
                                    packet = HEX_FORWARD
                                    ser_ama3.write(packet)
                                    print(f"📡 [UART3 송신] FORWARD -> {packet.hex().upper()}")
                                    
                                elif message == "BACKWARD":
                                    packet = HEX_BACKWARD
                                    ser_ama3.write(packet)
                                    print(f"📡 [UART3 송신] BACKWARD -> {packet.hex().upper()}")
                                    
                                elif message == "LEFT":
                                    packet = HEX_LEFT
                                    ser_ama3.write(packet)
                                    print(f"📡 [UART3 송신] LEFT -> {packet.hex().upper()}")
                                    
                                elif message == "RIGHT":
                                    packet = HEX_RIGHT
                                    ser_ama3.write(packet)
                                    print(f"📡 [UART3 송신] RIGHT -> {packet.hex().upper()}")
                                    
                                else:
                                    ser_ama3.write(message.encode())
                        else:
                            print("🛑 키 떨어짐 (STOP) -> UART 전송을 스킵하거나 정지 명령 처리")
                            # 필요에 따라 정지 시 모터 보드에 브레이크 패킷(HEX_BRAKE)을 한 번 명시적으로 보낼 수도 있습니다.
                            
                except asyncio.TimeoutError:
                    pass
                
                # 📡 [1] 라이다 데이터 수집 및 송신
                if has_lidar:
                    lidar_data = lidar.read_packet()
                    if lidar_data is not None:
                        await websocket.send(json.dumps(lidar_data))
                
                # 📹 [2] 카메라 프레임 수집 및 송신
                if has_camera and (current_time - last_camera_time >= 0.033):
                    frame = camera.get_frame()
                    if frame is not None:
                        await websocket.send(frame)
                    last_camera_time = current_time
                
                await asyncio.sleep(0.001)
                
    except websockets.exceptions.ConnectionClosed:
        print("❌ 중계 서버와의 네트워크 연결이 차단되었습니다.")
    except Exception as e:
        print(f"⚠️ 스트리밍 프로세스 중 치명적 오류 발생: {e}")
    finally:
        camera.stop()
        lidar.disconnect()
        if ser_ama3 and ser_ama3.is_open:
            ser_ama3.close()
        print("🧹 모든 분할 모듈의 자원이 안전하게 회수되었습니다.")

if __name__ == "__main__":
    try:
        asyncio.run(main_stream_loop())
    except KeyboardInterrupt:
        print("\n👋 메인 컨트롤러 가동을 중단하고 종료합니다.")
        sys.exit(0)