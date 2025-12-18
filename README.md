# Project Atom - AI-Powered 3D Robot Controller

A real-time gesture-controlled 3D robot inspired by the movie Real Steel. Control an animated robot using hand gestures captured via webcam, powered by machine learning.

![Project Atom Demo](project-atom.png)

## Overview

Project Atom uses computer vision and machine learning to detect hand gestures in real-time and translate them into robot animations. Make a fist to punch, open your palm to kick, or combine gestures for boxing and dancing moves.

**Key Features:**
- Real-time hand tracking using MediaPipe/TensorFlow
- 3D robot rendering with Ursina/Panda3D game engine
- Mixamo character animations (punch, kick, dance, boxing)
- Multi-threaded architecture for smooth 30+ FPS performance
- Live webcam feed with hand landmark visualization

## Gesture Controls

| Gesture | Action |
|---------|--------|
| Left Fist | Punch Left |
| Right Fist | Punch Right |
| Both Fists | Boxing |
| Left Palm Open | Kick Left |
| Right Palm Open | Kick Right |
| Both Palms Open | Dance |

## Architecture

```
Webcam → OpenCV → MediaPipe → Gesture Detection → Ursina/Panda3D → Robot GLB (Mixamo)
```

The application runs on two parallel threads:
- **ML Thread**: Captures webcam frames, runs hand tracking inference, and detects gestures
- **Render Thread**: Renders the 3D robot and updates animations based on detected gestures

Lock-free queues connect the threads, ensuring minimal latency between gesture detection and robot response.

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Python | Core programming language |
| MediaPipe/TensorFlow | ML hand tracking (21 landmarks per hand) |
| OpenCV | Webcam capture and image processing |
| Ursina/Panda3D | 3D game engine and rendering |
| Sketchfab | 3D robot model source |
| Mixamo | Character animation rigging |

## Project Structure

```
project-atom/
├── src/
│   ├── main_3d.py          # Main application entry point
│   ├── camera/
│   │   └── capture.py      # Webcam capture module
│   └── tracking/
│       ├── hands.py        # MediaPipe hand tracking wrapper
│       └── gestures.py     # Gesture detection logic
├── assets/
│   └── models/             # GLB robot animation files
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.9+
- Webcam
- macOS / Windows / Linux

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sgan0420/project-atom.git
   cd project-atom
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
python src/main_3d.py
```

The application will open in fullscreen mode. Allow webcam access when prompted.

**Controls:**
- **Hand gestures**: Control the robot (see gesture table above)
- **Number keys 1-7**: Manually trigger animations
- **ESC**: Exit the application

## How It Works

### Hand Tracking
MediaPipe detects 21 landmarks on each hand. The gesture detector analyzes finger positions by comparing fingertip Y-coordinates with the PIP (middle knuckle) joints:
- **Fist**: All fingertips below their PIP joints (fingers curled)
- **Open Palm**: All fingertips above their PIP joints (fingers extended)

### Threading Model
```
┌─────────────────────────────┐     ┌─────────────────────────────┐
│     ML Thread (Background)  │     │    Render Thread (Main)     │
│                             │     │                             │
│  1. Capture webcam frame    │     │  1. Get pose from queue     │
│  2. Run MediaPipe inference │     │  2. Update robot animation  │
│  3. Detect gesture          │     │  3. Get frame from queue    │
│  4. Put pose in queue ──────┼────►│  4. Update webcam display   │
│  5. Put frame in queue ─────┼────►│  5. Render 3D scene         │
│                             │     │                             │
└─────────────────────────────┘     └─────────────────────────────┘
```

## License

MIT License

## Acknowledgments

- Robot model from [Sketchfab](https://sketchfab.com)
- Character animations from [Mixamo](https://mixamo.com)
- Inspired by the movie Real Steel (2011)
