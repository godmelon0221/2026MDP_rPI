import asyncio
import websockets
from picamera2 import Picamera2
from PIL import Image
import io
import time

SERVER_URI = "ws://192.168.40.216:8765"

picam2 = Picamera2()
picam2.start()
time.sleep(2)

running = False

async def run():
    global running

    async with websockets.connect(
        SERVER_URI,
        ping_interval=None
    ) as websocket:

        print("서버 연결됨")

        async def send_frames():
            global running
            while True:
                if running:
                    frame = picam2.capture_array()

                    img = Image.fromarray(frame)
                    img = img.convert("RGB")

                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=50)

                    await websocket.send(buf.getvalue())

                await asyncio.sleep(0.03)  # 약 30fps

        send_task = asyncio.create_task(send_frames())

        while True:
            msg = await websocket.recv()
            print("명령:", msg)

            if msg == "start":
                running = True

            elif msg == "stop":
                running = False

asyncio.run(run())