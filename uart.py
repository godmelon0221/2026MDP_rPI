"""
라이다 방향 캘리브레이션(보정) 코드 - 실제 데이터 구조 반영판

실제 수신 데이터 형식:
{
    "type": "lidar",
    "points": [
        {"angle": 346.0, "distance": 1239.0, "x": 1202.03, "y": -300.4},
        ...
    ]
}
- angle: 0~360도 (라이다 자체 기준 각도, 로봇 정면과 일치한다는 보장 없음)
- distance: mm 단위. 0.0이면 유효하지 않은(측정 실패) 값이므로 제외
- x, y: mm 단위 직교좌표 (이미 계산되어 있음)

목적: 어떤 angle 값이 로봇의 "진짜 정면"인지 확인
사용법:
1. 이 코드를 실행한다.
2. 로봇 정면 15cm 앞에 손이나 박스 같은 물체를 놓는다.
3. 콘솔에 계속 갱신되는 "가장 가까운 포인트 TOP 5"를 보고,
   거리(distance)가 150mm 근처로 나오는 포인트의 angle 값을 확인한다.
4. 물체를 왼쪽/오른쪽/뒤로도 옮겨가며 각각의 angle 값을 확인한다.
"""

import asyncio
import json
import websockets

WS_URI = "ws://192.168.40.216:8765"

PRINT_INTERVAL = 0.5  # 화면 갱신 주기(초)


def extract_valid_points(data):
    """data에서 유효한 라이다 포인트 목록을 추출. (distance=0인 무효값은 제외)"""
    if not isinstance(data, dict) or data.get("type") != "lidar":
        return None

    points = data.get("points")
    if not isinstance(points, list):
        return None

    return [
        p for p in points
        if isinstance(p, dict) and p.get("distance", 0) > 0
    ]


async def calibrate():
    async with websockets.connect(WS_URI) as websocket:
        print(f"✅ 중계 서버 연결 성공: {WS_URI}")
        print("👉 지금 로봇 정면 15cm 앞에 물체(손, 박스 등)를 놓아주세요.")
        print("👉 아래 '가장 가까운 포인트'의 angle 값을 확인하면 됩니다.\n")

        buffer = []  # 최근 구간에서 모은 유효 포인트들
        last_print = 0

        async for message in websocket:
            if isinstance(message, (bytes, bytearray)):
                continue  # 카메라 프레임 무시

            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                continue

            points = extract_valid_points(data)
            if not points:
                continue  # 라이다 데이터가 아니거나 유효 포인트 없음

            buffer.extend(points)

            now = asyncio.get_event_loop().time()
            if now - last_print >= PRINT_INTERVAL and buffer:
                last_print = now

                closest = sorted(buffer, key=lambda p: p["distance"])[:5]

                print("─" * 55)
                print("📍 가장 가까운 포인트 TOP 5 (거리순)")
                for p in closest:
                    print(f"   거리={p['distance']:7.1f}mm  각도={p['angle']:6.1f}°   "
                          f"(x={p['x']:.1f}, y={p['y']:.1f})")

                buffer = []  # 다음 구간 위해 초기화


if __name__ == "__main__":
    try:
        asyncio.run(calibrate())
    except KeyboardInterrupt:
        print("\n1종료")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")