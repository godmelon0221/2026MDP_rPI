import asyncio
import websockets
import time

# 노트북 서버의 IP 주소와 포트
SERVER_URL = "ws://192.168.40.216:8080"

async def raspberry_client():
    try:
        async with websockets.connect(SERVER_URL) as websocket:
            # 1. 연결 직후 노트북 서버에 식별 정보 전송
            await websocket.send("ID:RASPBERRY")
            print(f"✅ 서버({SERVER_URL})에 연결되었습니다.")

            # 2. 서버로부터 메시지 수신 및 데이터 전송 루프
            while True:
                # 서버에서 오는 명령 대기 (예: 고도에서 보낸 조종 명령)
                try:
                    # timeout을 주어 루프가 갇히지 않게 하고, 그 사이 센서값을 보낼 수 있습니다.
                    message = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    print(f"📩 서버 명령 수신: {message}")
                    
                    # 여기에 모터 제어 로직 등을 넣으세요
                    # if "FORWARD" in message:
                    #     drive_forward()

                except asyncio.TimeoutError:
                    # 명령이 없을 때는 센서 데이터를 서버로 보냄 (예: LiDAR 값)
                    # 테스트용 가짜 데이터 전송
                    sensor_data = f"DISTANCE: {time.time() % 10:.2f}m"
                    # await websocket.send(sensor_data) 
                    pass

    except Exception as e:
        print(f"❌ 연결 오류: {e}")

if __name__ == "__main__":
    print("🚀 라즈베리 파이 클라이언트 시작...")
    try:
        asyncio.run(raspberry_client())
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")