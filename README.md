# medicare-robot

`medicare-robot` is a two-part robotics project with a Raspberry Pi controller and a laptop-side detection server.

## Install

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

## Use

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

- the Pi handles voice, movement, servo control, AI conversation, and video streaming
- the laptop server receives the stream and runs YOLO and MediaPipe detection
