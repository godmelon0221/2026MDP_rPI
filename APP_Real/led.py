import board
import neopixel

# 🛠️ 연결 사양 완벽 매칭
LED_COUNT = 15       # 실제 LED 개수
LED_PIN = board.D18   # GPIO 18번 핀 사용 (PWM 0 채널)
BRIGHTNESS = 0.2      # 밝기 제한 (전류 안전망)

class RGBStripController:
    def __init__(self):
        self.pixels = None
        try:
            # 작동 검증 완료된 neopixel 객체 사용
            self.pixels = neopixel.NeoPixel(
                LED_PIN, 
                LED_COUNT, 
                brightness=BRIGHTNESS, 
                auto_write=False, 
                pixel_order=neopixel.GRB
            )
            # 💡 [보완] 켜질 때 초기 스냅샷으로 전체 소등 상태 한번 밀어주기
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            print("✅ [neopixel] RGB 스트립 라이브러리 연동 및 초기화 성공")
        except Exception as e:
            print(f"❌ RGB 스트립 연동 실패!! (반드시 sudo 권한으로 실행했는지 확인하세요): {e}")

    def led_on(self):
        """흰색 켜기"""
        if self.pixels is None:
            print("⚠️ [LED 에러] 네오픽셀 객체가 초기화되지 않아 켤 수 없습니다.")
            return
        try:
            self.pixels.fill((255, 255, 255))
            self.pixels.show()
            print("💡 LED ON 점등 완료")
        except Exception as e:
            print(f"❌ LED ON 제어 중 물리 오류: {e}")

    def led_off(self):
        """전체 끄기"""
        if self.pixels is None:
            print("⚠️ [LED 에러] 네오픽셀 객체가 초기화되지 않아 끌 수 없습니다.")
            return
        try:
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
            print("🔦 LED OFF 소등 완료")
        except Exception as e:
            print(f"❌ LED OFF 제어 중 물리 오류: {e}")

# 인스턴스 단일 생성 (싱글톤)
led_controller = RGBStripController()