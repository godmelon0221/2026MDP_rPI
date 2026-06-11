import asyncio
import websockets
from picamera2 import Picamera2
from PIL import Image
import io
import time

SERVER_URI = "ws://192.168.40.216:8765"  # ← 노트북 IP

# 카메라 초기화
picam2 = Picamera2()
picam2.start()
time.sleep(2)

async def run():
    try:
        async with websockets.connect(
            SERVER_URI,
            ping_interval=None   # 🔥 timeout 방지
        ) as websocket:

            print("서버 연결됨")

            while True:
                try:
                    msg = await websocket.recv()
                    print("명령 받음:", msg)

                    if msg == "capture":
                        frame = picam2.capture_array()

                        img = Image.fromarray(frame)
                        img = img.convert("RGB")  # 🔥 RGBA → RGB

                        buf = io.BytesIO()
                        img.save(buf, format='JPEG', quality=60)

                        await websocket.send(buf.getvalue())
                        print("이미지 전송 완료")

                except Exception as e:
                    print("캡처/수신 에러:", e)
                    break

    except Exception as e:
        print("연결 에러:", e)

asyncio.run(run())