"""Camera capture module."""

import cv2


class Camera:
    """Webcam capture handler."""

    def __init__(self, camera_id: int = 0):
        self.camera_id = camera_id
        self.cap = None

    def start(self) -> bool:
        self.cap = cv2.VideoCapture(self.camera_id)
        return self.cap.isOpened()

    def read_frame(self, mirror: bool = True):
        if self.cap is None:
            return False, None
        success, frame = self.cap.read()
        if success and mirror:
            frame = cv2.flip(frame, 1)
        return success, frame

    def stop(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
