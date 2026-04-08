# Medicare Robot

A robotics stack that blends physical movement, medicine-box control, voice interaction, camera streaming, and live laptop-side detection into one cohesive assistant system.

## Why It Grabs Attention

`medicare-robot` feels like a real prototype, not just a folder of scripts. It has a split-brain architecture: the Raspberry Pi handles embodiment, while the laptop handles vision.

## What It Does

- listens for voice commands on the Raspberry Pi
- controls robot motion and servo-driven medicine-box actions
- streams live video from the robot side
- runs laptop-side detection with YOLO and MediaPipe
- supports AI-assisted spoken responses

## Project Structure

```text
medicare-robot/
|-- raspberry_pi/
|   |-- main.py
|   |-- motor_controller.py
|   |-- servo_controller.py
|   |-- voice_controller.py
|   |-- gemini_handler.py
|   `-- video_streamer.py
|-- laptop_server/
|   |-- detection_server.py
|   |-- config.py
|   `-- requirements.txt
`-- README.md
```

## Requirements

- Python 3.8+
- Raspberry Pi hardware for the robot side
- laptop or PC for detection and visualization
- connected motors, servo, microphone, and camera hardware

## Installation

Raspberry Pi side:

```bash
cd raspberry_pi
pip install -r requirements.txt
```

Laptop side:

```bash
cd laptop_server
pip install -r requirements.txt
```

## Run Locally

Start the robot controller:

```bash
cd raspberry_pi
python main.py
```

Start the detection server:

```bash
cd laptop_server
python detection_server.py
```

## How It Works

- the Pi runs the main control loop, interprets commands, and manages hardware actions
- the camera stream is sent outward for monitoring and analysis
- the laptop receives that stream and overlays detections in real time
- together, both halves turn the project into a believable assistive robotics prototype
