# led.py
import board
import neopixel

# 🛠️ 연결 사양 완벽 매칭
LED_COUNT = 20        # 실제 LED 개수
LED_PIN = board.D18   # GPIO 18번 핀 사용
BRIGHTNESS = 0.2      # 밝기 제한 (전류 안전망)

class RGBStripController:
    def __init__(self):
        try:
            # 작동 검증 완료된 neopixel 객체 사용
            self.pixels = neopixel.NeoPixel(
                LED_PIN, 
                LED_COUNT, 
                brightness=BRIGHTNESS, 
                auto_write=False, 
                pixel_order=neopixel.GRB
            )
            print("✅ [neopixel] RGB 스트립 라이브러리 연동 성공")
        except Exception as e:
            print(f"❌ RGB 스트립 연동 실패 (sudo 권한 누락 유무 확인): {e}")

    def led_on(self):
        """흰색 켜기"""
        self.pixels.fill((255, 255, 255))
        self.pixels.show()
        print("💡 LED ON 점등 완료")

    def led_off(self):
        """전체 끄기"""
        self.pixels.fill((0, 0, 0))
        self.pixels.show()
        print("🔦 LED OFF 소등 완료")

# 인스턴스 단일 생성 (싱글톤)
led_controller = RGBStripController()