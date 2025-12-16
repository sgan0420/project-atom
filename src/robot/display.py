"""
Robot display module - renders Atom-style robot in PyGame.
"""

import pygame
import math


class Robot:
    """Atom-style robot that can be drawn in PyGame."""

    def __init__(self, center_x: int, center_y: int, scale: float = 1.0):
        """
        Initialize the robot.

        Args:
            center_x: X position of robot center.
            center_y: Y position of robot center.
            scale: Scale factor for robot size.
        """
        self.center_x = center_x
        self.center_y = center_y
        self.scale = scale

        # Robot colors (Atom-inspired blue/silver)
        self.body_color = (60, 80, 120)        # Dark blue-gray
        self.body_highlight = (100, 130, 180)  # Lighter blue
        self.metal_color = (140, 150, 160)     # Silver/metal
        self.eye_color = (0, 200, 255)         # Cyan glow
        self.eye_glow = (100, 220, 255)        # Light cyan
        self.accent_color = (200, 50, 50)      # Red accent

        # State
        self.state = "idle"

    def set_position(self, center_x: int, center_y: int):
        """Update robot position."""
        self.center_x = center_x
        self.center_y = center_y

    def set_state(self, state: str):
        """Set robot state (idle, punch_left, punch_right, guard, etc.)."""
        self.state = state

    def _s(self, value: int) -> int:
        """Scale a value by the robot's scale factor."""
        return int(value * self.scale)

    def draw(self, screen):
        """Draw the robot on the screen."""
        cx, cy = self.center_x, self.center_y
        s = self._s

        # Draw based on state
        if self.state == "idle":
            self._draw_idle(screen, cx, cy, s)
        elif self.state == "punch_left":
            self._draw_punch_left(screen, cx, cy, s)
        elif self.state == "punch_right":
            self._draw_punch_right(screen, cx, cy, s)
        elif self.state == "guard":
            self._draw_guard(screen, cx, cy, s)
        else:
            self._draw_idle(screen, cx, cy, s)

    def _draw_idle(self, screen, cx, cy, s):
        """Draw robot in idle stance."""
        # Body (torso)
        body_rect = pygame.Rect(cx - s(60), cy - s(50), s(120), s(150))
        pygame.draw.rect(screen, self.body_color, body_rect, border_radius=s(15))
        pygame.draw.rect(screen, self.body_highlight, body_rect, width=3, border_radius=s(15))

        # Chest plate
        chest_rect = pygame.Rect(cx - s(40), cy - s(30), s(80), s(60))
        pygame.draw.rect(screen, self.metal_color, chest_rect, border_radius=s(8))

        # Chest light (arc reactor style)
        pygame.draw.circle(screen, self.eye_glow, (cx, cy), s(15))
        pygame.draw.circle(screen, self.eye_color, (cx, cy), s(10))

        # Head
        head_rect = pygame.Rect(cx - s(40), cy - s(120), s(80), s(70))
        pygame.draw.rect(screen, self.body_color, head_rect, border_radius=s(10))
        pygame.draw.rect(screen, self.body_highlight, head_rect, width=2, border_radius=s(10))

        # Eyes
        pygame.draw.ellipse(screen, self.eye_glow, (cx - s(30), cy - s(100), s(20), s(12)))
        pygame.draw.ellipse(screen, self.eye_glow, (cx + s(10), cy - s(100), s(20), s(12)))
        pygame.draw.ellipse(screen, self.eye_color, (cx - s(28), cy - s(98), s(16), s(8)))
        pygame.draw.ellipse(screen, self.eye_color, (cx + s(12), cy - s(98), s(16), s(8)))

        # Arms (idle - down at sides)
        # Left arm
        left_shoulder = (cx - s(70), cy - s(40))
        left_elbow = (cx - s(90), cy + s(20))
        left_hand = (cx - s(85), cy + s(80))
        pygame.draw.line(screen, self.metal_color, left_shoulder, left_elbow, s(20))
        pygame.draw.line(screen, self.metal_color, left_elbow, left_hand, s(18))
        pygame.draw.circle(screen, self.body_highlight, left_shoulder, s(15))
        pygame.draw.circle(screen, self.body_highlight, left_elbow, s(12))
        pygame.draw.circle(screen, self.accent_color, left_hand, s(18))

        # Right arm
        right_shoulder = (cx + s(70), cy - s(40))
        right_elbow = (cx + s(90), cy + s(20))
        right_hand = (cx + s(85), cy + s(80))
        pygame.draw.line(screen, self.metal_color, right_shoulder, right_elbow, s(20))
        pygame.draw.line(screen, self.metal_color, right_elbow, right_hand, s(18))
        pygame.draw.circle(screen, self.body_highlight, right_shoulder, s(15))
        pygame.draw.circle(screen, self.body_highlight, right_elbow, s(12))
        pygame.draw.circle(screen, self.accent_color, right_hand, s(18))

        # Legs
        # Left leg
        left_hip = (cx - s(30), cy + s(100))
        left_knee = (cx - s(35), cy + s(170))
        left_foot = (cx - s(40), cy + s(240))
        pygame.draw.line(screen, self.metal_color, left_hip, left_knee, s(22))
        pygame.draw.line(screen, self.metal_color, left_knee, left_foot, s(20))
        pygame.draw.circle(screen, self.body_highlight, left_hip, s(15))
        pygame.draw.circle(screen, self.body_highlight, left_knee, s(12))
        pygame.draw.ellipse(screen, self.body_color, (left_foot[0] - s(15), left_foot[1] - s(5), s(35), s(15)))

        # Right leg
        right_hip = (cx + s(30), cy + s(100))
        right_knee = (cx + s(35), cy + s(170))
        right_foot = (cx + s(40), cy + s(240))
        pygame.draw.line(screen, self.metal_color, right_hip, right_knee, s(22))
        pygame.draw.line(screen, self.metal_color, right_knee, right_foot, s(20))
        pygame.draw.circle(screen, self.body_highlight, right_hip, s(15))
        pygame.draw.circle(screen, self.body_highlight, right_knee, s(12))
        pygame.draw.ellipse(screen, self.body_color, (right_foot[0] - s(20), right_foot[1] - s(5), s(35), s(15)))

    def _draw_punch_left(self, screen, cx, cy, s):
        """Draw robot punching with left arm."""
        # Body (same as idle)
        self._draw_body_and_head(screen, cx, cy, s)

        # Left arm - PUNCHING (extended forward/left)
        left_shoulder = (cx - s(70), cy - s(40))
        left_elbow = (cx - s(130), cy - s(30))
        left_hand = (cx - s(200), cy - s(40))
        pygame.draw.line(screen, self.metal_color, left_shoulder, left_elbow, s(22))
        pygame.draw.line(screen, self.metal_color, left_elbow, left_hand, s(20))
        pygame.draw.circle(screen, self.body_highlight, left_shoulder, s(15))
        pygame.draw.circle(screen, self.body_highlight, left_elbow, s(12))
        pygame.draw.circle(screen, self.accent_color, left_hand, s(22))  # Bigger fist

        # Right arm (normal)
        right_shoulder = (cx + s(70), cy - s(40))
        right_elbow = (cx + s(90), cy + s(20))
        right_hand = (cx + s(85), cy + s(80))
        pygame.draw.line(screen, self.metal_color, right_shoulder, right_elbow, s(20))
        pygame.draw.line(screen, self.metal_color, right_elbow, right_hand, s(18))
        pygame.draw.circle(screen, self.body_highlight, right_shoulder, s(15))
        pygame.draw.circle(screen, self.body_highlight, right_elbow, s(12))
        pygame.draw.circle(screen, self.accent_color, right_hand, s(18))

        self._draw_legs(screen, cx, cy, s)

    def _draw_punch_right(self, screen, cx, cy, s):
        """Draw robot punching with right arm."""
        self._draw_body_and_head(screen, cx, cy, s)

        # Left arm (normal)
        left_shoulder = (cx - s(70), cy - s(40))
        left_elbow = (cx - s(90), cy + s(20))
        left_hand = (cx - s(85), cy + s(80))
        pygame.draw.line(screen, self.metal_color, left_shoulder, left_elbow, s(20))
        pygame.draw.line(screen, self.metal_color, left_elbow, left_hand, s(18))
        pygame.draw.circle(screen, self.body_highlight, left_shoulder, s(15))
        pygame.draw.circle(screen, self.body_highlight, left_elbow, s(12))
        pygame.draw.circle(screen, self.accent_color, left_hand, s(18))

        # Right arm - PUNCHING (extended forward/right)
        right_shoulder = (cx + s(70), cy - s(40))
        right_elbow = (cx + s(130), cy - s(30))
        right_hand = (cx + s(200), cy - s(40))
        pygame.draw.line(screen, self.metal_color, right_shoulder, right_elbow, s(22))
        pygame.draw.line(screen, self.metal_color, right_elbow, right_hand, s(20))
        pygame.draw.circle(screen, self.body_highlight, right_shoulder, s(15))
        pygame.draw.circle(screen, self.body_highlight, right_elbow, s(12))
        pygame.draw.circle(screen, self.accent_color, right_hand, s(22))  # Bigger fist

        self._draw_legs(screen, cx, cy, s)

    def _draw_guard(self, screen, cx, cy, s):
        """Draw robot in guard stance (both arms up)."""
        self._draw_body_and_head(screen, cx, cy, s)

        # Left arm - guard position (raised)
        left_shoulder = (cx - s(70), cy - s(40))
        left_elbow = (cx - s(100), cy - s(80))
        left_hand = (cx - s(60), cy - s(120))
        pygame.draw.line(screen, self.metal_color, left_shoulder, left_elbow, s(20))
        pygame.draw.line(screen, self.metal_color, left_elbow, left_hand, s(18))
        pygame.draw.circle(screen, self.body_highlight, left_shoulder, s(15))
        pygame.draw.circle(screen, self.body_highlight, left_elbow, s(12))
        pygame.draw.circle(screen, self.accent_color, left_hand, s(18))

        # Right arm - guard position (raised)
        right_shoulder = (cx + s(70), cy - s(40))
        right_elbow = (cx + s(100), cy - s(80))
        right_hand = (cx + s(60), cy - s(120))
        pygame.draw.line(screen, self.metal_color, right_shoulder, right_elbow, s(20))
        pygame.draw.line(screen, self.metal_color, right_elbow, right_hand, s(18))
        pygame.draw.circle(screen, self.body_highlight, right_shoulder, s(15))
        pygame.draw.circle(screen, self.body_highlight, right_elbow, s(12))
        pygame.draw.circle(screen, self.accent_color, right_hand, s(18))

        self._draw_legs(screen, cx, cy, s)

    def _draw_body_and_head(self, screen, cx, cy, s):
        """Draw robot body and head (shared by all poses)."""
        # Body (torso)
        body_rect = pygame.Rect(cx - s(60), cy - s(50), s(120), s(150))
        pygame.draw.rect(screen, self.body_color, body_rect, border_radius=s(15))
        pygame.draw.rect(screen, self.body_highlight, body_rect, width=3, border_radius=s(15))

        # Chest plate
        chest_rect = pygame.Rect(cx - s(40), cy - s(30), s(80), s(60))
        pygame.draw.rect(screen, self.metal_color, chest_rect, border_radius=s(8))

        # Chest light
        pygame.draw.circle(screen, self.eye_glow, (cx, cy), s(15))
        pygame.draw.circle(screen, self.eye_color, (cx, cy), s(10))

        # Head
        head_rect = pygame.Rect(cx - s(40), cy - s(120), s(80), s(70))
        pygame.draw.rect(screen, self.body_color, head_rect, border_radius=s(10))
        pygame.draw.rect(screen, self.body_highlight, head_rect, width=2, border_radius=s(10))

        # Eyes
        pygame.draw.ellipse(screen, self.eye_glow, (cx - s(30), cy - s(100), s(20), s(12)))
        pygame.draw.ellipse(screen, self.eye_glow, (cx + s(10), cy - s(100), s(20), s(12)))
        pygame.draw.ellipse(screen, self.eye_color, (cx - s(28), cy - s(98), s(16), s(8)))
        pygame.draw.ellipse(screen, self.eye_color, (cx + s(12), cy - s(98), s(16), s(8)))

    def _draw_legs(self, screen, cx, cy, s):
        """Draw robot legs (shared by all poses)."""
        # Left leg
        left_hip = (cx - s(30), cy + s(100))
        left_knee = (cx - s(35), cy + s(170))
        left_foot = (cx - s(40), cy + s(240))
        pygame.draw.line(screen, self.metal_color, left_hip, left_knee, s(22))
        pygame.draw.line(screen, self.metal_color, left_knee, left_foot, s(20))
        pygame.draw.circle(screen, self.body_highlight, left_hip, s(15))
        pygame.draw.circle(screen, self.body_highlight, left_knee, s(12))
        pygame.draw.ellipse(screen, self.body_color, (left_foot[0] - s(15), left_foot[1] - s(5), s(35), s(15)))

        # Right leg
        right_hip = (cx + s(30), cy + s(100))
        right_knee = (cx + s(35), cy + s(170))
        right_foot = (cx + s(40), cy + s(240))
        pygame.draw.line(screen, self.metal_color, right_hip, right_knee, s(22))
        pygame.draw.line(screen, self.metal_color, right_knee, right_foot, s(20))
        pygame.draw.circle(screen, self.body_highlight, right_hip, s(15))
        pygame.draw.circle(screen, self.body_highlight, right_knee, s(12))
        pygame.draw.ellipse(screen, self.body_color, (right_foot[0] - s(20), right_foot[1] - s(5), s(35), s(15)))


def run_robot_demo():
    """Demo: Display robot with different poses. Press 1-4 to change pose, q/ESC to quit."""
    from src.ui.window import Window

    window = Window(800, 600, "Project Atom - Robot Demo")
    window.start()

    # Create robot in center of screen
    robot = Robot(400, 280, scale=0.8)

    print("Robot demo started!")
    print("Press 1: Idle, 2: Punch Left, 3: Punch Right, 4: Guard")
    print("Press 'q' or ESC to quit.")

    while window.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                window.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    window.running = False
                elif event.key == pygame.K_1:
                    robot.set_state("idle")
                    print("State: idle")
                elif event.key == pygame.K_2:
                    robot.set_state("punch_left")
                    print("State: punch_left")
                elif event.key == pygame.K_3:
                    robot.set_state("punch_right")
                    print("State: punch_right")
                elif event.key == pygame.K_4:
                    robot.set_state("guard")
                    print("State: guard")

        # Clear screen
        window.clear((20, 20, 30))

        # Draw robot
        robot.draw(window.screen)

        # Update display
        window.update(60)

    window.stop()
    print("Robot demo closed.")


if __name__ == "__main__":
    run_robot_demo()
