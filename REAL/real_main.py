import asyncio
import websockets
import serial
import cam
from micropyGPS import MicropyGPS

# 1. 하드웨어 설정
# [STM32] 조종용 UART (기본 UART0)
try:
    ser_stm32 = serial.Serial('/dev/serial0', 9600, timeout=1)
    print("🤖 STM32 UART 연결 성공")
except Exception as e:
    print(f"⚠️ STM32 연결 실패: {e}")
    ser_stm32 = None

# [GPS] UART 4 포트 설정 (Pin 40:RX, Pin 18:TX)
try:
    ser_gps = serial.Serial('/dev/ttyAMA4', 9600, timeout=0.1)
    my_gps = MicropyGPS() # GPS 파싱 객체 생성
    print("🛰️ GPS UART 4 연결 성공")
except Exception as e:
    print(f"⚠️ GPS 연결 실패: {e}")
    ser_gps = None

SERVER_URL = "ws://192.168.40.216:8080"

async def raspberry_client():
    try:
        async with websockets.connect(SERVER_URL) as websocket:
            await websocket.send("ID:RASPBERRY")
            print("✅ 서버 연결 완료: 관제 시작")

            while True:
                try:
                    # 1. 서버로부터 제어 명령 수신 (0.01초만 대기)
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.01)
                    
                    if isinstance(message, str) and message.startswith("CMD:"):
                        cmd_char = message.split(":")[1]
                        if ser_stm32:
                            ser_stm32.write(cmd_char.encode())
                            print(f"🚀 STM32 명령 전송: {cmd_char}")
                
                except asyncio.TimeoutError:
                    # 2. 명령이 없을 때 센서 데이터 송신 루프
                    
                    # 📸 카메라 데이터 전송 (이미지 바이너리)
                    frame_data = cam.camera_send(quality_mode=0)
                    if frame_data:
                        await websocket.send(frame_data)
                    
                    # 🛰️ GPS 데이터 읽기 및 파싱
                    if ser_gps and ser_gps.in_waiting > 0:
                        try:
                            # GPS 데이터 읽기
                            line = ser_gps.readline().decode('utf-8', errors='ignore')
                            
                            # 한 글자씩 파서에 입력
                            for char in line:
                                my_gps.update(char)
                            
                            # 신호(Fix)가 잡혔을 때 파싱된 데이터 전송
                            # clean_sentences가 0보다 크면 최소한 하나 이상의 문장을 읽었다는 뜻
                            if my_gps.clean_sentences > 0:
                                # 도(Decimal Degrees) 단위로 변환
                                lat = my_gps.latitude[0] + (my_gps.latitude[1] / 60)
                                if my_gps.latitude[2] == 'S': lat = -lat
                                
                                lon = my_gps.longitude[0] + (my_gps.longitude[1] / 60)
                                if my_gps.longitude[2] == 'W': lon = -lon
                                
                                gps_text = f"GPS:{lat:.6f},{lon:.6f},ALT:{my_gps.altitude},SPD:{my_gps.speed[2]}"
                                await websocket.send(gps_text)
                                print(f"📡 GPS 송신: {gps_text}")
                            
                            else:
                                # 신호가 아직 안 잡혔다면 생데이터라도 확인용으로 송신
                                if line.startswith('$'):
                                    await websocket.send(f"GPS:WAITING_FIX:{line.strip()}")
                                    
                        except Exception as e:
                            print(f"GPS 파싱 오류: {e}")

    except Exception as e:
        print(f"❌ 접속 끊김 또는 오류: {e}")
        await asyncio.sleep(5) # 5초 후 재시도

if __name__ == "__main__":
    asyncio.run(raspberry_client())