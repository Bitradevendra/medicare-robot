# medicare-robot

`medicare-robot` is a two-part robotics project with a Raspberry Pi controller and a laptop-side detection server.

## Overview

The Raspberry Pi side manages voice interaction, movement, servo control, and streaming, while the laptop side performs live vision detection on the incoming video feed.

## Project Structure

```text
medicare-robot/
|-- laptop_server/
|   |-- detection_server.py
|   |-- config.py
|   `-- requirements.txt
|-- raspberry_pi/
|   |-- main.py
|   |-- gemini_handler.py
|   |-- motor_controller.py
|   |-- video_streamer.py
|   `-- requirements.txt
`-- README.md
```

## Requirements

- Python 3.8+
- Raspberry Pi hardware for the robot side
- laptop or PC for the detection server
- camera, motors, servo hardware, and GPIO wiring

## Installation

Laptop side:

```bash
cd laptop_server
pip install -r requirements.txt
```

Raspberry Pi side:

```bash
cd raspberry_pi
pip install -r requirements.txt
```

## Running The Project

On Raspberry Pi:

```bash
cd raspberry_pi
python main.py
```

On laptop:

```bash
cd laptop_server
python detection_server.py
```

## How It Works

- the Pi listens for commands and controls motors, servo movement, audio output, and streaming
- the laptop server receives the video feed and runs YOLO and MediaPipe detection
- the system combines robot control and real-time monitoring into one workflow
