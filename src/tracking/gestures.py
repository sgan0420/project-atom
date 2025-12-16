"""
Gesture detection module - analyzes hand landmarks to detect gestures.
"""


class GestureDetector:
    """Detects hand gestures from MediaPipe landmarks."""

    # MediaPipe hand landmark indices
    WRIST = 0
    THUMB_TIP = 4
    INDEX_TIP = 8
    MIDDLE_TIP = 12
    RING_TIP = 16
    PINKY_TIP = 20

    # Finger base joints (MCP - metacarpophalangeal)
    INDEX_MCP = 5
    MIDDLE_MCP = 9
    RING_MCP = 13
    PINKY_MCP = 17

    # Finger middle joints (PIP - proximal interphalangeal)
    INDEX_PIP = 6
    MIDDLE_PIP = 10
    RING_PIP = 14
    PINKY_PIP = 18

    def __init__(self):
        """Initialize gesture detector."""
        pass

    def is_fist(self, landmarks: list) -> bool:
        """
        Detect if hand is making a fist (all fingers curled).

        A fist is detected when all fingertips are below their corresponding
        PIP joints (fingers are curled inward).

        Args:
            landmarks: List of 21 (x, y, z) tuples from MediaPipe.

        Returns:
            True if fist detected, False otherwise.
        """
        if not landmarks or len(landmarks) < 21:
            return False

        # Check if each finger is curled (tip below PIP joint)
        # "Below" means higher y value (screen coordinates: y increases downward)

        # Index finger curled
        index_curled = landmarks[self.INDEX_TIP][1] > landmarks[self.INDEX_PIP][1]

        # Middle finger curled
        middle_curled = landmarks[self.MIDDLE_TIP][1] > landmarks[self.MIDDLE_PIP][1]

        # Ring finger curled
        ring_curled = landmarks[self.RING_TIP][1] > landmarks[self.RING_PIP][1]

        # Pinky curled
        pinky_curled = landmarks[self.PINKY_TIP][1] > landmarks[self.PINKY_PIP][1]

        # All four fingers must be curled for a fist
        return index_curled and middle_curled and ring_curled and pinky_curled

    def is_open_palm(self, landmarks: list) -> bool:
        """
        Detect if hand is open (all fingers extended).

        An open palm is detected when all fingertips are above their
        corresponding PIP joints (fingers are extended).

        Args:
            landmarks: List of 21 (x, y, z) tuples from MediaPipe.

        Returns:
            True if open palm detected, False otherwise.
        """
        if not landmarks or len(landmarks) < 21:
            return False

        # Check if each finger is extended (tip above PIP joint)
        index_extended = landmarks[self.INDEX_TIP][1] < landmarks[self.INDEX_PIP][1]
        middle_extended = landmarks[self.MIDDLE_TIP][1] < landmarks[self.MIDDLE_PIP][1]
        ring_extended = landmarks[self.RING_TIP][1] < landmarks[self.RING_PIP][1]
        pinky_extended = landmarks[self.PINKY_TIP][1] < landmarks[self.PINKY_PIP][1]

        # All four fingers must be extended for open palm
        return index_extended and middle_extended and ring_extended and pinky_extended

    def detect_gesture(self, landmarks: list) -> str:
        """
        Detect the current gesture from landmarks.

        Args:
            landmarks: List of 21 (x, y, z) tuples from MediaPipe.

        Returns:
            Gesture name: "fist", "open", or "none".
        """
        if not landmarks:
            return "none"

        if self.is_fist(landmarks):
            return "fist"
        elif self.is_open_palm(landmarks):
            return "open"
        else:
            return "none"


def run_gesture_demo():
    """Demo: Detect gestures and print to console. Press 'q' to quit."""
    from src.camera.capture import Camera
    from src.tracking.hands import HandTracker
    import cv2

    camera = Camera()
    tracker = HandTracker(max_hands=2)
    detector = GestureDetector()

    if not camera.start():
        print("Error: Could not open camera")
        return

    print("Gesture detection started!")
    print("Try making a FIST or OPEN PALM. Press 'q' to quit.")

    while True:
        success, frame = camera.read_frame()
        if not success:
            break

        # Process hand tracking
        results = tracker.process_frame(frame)

        # Get landmarks and handedness
        all_landmarks = tracker.get_landmarks(results)
        handedness = tracker.get_handedness(results)

        # Detect gestures for each hand
        for i, landmarks in enumerate(all_landmarks):
            hand_label = handedness[i] if i < len(handedness) else "Unknown"
            gesture = detector.detect_gesture(landmarks)

            if gesture != "none":
                print(f"{hand_label} hand: {gesture.upper()}!")

        # Draw landmarks
        frame = tracker.draw_landmarks(frame, results)

        # Display frame
        cv2.imshow("Gesture Detection", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    tracker.close()
    camera.stop()
    cv2.destroyAllWindows()
    print("Gesture detection stopped.")


if __name__ == "__main__":
    run_gesture_demo()
