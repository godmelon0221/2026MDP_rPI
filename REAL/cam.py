import asyncio
import io
import websockets
from picamera2 import Picamera2
from PIL import Image

# ----------------------------------------------------
# 1. Picamera2 카메라 초기화 (기존 정상 작동 로직)
# ----------------------------------------------------
picam2 = None
try:
    picam2 = Picamera2()
    # 640x480 기본 해상도로 카메라 구동
    config = picam2.create_video_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    print("🚀 Picamera2 Module Started Successfully!")
except Exception as e:
    print(f"❌ Camera Init Error: {e}")

# ----------------------------------------------------
# 2. 이미지 캡처 및 전송용 바이트 변환 함수
# ----------------------------------------------------
def get_camera_frame(quality_mode=1):
    if picam2 is None:
        return None

    buf = io.BytesIO()
    try:
        # 기존 로직: 가장 빠른 방식으로 즉시 캡처
        picam2.capture_file(buf, format='jpeg')
        
        # [고화질 모드] 원본 640x480 그대로 전송
        if quality_mode == 1:
            return buf.getvalue()
        
        # [저화질 모드] 용량 다이어트 및 리사이징 (플러터 테스트/네트워크 버벅임 방지용)
        buf.seek(0)
        img = Image.open(buf)
        
        # NEAREST 필터로 빠르게 리사이징
        # (참고: 기존 코드의 1200x800은 오히려 크기가 커지므로, 원본보다 작은 320x240 등으로 낮추는 것이 다이어트에 좋습니다.)
        img = img.resize((320, 240), Image.Resampling.NEAREST)
        
        out_buf = io.BytesIO()
        img.save(out_buf, format='JPEG', quality=20) 
        return out_buf.getvalue()
        
    except Exception as e:
        print(f"⚠️ Capture Error: {e}")
        return None
    finally:
        buf.close()

# ----------------------------------------------------
# 3. 웹소켓 연결 및 스트리밍 처리 핸들러
# ----------------------------------------------------
async def video_stream(websocket):
    print(f"📱 플러터 앱 연결됨: {websocket.remote_address}")
    
    try:
        while True:
            # 카메라로부터 최신 프레임 바이트 데이터 가져오기
            # (네트워크 환경에 따라 고화질은 1, 전송이 밀리면 저화질 0으로 설정해 테스트해보세요)
            frame_bytes = get_camera_frame(quality_mode=1)
            
            if frame_bytes is not None:
                # 웹소켓을 통해 플러터 앱으로 바이너리 데이터 전송
                await websocket.send(frame_bytes)
            
            # 약 30 FPS 전송 제한 (라즈베리파이 CPU 과부하 방지)
            await asyncio.sleep(0.033)

    except websockets.exceptions.ConnectionClosed:
        print(f"❌ 플러터 앱 연결 종료: {websocket.remote_address}")
    except Exception as e:
        print(f"⚠️ 스트리밍 중 에러 발생: {e}")

# ----------------------------------------------------
# 4. 서버 시작 메인 함수
# ----------------------------------------------------
async def main():
    # 포트 8080으로 외부 모든 IP(0.0.0.0)의 접속을 허용합니다.
    async with websockets.serve(video_stream, "0.0.0.0", 8080):
        print("🛰️ 라즈베리파이 웹소켓 비디오 서버가 가동되었습니다.")
        print("📡 플러터 앱의 카메라 화면 진입을 기다리는 중...")
        await asyncio.get_running_loop().create_future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 서버가 사용자에 의해 종료되었습니다.")
    finally:
        if picam2 is not None:
            picam2.stop()
            print("📹 카메라 자원이 안전하게 해제되었습니다.")