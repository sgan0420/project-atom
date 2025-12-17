"""Hand tracking module using MediaPipe."""

import mediapipe as mp
import cv2


class HandTracker:
    """Hand tracking using MediaPipe."""

    CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),      # Thumb
        (0, 5), (5, 6), (6, 7), (7, 8),      # Index
        (0, 9), (9, 10), (10, 11), (11, 12), # Middle
        (0, 13), (13, 14), (14, 15), (15, 16), # Ring
        (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
        (5, 9), (9, 13), (13, 17),           # Palm
    ]

    COLORS = {
        "Left": {"line": (0, 255, 0), "joint": (0, 200, 0), "tip": (0, 255, 255)},
        "Right": {"line": (255, 0, 0), "joint": (200, 0, 0), "tip": (255, 0, 255)},
    }

    def __init__(self, max_hands: int = 1, detection_confidence: float = 0.7):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=0.5,
        )

    def process_frame(self, frame):
        return self.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def get_landmarks(self, results):
        if not results.multi_hand_landmarks:
            return []
        return [[(lm.x, lm.y, lm.z) for lm in hand.landmark]
                for hand in results.multi_hand_landmarks]

    def get_handedness(self, results):
        if not results.multi_handedness:
            return []
        return [h.classification[0].label for h in results.multi_handedness]

    def close(self):
        self.hands.close()

    def draw_landmarks(self, frame, results):
        if not results.multi_hand_landmarks:
            return frame

        h, w = frame.shape[:2]
        handedness = self.get_handedness(results)

        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            label = handedness[idx] if idx < len(handedness) else "Right"
            colors = self.COLORS.get(label, self.COLORS["Right"])

            points = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]

            for start, end in self.CONNECTIONS:
                cv2.line(frame, points[start], points[end], colors["line"], 2)

            for i, point in enumerate(points):
                is_tip = i in [4, 8, 12, 16, 20]
                cv2.circle(frame, point, 8 if is_tip else 5,
                          colors["tip"] if is_tip else colors["joint"], -1)

            cv2.putText(frame, label, (points[0][0] - 30, points[0][1] + 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, colors["line"], 2)

        return frame
