"""
3-panel layout module for Project Atom.
"""

import pygame
import cv2
import numpy as np


class ThreePanelLayout:
    """Manages the 3-panel layout (left hand, robot, right hand)."""

    def __init__(self, screen_width: int, screen_height: int):
        """
        Initialize the 3-panel layout.

        Args:
            screen_width: Total screen width.
            screen_height: Total screen height.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height

        # Calculate panel dimensions (3 equal columns)
        self.panel_width = screen_width // 3
        self.panel_height = screen_height

        # Panel rectangles (x, y, width, height)
        self.left_panel = pygame.Rect(0, 0, self.panel_width, self.panel_height)
        self.middle_panel = pygame.Rect(self.panel_width, 0, self.panel_width, self.panel_height)
        self.right_panel = pygame.Rect(self.panel_width * 2, 0, self.panel_width, self.panel_height)

        # Colors
        self.border_color = (60, 60, 60)    # Gray border
        self.middle_color = (30, 30, 40)    # Robot arena background

    def draw_borders(self, screen, width: int = 2):
        """Draw borders between panels."""
        pygame.draw.line(
            screen,
            self.border_color,
            (self.panel_width, 0),
            (self.panel_width, self.screen_height),
            width
        )
        pygame.draw.line(
            screen,
            self.border_color,
            (self.panel_width * 2, 0),
            (self.panel_width * 2, self.screen_height),
            width
        )

    def cv2_to_pygame(self, frame):
        """
        Convert OpenCV frame (BGR) to PyGame surface.

        Args:
            frame: OpenCV BGR image.

        Returns:
            PyGame surface.
        """
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_rgb = np.rot90(frame_rgb)
        frame_rgb = np.flipud(frame_rgb)
        surface = pygame.surfarray.make_surface(frame_rgb)
        return surface

    def draw_webcam_in_panel(self, screen, frame, panel: str):
        """
        Draw webcam frame in a panel, cropping to show the relevant side.

        Args:
            screen: PyGame screen.
            frame: OpenCV frame.
            panel: "left" or "right".
        """
        if frame is None:
            return

        if panel == "left":
            target_rect = self.left_panel
        elif panel == "right":
            target_rect = self.right_panel
        else:
            return

        surface = self.cv2_to_pygame(frame)
        frame_w, frame_h = surface.get_size()

        # Scale to fill panel height
        scale = target_rect.height / frame_h
        new_w = int(frame_w * scale)
        new_h = target_rect.height

        scaled_surface = pygame.transform.scale(surface, (new_w, new_h))

        # Crop from left or right side
        if panel == "left":
            crop_x = 0
        else:
            crop_x = new_w - target_rect.width

        crop_rect = pygame.Rect(crop_x, 0, target_rect.width, target_rect.height)
        cropped_surface = scaled_surface.subsurface(crop_rect)

        screen.blit(cropped_surface, target_rect.topleft)


def run_panels_demo():
    """Demo: 3-panel layout with gesture-controlled robot. Press 'q' or ESC to quit."""
    from src.ui.window import Window
    from src.camera.capture import Camera
    from src.tracking.hands import HandTracker
    from src.tracking.gestures import GestureDetector
    from src.robot.display import Robot

    window = Window()
    window.start_fullscreen()

    layout = ThreePanelLayout(window.width, window.height)
    camera = Camera()
    tracker = HandTracker(max_hands=2)
    detector = GestureDetector()

    # Create robot in center of middle panel
    robot_x = layout.middle_panel.centerx
    robot_y = layout.middle_panel.centery
    robot = Robot(robot_x, robot_y, scale=1.0)

    if not camera.start():
        print("Error: Could not open camera")
        window.stop()
        return

    print(f"3-panel layout started! Screen: {window.width}x{window.height}")
    print("Controls: FIST = punch, OPEN PALM = idle, BOTH FISTS = guard")
    print("Press 'q' or ESC to quit.")

    while window.running:
        window.handle_events()

        success, frame = camera.read_frame()

        window.clear()

        # Draw middle panel background (robot arena)
        pygame.draw.rect(window.screen, layout.middle_color, layout.middle_panel)

        if success:
            results = tracker.process_frame(frame)

            all_landmarks = tracker.get_landmarks(results)
            handedness = tracker.get_handedness(results)

            # Detect gestures for each hand
            left_gesture = "none"
            right_gesture = "none"

            for i, landmarks in enumerate(all_landmarks):
                hand_label = handedness[i] if i < len(handedness) else "Unknown"
                gesture = detector.detect_gesture(landmarks)

                if hand_label == "Left":
                    left_gesture = gesture
                elif hand_label == "Right":
                    right_gesture = gesture

            # Determine robot state based on gestures
            if left_gesture == "fist" and right_gesture == "fist":
                robot.set_state("guard")
            elif left_gesture == "fist":
                robot.set_state("punch_left")
            elif right_gesture == "fist":
                robot.set_state("punch_right")
            else:
                robot.set_state("idle")

            # Draw webcam with hand landmarks in side panels
            frame_with_landmarks = tracker.draw_landmarks(frame.copy(), results)
            layout.draw_webcam_in_panel(window.screen, frame_with_landmarks, "left")
            layout.draw_webcam_in_panel(window.screen, frame_with_landmarks, "right")

        robot.draw(window.screen)
        layout.draw_borders(window.screen, width=3)

        window.update(60)

    tracker.close()
    camera.stop()
    window.stop()
    print("Layout closed.")


if __name__ == "__main__":
    run_panels_demo()
