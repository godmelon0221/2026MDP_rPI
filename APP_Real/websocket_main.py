import asyncio
import sys
import json
import websockets
import serial
import time

from camera import CameraStreamer
from led import led_controller 

# 서버 주소 및 포트
notebook_ip = "192.168.40.216" 
uri = f"ws://{notebook_ip}:8765"

# 제어 패킷 정의
HEX_BRAKE    = b'\x00'
HEX_FORWARD  = b'\x01'
HEX_BACKWARD = b'\x04'
HEX_LEFT     = b'\x02'
HEX_RIGHT    = b'\x03'
HEX_MODE_CHG = b'\x05'

# 웹소켓 binary 메시지 구분용 태그 (카메라/라이다 raw byte 구분)
TAG_LIDAR  = b'\x01'
TAG_CAMERA = b'\x02'

is_auto_mode = False         
is_led_on = False            

# UART 포트 초기화 (모터/센서 제어용)
try:
    ser_ama3 = serial.Serial('/dev/ttyAMA3', baudrate=9600, timeout=0)
    print("🟢 UART 3 포트 정상 로드 완료!")
except Exception as e:
    print(f"❌ UART 3 포트 오류: {e}")
    ser_ama3 = None

# UART 포트 초기화 (라이다 raw 데이터용)
try:
    ser_lidar = serial.Serial('/dev/ttyAMA4', baudrate=128000, timeout=0)
    print("📡 라이다 UART 포트 정상 로드 완료!")
except Exception as e:
    print(f"❌ 라이다 UART 포트 오류: {e}")
    ser_lidar = None

async def main_stream_loop():
    global is_auto_mode, is_led_on
    camera = CameraStreamer(width=640, height=480, quality=50)
    
    has_camera = camera.start()

    print("🚀 메인 프로세스 가동 시작")

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("🟢 중계 서버 연결 성공!")
                
                await websocket.send(json.dumps({
                    "type": "STATUS_SYNC", 
                    "is_auto": is_auto_mode,
                    "is_led": is_led_on
                }))
                
                last_camera_time = 0
                last_lidar_print_time = 0  # 라이다 로그 스로틀링용
                
                while True:
                    current_time = asyncio.get_event_loop().time()
                    
                    # [1] 조종 명령 수신 및 처리
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=0.01)
                        cmd_value = None
                        try:
                            json_data = json.loads(message)
                            cmd_value = json_data.get("command")
                        except:
                            cmd_value = message

                        if cmd_value:
                            if cmd_value in ["AUTO_ON", "AUTO_OFF"]:
                                is_auto_mode = (cmd_value == "AUTO_ON")
                                if ser_ama3 and ser_ama3.is_open:
                                    ser_ama3.write(HEX_MODE_CHG)
                                    await asyncio.sleep(0.01)
                                    ser_ama3.write(HEX_BRAKE)
                                    print(f"🤖 모드 변경: {cmd_value}")
                                
                                await websocket.send(json.dumps({
                                    "type": "STATUS_SYNC", "is_auto": is_auto_mode, "is_led": is_led_on
                                }))
                            
                            elif cmd_value in ["LED_ON", "LED_OFF"]:
                                if not is_auto_mode:
                                    is_led_on = (cmd_value == "LED_ON")
                                    led_controller.led_on() if is_led_on else led_controller.led_off()
                                    await websocket.send(json.dumps({
                                        "type": "STATUS_SYNC", "is_auto": is_auto_mode, "is_led": is_led_on
                                    }))

                            elif cmd_value == "STOP" and ser_ama3 and ser_ama3.is_open:
                                ser_ama3.write(HEX_BRAKE)
                            
                            else:
                                packet_map = {"BRAKE": HEX_BRAKE, "FORWARD": HEX_FORWARD, "BACKWARD": HEX_BACKWARD, "LEFT": HEX_LEFT, "RIGHT": HEX_RIGHT}
                                if cmd_value in packet_map and ser_ama3 and ser_ama3.is_open and not is_auto_mode:
                                    ser_ama3.write(packet_map[cmd_value])

                    except asyncio.TimeoutError:
                        pass
                    
                    # [2] 센서 데이터 수신 및 자율주행 LED 로직
                    if ser_ama3 and ser_ama3.is_open and ser_ama3.in_waiting >= 4:
                        rx_data = ser_ama3.read(4)
                        cds_value = rx_data[2]
                        
                        if is_auto_mode:
                            if cds_value < 50 and not is_led_on:
                                is_led_on = True
                                led_controller.led_on()
                            elif cds_value >= 50 and is_led_on:
                                is_led_on = False
                                led_controller.led_off()
                        
                        await websocket.send(json.dumps({"temperature": rx_data[0], "humidity": rx_data[1], "cds": cds_value, "gas": rx_data[3]}))
                    
                    # [3] 라이다 raw 데이터 그대로 송신 (파싱 없음, 앞에 태그 붙임)
                    if ser_lidar and ser_lidar.is_open and ser_lidar.in_waiting > 0:
                        raw_bytes = ser_lidar.read(ser_lidar.in_waiting)
                        
                        # 로그는 5초에 한 번만 출력 (초당 300줄 방지)
                        if current_time - last_lidar_print_time >= 5:
                            print(time.strftime('%Y.%m.%d - %H:%M:%S'), f"- lidar {len(raw_bytes)} bytes")
                            last_lidar_print_time = current_time
                        
                        await websocket.send(TAG_LIDAR + raw_bytes)  # 0x01 + raw data
                    
                    # [4] 카메라 프레임 송신 (앞에 태그 붙임)
                    if has_camera and (current_time - last_camera_time >= 0.033):
                        frame = camera.get_frame()
                        if frame: 
                            await websocket.send(TAG_CAMERA + frame)  # 0x02 + jpeg data
                        last_camera_time = current_time
                    
                    await asyncio.sleep(0.001)

        except Exception as e:
            print(f"⚠️ 연결 오류 발생: {e}")
            await asyncio.sleep(3)

if __name__ == "__main__":
    try: 
        asyncio.run(main_stream_loop())
    except KeyboardInterrupt:
        if ser_ama3 and ser_ama3.is_open: 
            ser_ama3.close()
        if ser_lidar and ser_lidar.is_open:
            ser_lidar.close()
        sys.exit(0)
