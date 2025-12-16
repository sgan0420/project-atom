"""
Camera capture module using OpenCV.
"""

import cv2


class Camera:
    """Handles webcam capture."""

    def __init__(self, camera_id: int = 0):
        """
        Initialize camera.

        Args:
            camera_id: Camera device ID (0 = default webcam)
        """
        self.camera_id = camera_id
        self.cap = None

    def start(self) -> bool:
        """
        Start the camera capture.

        Returns:
            True if camera opened successfully, False otherwise.
        """
        self.cap = cv2.VideoCapture(self.camera_id)
        return self.cap.isOpened()

    def read_frame(self, mirror: bool = True):
        """
        Read a frame from the camera.

        Args:
            mirror: If True, flip the frame horizontally (like a mirror).

        Returns:
            Tuple of (success, frame). Frame is None if read failed.
        """
        if self.cap is None:
            return False, None

        success, frame = self.cap.read()

        if success and mirror:
            frame = cv2.flip(frame, 1)  # 1 = horizontal flip

        return success, frame

    def stop(self):
        """Release the camera."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None


def run_camera_demo():
    """Demo: Display webcam feed in a window. Press 'q' to quit."""
    camera = Camera()

    if not camera.start():
        print("Error: Could not open camera")
        return

    print("Camera started! Press 'q' to quit.")

    while True:
        success, frame = camera.read_frame()

        if not success:
            print("Error: Could not read frame")
            break

        # Display the frame
        cv2.imshow("Project Atom - Webcam", frame)

        # Check for 'q' key to quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Cleanup
    camera.stop()
    cv2.destroyAllWindows()
    print("Camera stopped.")


if __name__ == "__main__":
    run_camera_demo()
