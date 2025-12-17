"""Gesture detection from hand landmarks."""


class GestureDetector:
    """Detects hand gestures from MediaPipe landmarks."""

    # Landmark indices
    INDEX_TIP, INDEX_PIP = 8, 6
    MIDDLE_TIP, MIDDLE_PIP = 12, 10
    RING_TIP, RING_PIP = 16, 14
    PINKY_TIP, PINKY_PIP = 20, 18

    def is_fist(self, landmarks: list) -> bool:
        """Check if all fingers are curled (fist)."""
        if not landmarks or len(landmarks) < 21:
            return False
        # Finger curled = tip below PIP joint (higher y value)
        return all(
            landmarks[tip][1] > landmarks[pip][1]
            for tip, pip in [
                (self.INDEX_TIP, self.INDEX_PIP),
                (self.MIDDLE_TIP, self.MIDDLE_PIP),
                (self.RING_TIP, self.RING_PIP),
                (self.PINKY_TIP, self.PINKY_PIP),
            ]
        )

    def is_open_palm(self, landmarks: list) -> bool:
        """Check if all fingers are extended (open palm)."""
        if not landmarks or len(landmarks) < 21:
            return False
        # Finger extended = tip above PIP joint (lower y value)
        return all(
            landmarks[tip][1] < landmarks[pip][1]
            for tip, pip in [
                (self.INDEX_TIP, self.INDEX_PIP),
                (self.MIDDLE_TIP, self.MIDDLE_PIP),
                (self.RING_TIP, self.RING_PIP),
                (self.PINKY_TIP, self.PINKY_PIP),
            ]
        )

    def detect_gesture(self, landmarks: list) -> str:
        """Detect gesture: 'fist', 'open', or 'none'."""
        if not landmarks:
            return "none"
        if self.is_fist(landmarks):
            return "fist"
        if self.is_open_palm(landmarks):
            return "open"
        return "none"
