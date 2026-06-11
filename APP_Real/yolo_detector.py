import cv2
import numpy as np

class YOLO_Detector:
    def __init__(self, model_path=None, conf_threshold=0.5):
        self.conf_threshold = conf_threshold
        self.net = None

        if model_path:
            try:
                self.net = cv2.dnn.readNet(model_path)
                print("✅ YOLO 모델 로드 성공")
            except Exception as e:
                print(f"⚠️ YOLO 모델 로드 실패: {e}")
        else:
            print("⚠️ YOLO 모델 경로 없음 — 더미 모드로 실행")

    def detect(self, frame_np: np.ndarray) -> list:
        """
        frame_np: numpy BGR 배열
        return: [{"label": str, "confidence": float, "box": [x,y,w,h]}, ...]
        """
        if self.net is None or frame_np is None:
            return []  # 모델 없으면 빈 결과 반환

        try:
            blob = cv2.dnn.blobFromImage(frame_np, 1/255.0, (416, 416), swapRB=True, crop=False)
            self.net.setInput(blob)
            outputs = self.net.forward(self.net.getUnconnectedOutLayersNames())

            results = []
            for output in outputs:
                for detection in output:
                    scores = detection[5:]
                    class_id = int(np.argmax(scores))
                    confidence = float(scores[class_id])
                    if confidence >= self.conf_threshold:
                        cx, cy, w, h = detection[:4]
                        results.append({
                            "label":      str(class_id),
                            "confidence": round(confidence, 3),
                            "box":        [float(cx), float(cy), float(w), float(h)],
                        })
            return results

        except Exception as e:
            print(f"⚠️ YOLO 추론 오류: {e}")
            return []