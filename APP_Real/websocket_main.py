import asyncio
import sys
import json
import websockets
import serial

from camera import CameraStreamer
from lidar import LidarReader
from led import led_controller 

notebook_ip = "192.168.40.216" 
uri = f"ws://{notebook_ip}:8765"

HEX_BRAKE    = b'\x00'
HEX_FORWARD  = b'\x01'
HEX_BACKWARD = b'\x04'
HEX_LEFT     = b'\x02'
HEX_RIGHT    = b'\x03'
HEX_MODE_CHG = b'\x05'

is_auto_mode = False       
is_led_on = False          

try:
    ser_ama3 = serial.Serial('/dev/ttyAMA3', baudrate=9600, timeout=0)
    print("🟢 UART 3 포트 정상 로드 완료!")
except Exception as e:
    print(f"❌ UART 3 포트 오류: {e}")
    ser_ama3 = None

async def main_stream_loop():
    global is_auto_mode, is_led_on
    camera = CameraStreamer(width=640, height=480, quality=50)
    lidar = LidarReader(port='/dev/ttyS0', baudrate=115200)
    
    has_camera = camera.start()
    has_lidar = lidar.connect()

    print("🚀 메인 프로세스 가동 시작")

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                print("🟢 중계 서버 연결 성공!")
                
                # [연결 직후] 현재의 모든 상태를 정확한 키값으로 전송
                await websocket.send(json.dumps({
                    "type": "STATUS_SYNC", 
                    "is_auto": is_auto_mode,
                    "is_led": is_led_on
                }))
                
                last_camera_time = 0
                
                while True:
                    current_time = asyncio.get_event_loop().time()
                    
                    # ----------------------------------------------------
                    # [1] 조종 명령 수신 및 처리
                    # ----------------------------------------------------
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=0.01)
                        cmd_value = None
                        try:
                            json_data = json.loads(message)
                            cmd_value = json_data.get("command")
                        except:
                            cmd_value = message

                        if cmd_value:
                            # 1) 자율주행 모드 스위치 처리
                            if cmd_value in ["AUTO_ON", "AUTO_OFF"]:
                                is_auto_mode = (cmd_value == "AUTO_ON")
                                if ser_ama3 and ser_ama3.is_open:
                                    # 💡 [보완] 모드 변경 패킷(0x05) 전송 후 브레이크(0x00) 연속 전송 시퀀스 적용
                                    ser_ama3.write(HEX_MODE_CHG)
                                    await asyncio.sleep(0.01)
                                    ser_ama3.write(HEX_BRAKE)
                                    print(f"🤖 모드 변경 수신: {cmd_value} (is_auto_mode={is_auto_mode}) -> 0x05 전송 후 안전 브레이크 0x00 완료")
                                else:
                                    print(f"🤖 모드 변경 수신: {cmd_value} (UART 포트가 닫혀있어 명령 무시)")
                                
                                await websocket.send(json.dumps({
                                    "type": "STATUS_SYNC", 
                                    "is_auto": is_auto_mode, 
                                    "is_led": is_led_on
                                }))
                            
                            # 2) 수동 LED 스위치 처리 (자율주행 모드가 꺼져있을 때만 동작)
                            elif cmd_value in ["LED_ON", "LED_OFF"]:
                                if not is_auto_mode:
                                    is_led_on = (cmd_value == "LED_ON")
                                    if is_led_on:
                                        led_controller.led_on()
                                    else:
                                        led_controller.led_off()
                                        
                                    print(f"💡 수동 LED 변경 수신: {cmd_value} (is_led_on={is_led_on})")
                                    
                                    await websocket.send(json.dumps({
                                        "type": "STATUS_SYNC", 
                                        "is_auto": is_auto_mode, 
                                        "is_led": is_led_on
                                    }))
                                else:
                                    print("⚠️ 자율주행 모드 작동 중이므로 수동 LED 명령을 무시합니다. (자동 제어 작동 중)")

                            elif cmd_value == "STOP":
                                if ser_ama3 and ser_ama3.is_open:
                                    await asyncio.sleep(0.01)
                                    ser_ama3.write(HEX_BRAKE)
                            else:
                                packet_map = {"BRAKE": HEX_BRAKE, "FORWARD": HEX_FORWARD, "BACKWARD": HEX_BACKWARD, "LEFT": HEX_LEFT, "RIGHT": HEX_RIGHT}
                                if cmd_value in packet_map and ser_ama3 and ser_ama3.is_open:
                                    if not is_auto_mode:
                                        ser_ama3.write(packet_map[cmd_value])

                    except asyncio.TimeoutError:
                        pass
                    
                    # ----------------------------------------------------
                    # [2] 센서 데이터 수신 및 자율주행 자동 LED 로직 연동
                    # ----------------------------------------------------
                    if ser_ama3 and ser_ama3.is_open and ser_ama3.in_waiting >= 4:
                        rx_data = ser_ama3.read(4)
                        
                        temperature = rx_data[0]
                        humidity = rx_data[1]
                        cds_value = rx_data[2]  # 조도 센서값 추출
                        gas = rx_data[3]
                        
                        # 💡 자율주행 모드 상태일 때, 조도 센서값에 기반한 자동 밤길 조명 제어
                        if is_auto_mode:
                            # 주변이 어두워졌을 때 (cds < 50) -> 자동 점등 (1회만 실행되게 차단막 설치)
                            if cds_value < 50 and not is_led_on:
                                is_led_on = True
                                led_controller.led_on()
                                print(f"🌙 [자동 조등] 자율주행 중 어두워짐 감지 (CDS: {cds_value}) -> LED ON")
                                
                                await websocket.send(json.dumps({
                                    "type": "STATUS_SYNC", 
                                    "is_auto": is_auto_mode, 
                                    "is_led": is_led_on
                                }))
                            
                            # 주변이 다시 밝아졌을 때 (cds >= 50) -> 자동 소등 (1회만 실행되게 차단막 설치)
                            elif cds_value >= 50 and is_led_on:
                                is_led_on = False
                                led_controller.led_off()
                                print(f"☀️ [자동 소등] 자율주행 중 밝아짐 감지 (CDS: {cds_value}) -> LED OFF")
                                
                                await websocket.send(json.dumps({
                                    "type": "STATUS_SYNC", 
                                    "is_auto": is_auto_mode, 
                                    "is_led": is_led_on
                                }))

                        data_pkt = json.dumps({"temperature": temperature, "humidity": humidity, "cds": cds_value, "gas": gas})
                        await websocket.send(data_pkt)
                    
                    # ----------------------------------------------------
                    # [3] 라이다 및 카메라 데이터 송신
                    # ----------------------------------------------------
                    if has_lidar:
                        lidar_data = json.dumps(lidar.read_packet())
                        if lidar_data: 
                            await websocket.send(lidar_data)
                    
                    if has_camera and (current_time - last_camera_time >= 0.033):
                        frame = camera.get_frame()
                        if frame: 
                            await websocket.send(frame)
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
        sys.exit(0)