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
            for i, landmarks in enumerate(all_landmarks):
                hand_label = handedness[i] if i < len(handedness) else "Unknown"
                gesture = self.detector.detect_gesture(landmarks)
                if hand_label == "Left":
                    left_gesture = gesture
                elif hand_label == "Right":
                    right_gesture = gesture

            # Map gestures to animations (intuitive mappings)
            if left_gesture == "fist" and right_gesture == "fist":
                pose = "boxing"
            elif left_gesture == "open" and right_gesture == "open":
                pose = "dance"
            # Single hand fist = punch that side
            elif left_gesture == "fist":
                pose = "punch_left"
            elif right_gesture == "fist":
                pose = "punch_right"
            # Single hand open = kick that side
            elif left_gesture == "open":
                pose = "kick_left"
            elif right_gesture == "open":
                pose = "kick_right"
            else:
                pose = "idle"

            try:
                self.gesture_queue.put_nowait(pose)
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

    def get_latest_pose(self):
        pose = None
        while not self.gesture_queue.empty():
            try:
                pose = self.gesture_queue.get_nowait()
            except queue.Empty:
                break
        return pose

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
            'idle': MODELS_PATH / 'robot-default.glb',
            'dance': MODELS_PATH / 'robot-dance.glb',
            'punch_left': MODELS_PATH / 'robot-punch-left.glb',
            'punch_right': MODELS_PATH / 'robot-punch-right.glb',
            'kick_left': MODELS_PATH / 'robot-left-kick.glb',
            'kick_right': MODELS_PATH / 'robot-right-kick.glb',
            'boxing': MODELS_PATH / 'robot-boxing.glb',
        }
        self.current_animation = None
        self.current_actor = None
        self._init_materials()
        self.set_animation('idle')

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
            'white': make_material(100, (0.4, 0.4, 0.4), (0.95, 0.95, 0.95), (1.0, 1.0, 1.0)),
            'blue': make_material(120, (0.1, 0.15, 0.4), (0.2, 0.4, 0.95), (0.5, 0.6, 1.0)),
            'red': make_material(120, (0.4, 0.1, 0.1), (0.95, 0.2, 0.15), (1.0, 0.5, 0.5)),
            'yellow': make_material(150, (0.4, 0.35, 0.0), (1.0, 0.85, 0.1), (1.0, 1.0, 0.6)),
            'gray': make_material(80, (0.15, 0.15, 0.15), (0.35, 0.35, 0.4), (0.6, 0.6, 0.6)),
        }

    def _apply_colors(self):
        if not self.current_actor:
            return

        mats = AnimatedRobot.MATERIALS
        # Height zones: 0=feet, 1=head (Z range: 0.1 to 23.5)
        zones = [
            (0.92, 'yellow'),  # Head top
            (0.82, 'white'),   # Head
            (0.72, 'blue'),    # Chest
            (0.58, 'white'),   # Abdomen
            (0.45, 'gray'),    # Waist
            (0.22, 'white'),   # Upper legs
            (0.15, 'yellow'),  # Knees
            (0.06, 'white'),   # Lower legs
            (0.00, 'red'),     # Feet
        ]

        for mesh in self.current_actor.findAllMatches('**/+GeomNode'):
            bounds = mesh.getTightBounds()
            if not bounds:
                mesh.setMaterial(mats['white'], 1)
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
    app = Ursina(title='Project Atom', fullscreen=True, borderless=True)
    window.color = color.rgb(15, 20, 30)

    robot = AnimatedRobot(position=(0, 0, 0), scale=18)
    camera.position = (0, 5, -18)
    camera.rotation_x = 10

    DirectionalLight().look_at((1, -1, 1))
    AmbientLight(color=color.rgb(80, 80, 100))

    # Webcam panel setup
    webcam_size = (426, 240)
    webcam_tex = P3DTexture("webcam")
    webcam_tex.setup2dTexture(*webcam_size, P3DTexture.T_unsigned_byte, P3DTexture.F_rgb8)
    webcam_tex.setWrapU(P3DTexture.WM_clamp)
    webcam_tex.setWrapV(P3DTexture.WM_clamp)

    panel_height = 0.22
    panel_width = panel_height * (webcam_size[0] / webcam_size[1])
    margin = 0.02
    pos = (window.aspect_ratio * 0.5 - panel_width / 2 - margin,
           -0.5 + panel_height / 2 + margin)

    webcam_panel = Entity(parent=camera.ui, model='quad', scale=(panel_width, panel_height),
                          position=pos, color=color.white)
    webcam_panel.setTexture(webcam_tex)
    Entity(parent=camera.ui, model='quad', scale=(panel_width + 0.01, panel_height + 0.01),
           position=pos, color=color.dark_gray, z=0.01)

    status_text = Text(text='Loading...', position=(-0.85, -0.45), origin=(-1, 0),
                       scale=0.8, color=color.rgb(100, 100, 120))

    gesture_controller = GestureController()
    if gesture_controller.start():
        status_text.text = '2 Fists=Box | 2 Palms=Dance | 1 Fist=Punch | 1 Palm=Kick'
    else:
        status_text.text = 'Camera error'
        status_text.color = color.red

    class GameController(Entity):
        def __init__(self):
            super().__init__()
            self.last_animation = 'idle'

        def update(self):
            pose = gesture_controller.get_latest_pose()
            if pose and pose != self.last_animation:
                robot.set_animation(pose)
                self.last_animation = pose

            frame = gesture_controller.get_latest_frame()
            if frame is not None:
                frame = cv2.resize(frame, webcam_size)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.flip(frame, 0)
                webcam_tex.setRamImage(frame.tobytes())

            robot.rotation_y += 10 * time.dt

        def input(self, key):
            if key == 'escape':
                gesture_controller.stop()
                application.quit()
            animations = {'1': 'idle', '2': 'dance', '3': 'punch_left',
                         '4': 'punch_right', '5': 'kick_left', '6': 'kick_right',
                         '7': 'boxing'}
            if key in animations:
                robot.set_animation(animations[key])
                self.last_animation = animations[key]

    GameController()
    app.run()


if __name__ == '__main__':
    main()
