import serial

# X4PRO의 기본 보드레이트는 128000입니다.
ser = serial.Serial('/dev/serial0', 128000, timeout=1)

try:
    while True:
        if ser.in_waiting > 0:
            data = ser.read(ser.in_waiting)
            print(data.hex()) # 바이너리 데이터가 출력되면 연결 성공
except KeyboardInterrupt:
    ser.close()