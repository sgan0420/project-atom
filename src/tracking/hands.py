"""
Hand tracking module using MediaPipe.
"""

import mediapipe as mp
import cv2


class HandTracker:
    """Tracks hands using MediaPipe."""

    def __init__(self, max_hands: int = 1, detection_confidence: float = 0.7):
        """
        Initialize hand tracker.

        Args:
            max_hands: Maximum number of hands to detect.
            detection_confidence: Minimum confidence for detection (0-1).
        """
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=0.5,
        )

    def process_frame(self, frame):
        """
        Process a frame and detect hands.

        Args:
            frame: BGR image from OpenCV.

        Returns:
            MediaPipe results object with hand landmarks.
        """
        # MediaPipe needs RGB, OpenCV gives BGR
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return self.hands.process(rgb_frame)

    def get_landmarks(self, results):
        """
        Extract landmark coordinates from results.

        Args:
            results: MediaPipe results object.

        Returns:
            List of hands, each hand is a list of 21 landmarks (x, y, z).
            Returns empty list if no hands detected.
        """
        if not results.multi_hand_landmarks:
            return []

        all_hands = []
        for hand_landmarks in results.multi_hand_landmarks:
            landmarks = []
            for landmark in hand_landmarks.landmark:
                landmarks.append((landmark.x, landmark.y, landmark.z))
            all_hands.append(landmarks)

        return all_hands

    def get_handedness(self, results):
        """
        Get which hand is which (left or right).

        Args:
            results: MediaPipe results object.

        Returns:
            List of hand labels ("Left" or "Right") matching the order of landmarks.
            Returns empty list if no hands detected.
        """
        if not results.multi_handedness:
            return []

        labels = []
        for hand_info in results.multi_handedness:
            # MediaPipe returns "Left" or "Right"
            label = hand_info.classification[0].label
            labels.append(label)

        return labels

    def close(self):
        """Release resources."""
        self.hands.close()

    def draw_landmarks(self, frame, results):
        """
        Draw hand landmarks and connections on frame.

        Args:
            frame: BGR image to draw on.
            results: MediaPipe results object.

        Returns:
            Frame with landmarks drawn.
        """
        if not results.multi_hand_landmarks:
            return frame

        h, w, _ = frame.shape
        handedness = self.get_handedness(results)

        # Connection pairs (which landmarks connect to which)
        connections = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),  # Thumb
            (0, 5),
            (5, 6),
            (6, 7),
            (7, 8),  # Index
            (0, 9),
            (9, 10),
            (10, 11),
            (11, 12),  # Middle
            (0, 13),
            (13, 14),
            (14, 15),
            (15, 16),  # Ring
            (0, 17),
            (17, 18),
            (18, 19),
            (19, 20),  # Pinky
            (5, 9),
            (9, 13),
            (13, 17),  # Palm
        ]

        # Colors for left and right hands (BGR format)
        colors = {
            "Left": {
                "line": (0, 255, 0),
                "joint": (0, 200, 0),
                "tip": (0, 255, 255),
            },  # Green/Yellow
            "Right": {
                "line": (255, 0, 0),
                "joint": (200, 0, 0),
                "tip": (255, 0, 255),
            },  # Blue/Magenta
        }

        for idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            # Get hand label (Left or Right)
            label = handedness[idx] if idx < len(handedness) else "Right"
            hand_colors = colors.get(label, colors["Right"])

            # Convert normalized coordinates to pixel coordinates
            points = []
            for landmark in hand_landmarks.landmark:
                px = int(landmark.x * w)
                py = int(landmark.y * h)
                points.append((px, py))

            # Draw connections (lines)
            for start_idx, end_idx in connections:
                cv2.line(
                    frame, points[start_idx], points[end_idx], hand_colors["line"], 2
                )

            # Draw landmarks (circles)
            for i, point in enumerate(points):
                if i in [4, 8, 12, 16, 20]:  # Fingertips
                    color = hand_colors["tip"]
                    radius = 8
                else:
                    color = hand_colors["joint"]
                    radius = 5
                cv2.circle(frame, point, radius, color, -1)

            # Draw label near wrist
            wrist = points[0]
            cv2.putText(
                frame,
                label,
                (wrist[0] - 30, wrist[1] + 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                hand_colors["line"],
                2,
            )

        return frame


def run_tracking_demo():
    """Demo: Track both hands with visual overlay. Press 'q' to quit."""
    from src.camera.capture import Camera

    camera = Camera()
    tracker = HandTracker(max_hands=2)  # Track both hands

    if not camera.start():
        print("Error: Could not open camera")
        return

    print("Hand tracking started! Show your hand. Press 'q' to quit.")

    while True:
        success, frame = camera.read_frame()
        if not success:
            break

        # Process frame for hand detection
        results = tracker.process_frame(frame)

        # Draw landmarks on frame
        frame = tracker.draw_landmarks(frame, results)

        # Display frame
        cv2.imshow("Project Atom - Hand Tracking", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Cleanup
    tracker.close()
    camera.stop()
    cv2.destroyAllWindows()
    print("Hand tracking stopped.")


if __name__ == "__main__":
    run_tracking_demo()
