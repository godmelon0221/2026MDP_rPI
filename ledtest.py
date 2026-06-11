import time
import board
import neopixel

# 💡 본인의 실제 LED 개수에 맞게 수정하세요! (예: 10개만 테스트하려면 10)
LED_COUNT = 20        
LED_PIN = board.D18   # GPIO 18번 사용
BRIGHTNESS = 0.2      # 눈부심 방지용 밝기 20% 제한 (0.0 ~ 1.0)

# 네오픽셀 스트립 초기화 (GRB 순서 표준 제품 기준)
pixels = neopixel.NeoPixel(
    LED_PIN, 
    LED_COUNT, 
    brightness=BRIGHTNESS, 
    auto_write=False, 
    pixel_order=neopixel.GRB
)

def color_wipe(color, wait):
    """LED를 하나씩 순서대로 지정한 색으로 채우는 함수"""
    for i in range(len(pixels)):
        pixels[i] = color
        pixels.show()
        time.sleep(wait)

if __name__ == "__main__":
    print("🚀 3선식 RGB 스트립 테스트 시작 (종료하려면 Ctrl + C)")
    try:
        while True:
            # 🔴 빨간색 쭈르륵 켜지기
            print("🔴 빨간색 켜는 중...")
            color_wipe((255, 0, 0), 0.05)
            time.sleep(1)
            
            # 🟢 초록색 쭈르륵 켜지기
            print("🟢 초록색 켜는 중...")
            color_wipe((0, 255, 0), 0.05)
            time.sleep(1)
            
            # 🔵 파랑색 쭈르륵 켜지기
            print("🔵 파란색 켜는 중...")
            color_wipe((0, 0, 255), 0.05)
            time.sleep(1)
            
            # ⚪ 전체 소등 후 잠시 대기
            print("⚫ 잠시 소등...")
            pixels.fill((0, 0, 0))
            pixels.show()
            time.sleep(1)
            
    except KeyboardInterrupt:
        # Ctrl + C로 종료 시 안전하게 불 끄기
        pixels.fill((0, 0, 0))
        pixels.show()
        print("\n👋 테스트를 종료하고 LED를 끕니다.")