"""
Project Atom - 3D Robot with Gesture Control
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MODELS_PATH = PROJECT_ROOT / "assets" / "models"
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

from ursina import *
from direct.actor.Actor import Actor
from panda3d.core import Material, LColor, Texture as P3DTexture
import cv2
import threading
import queue

application.asset_folder = PROJECT_ROOT


# ============================================================================
# UI STYLING CONSTANTS
# ============================================================================
class UIColors:
    """Centralized color palette for consistent UI styling."""

    BACKGROUND = color.rgb(20, 20, 35)
    PANEL_BG = color.rgba(15, 15, 25, 200)
    PANEL_BORDER = color.rgba(60, 70, 90, 255)

    TEXT_PRIMARY = color.rgba(220, 225, 235, 255)
    TEXT_SECONDARY = color.rgba(140, 150, 170, 255)
    TEXT_MUTED = color.rgba(90, 100, 120, 255)

    ACCENT_BLUE = color.rgba(80, 140, 255, 255)
    ACCENT_GREEN = color.rgba(80, 220, 140, 255)
    ACCENT_ORANGE = color.rgba(255, 180, 80, 255)
    ACCENT_RED = color.rgba(255, 100, 100, 255)
    ACCENT_PURPLE = color.rgba(180, 120, 255, 255)
    ACCENT_CYAN = color.rgba(80, 220, 230, 255)
    ACCENT_YELLOW = color.rgba(255, 220, 80, 255)

    ACTIVE_GLOW = color.rgba(100, 200, 255, 255)
    INACTIVE = color.rgba(70, 75, 90, 255)


class ActionCard(Entity):
    """A styled card representing a gesture action with highlight capability."""

    def __init__(
        self, action_id, label, gesture_hint, accent_color, position=(0, 0), **kwargs
    ):
        super().__init__(parent=camera.ui, position=position, **kwargs)

        self.action_id = action_id
        self.is_active = False
        self.target_scale = 1.0
        self.current_scale = 1.0
        self.accent_color = accent_color

        # Card dimensions
        card_width = 0.19
        card_height = 0.058

        # Background panel
        self.bg = Entity(
            parent=self,
            model="quad",
            scale=(card_width, card_height),
            color=UIColors.PANEL_BG,
            z=0.02,
        )

        # Left accent bar
        self.accent_bar = Entity(
            parent=self,
            model="quad",
            scale=(0.005, card_height - 0.008),
            position=(-card_width / 2 + 0.006, 0),
            color=UIColors.INACTIVE,
            z=0.01,
        )

        # Action label (main text)
        self.label = Text(
            parent=self,
            text=label,
            position=(-card_width / 2 + 0.018, 0.008),
            origin=(-0.5, 0),
            scale=0.65,
            color=UIColors.TEXT_SECONDARY,
        )

        # Gesture hint (smaller subtext)
        self.hint = Text(
            parent=self,
            text=gesture_hint,
            position=(-card_width / 2 + 0.018, -0.014),
            origin=(-0.5, 0),
            scale=0.45,
            color=UIColors.TEXT_MUTED,
        )

    def set_active(self, active):
        """Set the active state with visual feedback."""
        if active == self.is_active:
            return
        self.is_active = active
        self.target_scale = 1.06 if active else 1.0

        if active:
            self.accent_bar.color = self.accent_color
            self.label.color = UIColors.TEXT_PRIMARY
            self.label.scale = 0.72
            self.hint.color = UIColors.TEXT_SECONDARY
            self.bg.color = color.rgba(30, 35, 50, 230)
        else:
            self.accent_bar.color = UIColors.INACTIVE
            self.label.color = UIColors.TEXT_SECONDARY
            self.label.scale = 0.65
            self.hint.color = UIColors.TEXT_MUTED
            self.bg.color = UIColors.PANEL_BG

    def update(self):
        """Smooth scale animation."""
        if abs(self.current_scale - self.target_scale) > 0.001:
            self.current_scale = lerp(
                self.current_scale, self.target_scale, time.dt * 12
            )
            self.scale = self.current_scale


class DetectionStatusPanel(Entity):
    """Panel showing current detection status, gesture, and confidence."""

    def __init__(self, position=(0, 0), **kwargs):
        super().__init__(parent=camera.ui, position=position, **kwargs)

        panel_width = 0.32  # Wider panel to fit content
        panel_height = 0.12

        # Background
        self.bg = Entity(
            parent=self,
            model="quad",
            scale=(panel_width, panel_height),
            color=UIColors.PANEL_BG,
            z=0.02,
        )

        # Header
        self.header = Text(
            parent=self,
            text="DETECTION STATUS",
            position=(-panel_width / 2 + 0.015, panel_height / 2 - 0.022),
            origin=(-0.5, 0),
            scale=0.5,
            color=UIColors.TEXT_MUTED,
        )

        # Detected gesture label
        self.gesture_label = Text(
            parent=self,
            text="Gesture:",
            position=(-panel_width / 2 + 0.015, 0.015),
            origin=(-0.5, 0),
            scale=0.55,
            color=UIColors.TEXT_SECONDARY,
        )

        self.gesture_value = Text(
            parent=self,
            text="--",
            position=(0.02, 0.015),
            origin=(-0.5, 0),
            scale=0.55,
            color=UIColors.TEXT_PRIMARY,
        )

        # Action label
        self.action_label = Text(
            parent=self,
            text="Action:",
            position=(-panel_width / 2 + 0.015, -0.012),
            origin=(-0.5, 0),
            scale=0.55,
            color=UIColors.TEXT_SECONDARY,
        )

        self.action_value = Text(
            parent=self,
            text="Idle",
            position=(0.02, -0.012),
            origin=(-0.5, 0),
            scale=0.55,
            color=UIColors.ACCENT_BLUE,
        )

        # Confidence bar background
        self.conf_label = Text(
            parent=self,
            text="Conf:",
            position=(-panel_width / 2 + 0.015, -0.042),
            origin=(-0.5, 0),
            scale=0.5,
            color=UIColors.TEXT_MUTED,
        )

        bar_width = 0.12
        self.conf_bar_bg = Entity(
            parent=self,
            model="quad",
            scale=(bar_width, 0.012),
            position=(0.02, -0.042),
            color=UIColors.INACTIVE,
            z=0.01,
        )

        self.conf_bar_fill = Entity(
            parent=self,
            model="quad",
            scale=(0, 0.012),
            position=(0.02 - bar_width / 2, -0.042),
            origin=(-0.5, 0),
            color=UIColors.ACCENT_GREEN,
            z=0.005,
        )

        self.conf_bar_width = bar_width
        self.conf_text = Text(
            parent=self,
            text="--",
            position=(0.09, -0.042),
            origin=(-0.5, 0),
            scale=0.5,
            color=UIColors.TEXT_SECONDARY,
        )

    def update_status(self, left_gesture, right_gesture, action, confidence):
        """Update the detection status display."""
        # Format gesture display
        if left_gesture == "none" and right_gesture == "none":
            gesture_str = "No hands detected"
            self.gesture_value.color = UIColors.TEXT_MUTED
        else:
            parts = []
            if left_gesture != "none":
                parts.append(f"L: {left_gesture.title()}")
            if right_gesture != "none":
                parts.append(f"R: {right_gesture.title()}")
            gesture_str = " | ".join(parts)
            self.gesture_value.color = UIColors.TEXT_PRIMARY

        self.gesture_value.text = gesture_str

        # Format action display
        action_names = {
            "idle": "Idle",
            "boxing": "Boxing",
            "dance": "Dancing",
            "punch_left": "Left Punch",
            "punch_right": "Right Punch",
            "kick_left": "Left Kick",
            "kick_right": "Right Kick",
        }
        self.action_value.text = action_names.get(action, action.title())

        # Color code action
        action_colors = {
            "idle": UIColors.TEXT_MUTED,
            "boxing": UIColors.ACCENT_RED,
            "dance": UIColors.ACCENT_PURPLE,
            "punch_left": UIColors.ACCENT_ORANGE,
            "punch_right": UIColors.ACCENT_ORANGE,
            "kick_left": UIColors.ACCENT_CYAN,
            "kick_right": UIColors.ACCENT_CYAN,
        }
        self.action_value.color = action_colors.get(action, UIColors.ACCENT_BLUE)

        # Update confidence bar
        conf_pct = confidence * 100
        self.conf_bar_fill.scale_x = self.conf_bar_width * confidence
        self.conf_text.text = f"{conf_pct:.0f}%"

        # Color confidence bar based on level
        if confidence > 0.8:
            self.conf_bar_fill.color = UIColors.ACCENT_GREEN
        elif confidence > 0.5:
            self.conf_bar_fill.color = UIColors.ACCENT_YELLOW
        else:
            self.conf_bar_fill.color = UIColors.ACCENT_RED


class GestureUI:
    """Main UI controller for gesture display."""

    def __init__(self):
        self.action_cards = {}
        self.current_action = "idle"

        # Create title
        self.title = Text(
            text="GESTURE CONTROLS",
            position=(-0.87, 0.42),
            origin=(-0.5, 0),
            scale=0.6,
            color=UIColors.TEXT_MUTED,
        )

        # Action card definitions
        actions = [
            ("boxing", "Boxing", "Both fists", UIColors.ACCENT_RED),
            ("dance", "Dance", "Both palms open", UIColors.ACCENT_PURPLE),
            ("punch_left", "Left Punch", "Left fist only", UIColors.ACCENT_ORANGE),
            ("punch_right", "Right Punch", "Right fist only", UIColors.ACCENT_ORANGE),
            ("kick_left", "Left Kick", "Left palm only", UIColors.ACCENT_CYAN),
            ("kick_right", "Right Kick", "Right palm only", UIColors.ACCENT_CYAN),
        ]

        # Create action cards in a vertical list
        start_y = 0.35
        spacing = 0.068

        for i, (action_id, label, hint, accent) in enumerate(actions):
            card = ActionCard(
                action_id=action_id,
                label=label,
                gesture_hint=hint,
                accent_color=accent,
                position=(-0.78, start_y - i * spacing),
            )
            self.action_cards[action_id] = card

        # Detection status panel
        self.status_panel = DetectionStatusPanel(position=(-0.71, -0.38))

    def update(self, action, left_gesture="none", right_gesture="none", confidence=0.0):
        """Update UI state based on current action and gestures."""
        # Update detection status panel
        self.status_panel.update_status(left_gesture, right_gesture, action, confidence)

        # Update action cards
        if action != self.current_action:
            # Deactivate previous
            if self.current_action in self.action_cards:
                self.action_cards[self.current_action].set_active(False)

            # Activate new
            if action in self.action_cards:
                self.action_cards[action].set_active(True)

            self.current_action = action


class GestureController:
    """Handles webcam capture and gesture detection in a background thread."""

    def __init__(self):
        from src.camera.capture import Camera
        from src.tracking.hands import HandTracker
        from src.tracking.gestures import GestureDetector

        self.camera = Camera()
        self.tracker = HandTracker(max_hands=2)
        self.detector = GestureDetector()
        self.running = False
        self.gesture_queue = queue.Queue()
        self.frame_queue = queue.Queue(maxsize=2)
        self.thread = None

    def start(self):
        if not self.camera.start():
            return False
        self.running = True
        self.thread = threading.Thread(target=self._process_loop, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
        self.tracker.close()
        self.camera.stop()

    def _process_loop(self):
        while self.running:
            success, frame = self.camera.read_frame()
            if not success:
                continue

            results = self.tracker.process_frame(frame)
            all_landmarks = self.tracker.get_landmarks(results)
            handedness = self.tracker.get_handedness(results)

            left_gesture = right_gesture = "none"
            confidence = 0.0
            gesture_count = 0

            for i, landmarks in enumerate(all_landmarks):
                hand_label = handedness[i] if i < len(handedness) else "Unknown"
                gesture = self.detector.detect_gesture(landmarks)
                if hand_label == "Left":
                    left_gesture = gesture
                    if gesture != "none":
                        confidence += 1.0
                        gesture_count += 1
                elif hand_label == "Right":
                    right_gesture = gesture
                    if gesture != "none":
                        confidence += 1.0
                        gesture_count += 1

            # Calculate confidence based on clear gesture detection
            if gesture_count > 0:
                confidence = confidence / gesture_count
            elif len(all_landmarks) > 0:
                # Hands detected but no clear gesture
                confidence = 0.5
            else:
                confidence = 0.0

            # Map gestures to animations (intuitive mappings)
            if left_gesture == "fist" and right_gesture == "fist":
                pose = "boxing"
                confidence = 1.0  # Both hands matching = high confidence
            elif left_gesture == "open" and right_gesture == "open":
                pose = "dance"
                confidence = 1.0
            # Single hand fist = punch that side
            elif left_gesture == "fist":
                pose = "punch_left"
                confidence = 0.85
            elif right_gesture == "fist":
                pose = "punch_right"
                confidence = 0.85
            # Single hand open = kick that side
            elif left_gesture == "open":
                pose = "kick_left"
                confidence = 0.85
            elif right_gesture == "open":
                pose = "kick_right"
                confidence = 0.85
            else:
                pose = "idle"
                confidence = 0.0 if len(all_landmarks) == 0 else 0.3

            # Pack all data into a dict for the UI
            gesture_data = {
                "pose": pose,
                "left_gesture": left_gesture,
                "right_gesture": right_gesture,
                "confidence": confidence,
            }

            try:
                self.gesture_queue.put_nowait(gesture_data)
            except queue.Full:
                pass

            frame_with_landmarks = self.tracker.draw_landmarks(frame.copy(), results)
            try:
                while not self.frame_queue.empty():
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        break
                self.frame_queue.put_nowait(frame_with_landmarks)
            except queue.Full:
                pass

    def get_latest_gesture_data(self):
        """Get the latest gesture data dict with pose, gestures, and confidence."""
        data = None
        while not self.gesture_queue.empty():
            try:
                data = self.gesture_queue.get_nowait()
            except queue.Empty:
                break
        return data

    def get_latest_frame(self):
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None


class AnimatedRobot(Entity):
    """3D Robot using animated GLB models."""

    MATERIALS = None  # Class-level cache for materials

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.animation_files = {
            "idle": MODELS_PATH / "robot-default.glb",
            "dance": MODELS_PATH / "robot-dance.glb",
            "punch_left": MODELS_PATH / "robot-punch-left.glb",
            "punch_right": MODELS_PATH / "robot-punch-right.glb",
            "kick_left": MODELS_PATH / "robot-left-kick.glb",
            "kick_right": MODELS_PATH / "robot-right-kick.glb",
            "boxing": MODELS_PATH / "robot-boxing.glb",
        }
        self.current_animation = None
        self.current_actor = None
        self._init_materials()
        self.set_animation("idle")

    def _init_materials(self):
        if AnimatedRobot.MATERIALS:
            return

        def make_material(shininess, ambient, diffuse, specular):
            mat = Material()
            mat.setShininess(shininess)
            mat.setAmbient(LColor(*ambient, 1))
            mat.setDiffuse(LColor(*diffuse, 1))
            mat.setSpecular(LColor(*specular, 1))
            return mat

        AnimatedRobot.MATERIALS = {
            "white": make_material(
                100, (0.4, 0.4, 0.4), (0.95, 0.95, 0.95), (1.0, 1.0, 1.0)
            ),
            "blue": make_material(
                120, (0.1, 0.15, 0.4), (0.2, 0.4, 0.95), (0.5, 0.6, 1.0)
            ),
            "red": make_material(
                120, (0.4, 0.1, 0.1), (0.95, 0.2, 0.15), (1.0, 0.5, 0.5)
            ),
            "yellow": make_material(
                150, (0.4, 0.35, 0.0), (1.0, 0.85, 0.1), (1.0, 1.0, 0.6)
            ),
            "gray": make_material(
                80, (0.15, 0.15, 0.15), (0.35, 0.35, 0.4), (0.6, 0.6, 0.6)
            ),
        }

    def _apply_colors(self):
        if not self.current_actor:
            return

        mats = AnimatedRobot.MATERIALS
        # Height zones: 0=feet, 1=head (Z range: 0.1 to 23.5)
        zones = [
            (0.92, "yellow"),  # Head top
            (0.82, "white"),  # Head
            (0.72, "blue"),  # Chest
            (0.58, "white"),  # Abdomen
            (0.45, "gray"),  # Waist
            (0.22, "white"),  # Upper legs
            (0.15, "yellow"),  # Knees
            (0.06, "white"),  # Lower legs
            (0.00, "red"),  # Feet
        ]

        for mesh in self.current_actor.findAllMatches("**/+GeomNode"):
            bounds = mesh.getTightBounds()
            if not bounds:
                mesh.setMaterial(mats["white"], 1)
                continue

            height_pct = ((bounds[0].z + bounds[1].z) / 2 - 0.1) / 23.4
            for threshold, mat_name in zones:
                if height_pct > threshold:
                    mesh.setMaterial(mats[mat_name], 1)
                    break

    def set_animation(self, name: str):
        if name == self.current_animation or name not in self.animation_files:
            return

        if self.current_actor:
            self.current_actor.cleanup()
            self.current_actor.removeNode()

        try:
            self.current_actor = Actor(str(self.animation_files[name]))
            self.current_actor.reparentTo(self)
            self.current_animation = name
            anim_names = self.current_actor.getAnimNames()
            if anim_names:
                self.current_actor.loop(anim_names[0])
            self._apply_colors()
        except Exception as e:
            print(f"Error loading animation '{name}': {e}")


def main():
    app = Ursina(title="Project Atom", fullscreen=True, borderless=True)
    window.color = UIColors.BACKGROUND
    window.fps_counter.enabled = False  # Disable FPS counter
    window.exit_button.visible = False  # Hide exit button

    robot = AnimatedRobot(position=(0, 0, 0), scale=18)
    camera.position = (0, 5, -18)
    camera.rotation_x = 10

    # Lighting
    DirectionalLight().look_at((1, -1, 1))
    AmbientLight(color=color.rgb(60, 60, 80))

    # Arena floor - flat circular platform
    Entity(
        model="circle",
        scale=18,
        position=(0, -0.1, 0),
        rotation_x=90,
        color=color.rgb(35, 40, 50),
    )

    # Inner ring
    Entity(
        model="circle",
        scale=14,
        position=(0, -0.05, 0),
        rotation_x=90,
        color=color.rgb(50, 55, 65),
    )

    # Center highlight
    Entity(
        model="circle",
        scale=8,
        position=(0, 0, 0),
        rotation_x=90,
        color=color.rgb(60, 65, 75),
    )

    # Webcam panel setup
    webcam_size = (426, 240)
    webcam_tex = P3DTexture("webcam")
    webcam_tex.setup2dTexture(
        *webcam_size, P3DTexture.T_unsigned_byte, P3DTexture.F_rgb8
    )
    webcam_tex.setWrapU(P3DTexture.WM_clamp)
    webcam_tex.setWrapV(P3DTexture.WM_clamp)

    panel_height = 0.22
    panel_width = panel_height * (webcam_size[0] / webcam_size[1])
    margin = 0.02
    pos = (
        window.aspect_ratio * 0.5 - panel_width / 2 - margin,
        -0.5 + panel_height / 2 + margin,
    )

    webcam_panel = Entity(
        parent=camera.ui,
        model="quad",
        scale=(panel_width, panel_height),
        position=pos,
        color=color.white,
    )
    webcam_panel.setTexture(webcam_tex)
    Entity(
        parent=camera.ui,
        model="quad",
        scale=(panel_width + 0.01, panel_height + 0.01),
        position=pos,
        color=UIColors.PANEL_BORDER,
        z=0.01,
    )

    # Initialize gesture UI
    gesture_ui = GestureUI()

    # Camera error text (hidden by default)
    camera_error_text = Text(
        text="Camera not available",
        position=(0, 0),
        origin=(0, 0),
        scale=1.2,
        color=UIColors.ACCENT_RED,
        enabled=False,
    )

    gesture_controller = GestureController()
    camera_ok = gesture_controller.start()
    if not camera_ok:
        camera_error_text.enabled = True

    # Track current gesture state for UI updates
    current_gesture_state = {
        "pose": "idle",
        "left_gesture": "none",
        "right_gesture": "none",
        "confidence": 0.0,
    }

    class GameController(Entity):
        def __init__(self):
            super().__init__()
            self.last_animation = "idle"

        def update(self):
            nonlocal current_gesture_state

            # Get gesture data (includes pose, gestures, and confidence)
            gesture_data = gesture_controller.get_latest_gesture_data()
            if gesture_data:
                current_gesture_state = gesture_data
                pose = gesture_data["pose"]

                if pose != self.last_animation:
                    robot.set_animation(pose)
                    self.last_animation = pose

            # Update UI with current state
            gesture_ui.update(
                action=current_gesture_state["pose"],
                left_gesture=current_gesture_state["left_gesture"],
                right_gesture=current_gesture_state["right_gesture"],
                confidence=current_gesture_state["confidence"],
            )

            # Update webcam display
            frame = gesture_controller.get_latest_frame()
            if frame is not None:
                frame = cv2.resize(frame, webcam_size)
                frame = cv2.flip(frame, 0)
                webcam_tex.setRamImage(frame.tobytes())

            robot.rotation_y += 10 * time.dt

        def input(self, key):
            nonlocal current_gesture_state

            if key == "escape":
                gesture_controller.stop()
                application.quit()

            # Keyboard shortcuts for testing
            animations = {
                "1": "idle",
                "2": "dance",
                "3": "punch_left",
                "4": "punch_right",
                "5": "kick_left",
                "6": "kick_right",
                "7": "boxing",
            }
            if key in animations:
                pose = animations[key]
                robot.set_animation(pose)
                self.last_animation = pose
                # Update UI for keyboard input
                current_gesture_state = {
                    "pose": pose,
                    "left_gesture": "none",
                    "right_gesture": "none",
                    "confidence": 1.0,
                }

    GameController()
    app.run()


if __name__ == "__main__":
    main()
