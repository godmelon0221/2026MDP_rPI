import io
from picamera2 import Picamera2

class CameraStreamer:
    def __init__(self, width=640, height=480, quality=50):
        self.width = width
        self.height = height
        self.quality = quality  # JPEG 압축 품질 (1~100)
        self.picam = None
        self.image_buffer = io.BytesIO()

    def start(self):
        """📸 카메라 장치 활성화 및 해상도/품질 설정"""
        try:
            self.picam = Picamera2()
            
            # 1. 기본 미리보기 및 메인 스트림 구성 생성
            config = self.picam.create_preview_configuration(main={"size": (self.width, self.height)})
            
            # 💡 [핵심 수정]: capture_file이 아니라 여기에 인코더 옵션으로 quality를 먹여야 합니다.
            config["encoder"] = {"quality": self.quality}
            
            # 2. 변경된 설정을 카메라에 적용 후 가동
            self.picam.configure(config)
            self.picam.start()
            
            print(f"📹 Picamera2 가동 성공 (해상도: {self.width}x{self.height}, Quality: {self.quality})")
            return True
        except Exception as e:
            print(f"❌ 카메라를 열 수 없습니다: {e}")
            return False

    def get_frame(self):
        """🖼️ 현재 카메라 프레임을 JPEG 바이트 데이터로 추출"""
        if self.picam is None:
            return None
        try:
            self.image_buffer.seek(0)
            self.image_buffer.truncate()
            
            # 💡 [핵심 수정]: 'quality' 아규먼트를 완전히 제거했습니다. 
            # 설정(configure) 단계에서 이미 세팅되었으므로 포맷만 지정하면 됩니다.
            self.picam.capture_file(self.image_buffer, format="jpeg")
            return self.image_buffer.getvalue()
        except Exception as e:
            print(f"⚠️ 프레임 캡처 오류: {e}")
            return None

    def stop(self):
        """🧹 카메라 리소스 안전하게 해제"""
        if self.picam:
            try:
                self.picam.stop()
                self.picam.close()
                print("📹 카메라 리소스가 반환되었습니다.")
            except Exception as e:
                print(f"⚠️ 카메라 해제 오류: {e}")