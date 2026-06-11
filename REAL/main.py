# 메인 코드
import asyncio
import websockets

# 내가 만든 코드 (cam.py, lidar.py 파일이 같은 폴더에 있어야 함)
import cam
import lidar

SERVER_URI = "ws://192.168.40.216:8765"
cam_run = False  # 영상 전송 스위치

async def run():
    global cam_run
    
    # 1. 프로그램 시작 시 라이다 초기화 및 모터 구동
    if lidar.lidar.start():
        print("LiDAR 준비 완료!")
    else:
        print("LiDAR 연결 실패, 하지만 프로그램은 계속 실행합니다.")

    async with websockets.connect(
        SERVER_URI,
        ping_interval = None 
    ) as webscket: 
        
        print("서버 연결 성공")
        
        # [Task 1] 카메라 영상 전송 함수
        async def send_frames():
            global cam_run
            while True:
                if cam_run:
                    frame = cam.camera_send()
                    if frame:
                        await webscket.send(frame)
                
                await asyncio.sleep(0.03) # 약 30FPS

        # [Task 2] 라이다 데이터 전송 함수 (새로 추가)
        async def lidar_send_task():
            while True:
                # 라이다 원본 데이터(hex 문자열) 가져오기
                raw_data = lidar.lidar.get_raw_data()
                
                if raw_data:
                    # 노트북에서 영상 데이터와 구분할 수 있게 태그를 붙여서 전송
                    try:
                        await webscket.send(f"LIDAR:{raw_data}")
                    except Exception as e:
                        print(f"라이다 전송 오류: {e}")
                        break
                
                # 라이다 데이터 주기를 조절 (0.1초마다 전송)
                await asyncio.sleep(0.1)

        # 각 태스크를 백그라운드에서 실행하도록 예약
        send_task = asyncio.create_task(send_frames())
        lidar_task = asyncio.create_task(lidar_send_task())
        
        try:
            # 메인 루프: 서버로부터 명령(start/stop)을 기다립니다.
            while True:
                msg = await webscket.recv()
                print(f"받은 명령: {msg}")
                
                if msg == "start":
                    cam_run = True
                elif msg == "stop":
                    cam_run = False
        except Exception as e:
            print(f"서버 통신 중 에러: {e}")
        finally:
            # 종료 시 태스크 취소 및 리소스 정리
            send_task.cancel()
            lidar_task.cancel()
            lidar.lidar.stop() # 라이다 모터 정지 및 GPIO 정리
            print("프로그램을 종료합니다.")

# 프로그램 실행
if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass