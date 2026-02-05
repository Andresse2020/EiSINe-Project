# Raspberry Pi License Plate Detection System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)](https://opencv.org/)
[![YOLO](https://img.shields.io/badge/YOLO-v8-red.svg)](https://github.com/ultralytics/ultralytics)
[![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)](LICENSE)

Real-time license plate detection system for Raspberry Pi with camera support. Detects license plates using YOLO, designed with a clean layered architecture for easy maintenance and hardware portability.

---

## 📑 Table of Contents

- [Project Overview](#-project-overview)
- [Current Status](#-current-status)
- [Architecture](#️-architecture)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Configuration](#️-configuration)
- [Usage](#-usage)
- [Key Components](#-key-components-explained)
- [Development Guidelines](#️-development-guidelines)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Requirements](#-requirements-summary)
- [Roadmap](#️-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Project Overview

This system captures video frames from a camera, detects license plates in real-time using YOLO object detection, and provides a foundation for future OCR integration. The architecture is designed to run identically on both **PC (development)** and **Raspberry Pi (production)** by simply changing a configuration parameter.

### Key Features

- **Real-time detection**: YOLO-based license plate detection with confidence scoring
- **Hardware abstraction**: Same code runs on PC and Raspberry Pi
- **Multi-driver support**: Easy camera backend switching via factory pattern
- **Thread-safe processing**: Concurrent frame capture and analysis
- **Headless compatible**: No display required for production deployment
- **Modular architecture**: Clean separation of concerns across layers

---

## ✅ Current Status

### Implemented

- ✅ **License plate detection** (YOLO-based object detection)
- ✅ **Multi-driver camera abstraction** (OpenCV implemented, Picamera2 ready)
- ✅ **Service-oriented architecture** (Service → Control → App)
- ✅ **Thread-safe frame processing pipeline**
- ✅ **Bounding box visualization** with confidence scores
- ✅ **Frame buffering service** for non-blocking capture
- ✅ **ROI extraction service** (foundation for plate cropping)
- ✅ **Preprocessing service** (image enhancement pipeline)

### Not Yet Implemented

- ⏳ **OCR** (Optical Character Recognition for reading plate text)
- ⏳ **Plate extraction refinement** (precise plate cropping)
- ⏳ **Database/logging system** (result persistence)
- ⏳ **Web interface** (remote monitoring dashboard)
- ⏳ **Picamera2 driver** (native Raspberry Pi Camera Module support)

---

## 🏗️ Architecture

### Layered Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           APP LAYER                                 │
│                           main.py                                   │
│               (User interface, display logic, entry point)          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                         CONTROL LAYER                               │
│                        lpd_control.py                               │
│          (Pipeline orchestration, threading, business workflow)     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                         SERVICE LAYER                               │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  Camera Service  │  │ YOLO Detector    │  │  Preprocess      │   │
│  │  (Frame buffer)  │  │ Service          │  │  Service         │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘   │
│  ┌──────────────────┐  ┌──────────────────┐                         │
│  │ ROI Extraction   │  │  OCR Service     │                         │
│  │ Service          │  │  (Future)        │                         │
│  └──────────────────┘  └──────────────────┘                         │
│         (Reusable components: ML, image processing, I/O)            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                       INTERFACE LAYER                               │
│                    camera_interface.py (ABC)                        │
│          (Abstract contract defining camera driver behavior)        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
               ┌─────────────┴─────────────┐
               │                           │
 ┌─────────────▼──────────┐    ┌───────────▼──────────┐
 │   DRIVER LAYER         │    │   DRIVER LAYER       │
 │  opencv_camera.py      │    │  picamera2_camera.py │
 │  (USB/CSI via V4L2)    │    │  (Pi CSI - Future)   │
 │  Cross-platform        │    │  Native Raspberry Pi │
 └────────────────────────┘    └──────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         CONFIG LAYER                                │
│                      camera_factory.py                              │
│          (Runtime driver selection and instantiation)               │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow Pipeline

```
┌──────────────┐   ┌────────────────┐   ┌────────────────┐   ┌──────────┐
│   Camera     │──▶│    Camera      │──▶│      LPD       │──▶│   App    │
│   Driver     │   │    Service     │   │    Control     │   │  Layer   │
└──────────────┘   └────────────────┘   └────────────────┘   └──────────┘
      │                   │                     │                   │
  Hardware           Frame Buffer          YOLO Pipeline        Display
  Capture            (Thread-safe)         • Detection           Results
  (cv2.read)         • Latest frame        • ROI Extract
                     • Non-blocking        • Preprocess
                                          • Overlay
```

**Detailed Flow:**

1. **Camera Driver** (`opencv_camera.py`)
   - Captures raw frames from hardware via OpenCV
   - Returns normalized `Frame` objects

2. **Camera Service** (`camera_service.py`)
   - Runs background thread for continuous capture
   - Buffers latest frame in thread-safe manner
   - Converts `Frame` → `ImageFrame` for upper layers

3. **LPD Control** (`lpd_control.py`)
   - Pulls frames from Camera Service (non-blocking)
   - Runs detection pipeline:
     - YOLO detection → bounding boxes + confidence
     - ROI extraction (optional plate cropping)
     - Preprocessing (optional image enhancement)
     - Debug overlay rendering
   - Stores results thread-safely

4. **App Layer** (`main.py`)
   - Retrieves latest detection results
   - Displays frames with overlays
   - Handles user input (quit, pause, etc.)

---

## 📁 Project Structure

```
raspberry-lpd/
│
├── Software/
│   │
│   ├── App/
│   │   └── main.py                          # Application entry point
│   │
│   ├── Control/
│   │   └── lpd_control.py                   # Detection pipeline controller
│   │
│   ├── Service/
│   │   ├── camera_service.py                # Frame buffering service
│   │   ├── yolo_detector_service.py         # YOLO inference wrapper
│   │   ├── roi_extraction_service.py        # Plate region extraction
│   │   ├── plate_preprocess_service.py      # Image preprocessing
│   │   ├── ocr_service.py                   # OCR (placeholder)
│   │   └── ML_Models/
│   │       ├── license_plate_detector.pt    # YOLO weights (required)
│   │       └── yolov8n.pt                   # Optional backup model
│   │
│   ├── Interface/
│   │   └── camera_interface.py              # Abstract camera contract (ABC)
│   │
│   ├── Drivers/
│   │   └── opencv_camera.py                 # OpenCV camera implementation
│   │
│   ├── Config/
│   │   └── camera_factory.py                # Driver selection factory
│   │
│   ├── Tests/
│   │   ├── test_camera.py                   # Driver unit tests
│   │   └── test_camera_service.py           # Service layer tests
│   │
│   └── Tools/
│       └── debug_display.py                 # Debugging utilities
│
├── launch.sh                                # Startup script (source to load aliases)
├── setup.py                                 # Package configuration
└── README.md                                # This file
```

### Directory Responsibilities

| Directory | Purpose |
|-----------|---------|
| `App/` | User-facing application logic, entry points |
| `Control/` | Business workflows, pipeline orchestration |
| `Service/` | Reusable components (ML models, image processing, I/O) |
| `Interface/` | Abstract contracts for hardware abstraction |
| `Drivers/` | Concrete hardware implementations |
| `Config/` | Configuration files, factory patterns |
| `Tests/` | Unit and integration tests |
| `Tools/` | Development and debugging utilities |

---

## 🔧 Installation

### Development Environment (PC)

**Supported OS:** Linux, macOS, Windows

```bash
# 1. Clone repository
git clone https://github.com/Andresse2020/EiSINe-Project
cd EiSINe-Project

# 2. Ensure pip is installed
python3 -m ensurepip --upgrade
python3 -m pip install --upgrade pip

# 3. Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\activate           # Windows

# 4. Install dependencies
pip install numpy
pip install opencv-python
pip install ultralytics           # YOLO

# 5. Verify installation
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
python3 -c "import ultralytics; print('YOLO: OK')"
```

### Production Environment (Raspberry Pi)

**Tested on:** Raspberry Pi OS (Bullseye/Bookworm)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install system dependencies
sudo apt install -y python3-opencv python3-pip

# 3. Install Python packages
pip3 install ultralytics numpy

# Optional: Enable Raspberry Pi Camera Module (CSI)
sudo apt install -y python3-picamera2

# 4. Clone repository
git clone https://github.com/Andresse2020/EiSINe-Project
cd EiSINe-Project

# 5. Verify installation
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
```

### YOLO Model Setup

The system requires a trained YOLO model for license plate detection:

```bash
# Ensure the model file exists at:
Software/Service/ML_Models/license_plate_detector.pt

# If you need to train your own model, see:
# https://docs.ultralytics.com/modes/train/
```

---

## ⚙️ Configuration

### Camera Driver Selection

The **only** configuration needed to switch between PC and Raspberry Pi is in `Software/Config/camera_factory.py`:

```python
# ============================================================
# GLOBAL HARDWARE CONFIGURATION
# ============================================================

# Select active camera driver
# Options:
#   - "Software.Drivers.opencv_camera.OpenCVCamera"       (USB, V4L2)
#   - "Software.Drivers.picamera2_camera.Picamera2Camera" (Pi CSI - future)
ACTIVE_CAMERA_DRIVER = "Software.Drivers.opencv_camera.OpenCVCamera"

# Hardware parameters
CAMERA_HARDWARE_CONFIG = {
    "device_index": 0,                    # /dev/video0 (Linux) or index 0
    "default_resolution": (640, 480),     # Lower for Raspberry Pi performance
    "default_framerate": 30.0,            # FPS target
}
```

### Configuration Examples

#### For PC Development (USB Camera)
```python
ACTIVE_CAMERA_DRIVER = "Software.Drivers.opencv_camera.OpenCVCamera"
CAMERA_HARDWARE_CONFIG = {
    "device_index": 0,              # First USB camera
    "default_resolution": (1280, 720),
    "default_framerate": 30.0,
}
```

#### For Raspberry Pi (USB Camera)
```python
ACTIVE_CAMERA_DRIVER = "Software.Drivers.opencv_camera.OpenCVCamera"
CAMERA_HARDWARE_CONFIG = {
    "device_index": 0,              # /dev/video0
    "default_resolution": (640, 480),  # Lower resolution for performance
    "default_framerate": 15.0,         # Reduced FPS
}
```

#### For Raspberry Pi (CSI Camera - Future)
```python
ACTIVE_CAMERA_DRIVER = "Software.Drivers.picamera2_camera.Picamera2Camera"
CAMERA_HARDWARE_CONFIG = {
    "device_index": 0,
    "default_resolution": (1640, 1232),
    "default_framerate": 30.0,
}
```

---

## 🚀 Usage

### Basic Operation

```bash
# Method 1: Using launch script (loads aliases)
cd EiSINe-Project/Software
source launch.sh     # Once the launch.sh file is succefuly executed, you can run "run_app" and "show_video" in any directory.
run_app              # Launch main detection application
show_video           # Launch debug video display tool

# Method 2: Direct Python execution
cd EiSINe-Project
python3 -m Software.App.main
python3 -m Software.Tools.debug_display

# Method 3: From project root
cd EiSINe-Project
python3 -m Software.App.main
```

### Launch Script Details

The `launch.sh` script provides convenient aliases:

```bash
#!/bin/bash
# Load aliases into current shell
cd EiSINe-Project/Software
source launch.sh

# Available commands:
run_app      # Runs the license plate detection system
show_video   # Runs the debug video display utility
```

**Important:** Use `source launch.sh` (or `. launch.sh`) instead of `./launch.sh` to load aliases into your current shell session.

### Expected Console Output

```
🔍 [DebugDisplay] Starting viewer...
📡 CameraService started.
🧠 LPDControl started.

...

Press 'q' to quit
```

### Keyboard Controls

| Key | Action |
|-----|--------|
| `q` | Quit application |
| `p` | Pause/Resume detection |
| `s` | Save current frame |

### Running Tests

```bash
# Test camera driver
cd EiSINe-Project/Software
python3 -m Software.Tests.test_camera

# Test camera service
cd EiSINe-Project/Software
python3 -m Software.Tests.test_camera_service
```

---

## 🔍 Key Components Explained

### 1. `camera_interface.py` (Interface Layer)

**Purpose:** Defines the abstract contract that all camera drivers must implement.

**Key Methods:**
- `open(config)` — Initialize camera hardware
- `close()` — Release camera resources
- `start_stream()` — Begin continuous capture
- `stop_stream()` — End continuous capture
- `read(timeout)` — Capture a single frame
- `set_config(config)` — Apply camera settings (resolution, FPS, etc.)
- `capabilities()` — Query backend features

**Why it matters:** Upper layers only depend on this interface, never on concrete drivers.

---

### 2. `opencv_camera.py` (Driver Layer)

**Purpose:** Concrete implementation using OpenCV's `cv2.VideoCapture`.

**Features:**
- Works with USB cameras via V4L2 (Linux)
- Cross-platform support (Windows, macOS, Linux)
- Implements full `CameraInterface` contract
- Thread-safe frame acquisition

**Example Usage:**
```python
from Software.Drivers.opencv_camera import OpenCVCamera

cam = OpenCVCamera(device_index=0)
cam.open()
cam.start_stream()
frame = cam.read()  # Returns Frame object
cam.stop_stream()
cam.close()
```

---

### 3. `camera_service.py` (Service Layer)

**Purpose:** Provides thread-safe frame buffering with non-blocking access.

**Features:**
- Background thread continuously captures frames
- Stores latest frame in locked buffer
- Converts `Frame` → `ImageFrame` (simplified data structure)
- Non-blocking `get_latest()` method

**Why it matters:** Decouples frame capture from processing, preventing pipeline blocking.

**Example Usage:**
```python
from Software.Service.camera_service import CameraService

service = CameraService(camera_driver)
service.start()

# Non-blocking access
latest = service.get_latest()  # Returns ImageFrame or None
```

---

### 4. `yolo_detector_service.py` (Service Layer)

**Purpose:** Wraps YOLO model for license plate detection.

**Features:**
- Loads YOLO model from `.pt` file
- Runs inference on images
- Returns bounding boxes sorted by confidence

**Example Usage:**
```python
from Software.Service.yolo_detector_service import YoloDetectorService

detector = YoloDetectorService("path/to/model.pt")
detections = detector.detect(image)  # Returns [(x, y, w, h, conf), ...]
```

---

### 5. `lpd_control.py` (Control Layer)

**Purpose:** Orchestrates the complete detection pipeline.

**Pipeline Steps:**
1. Pull frame from Camera Service
2. Run YOLO detection
3. Extract ROI (optional)
4. Preprocess plate image (optional)
5. Draw debug overlay
6. Store results thread-safely

**Features:**
- Runs in background thread
- Thread-safe result storage
- Configurable processing steps

**Example Usage:**
```python
from Software.Control.lpd_control import LPDControl

controller = LPDControl(camera_service)
controller.start()

# Retrieve latest detection
result = controller.get_latest_result()  # { "bbox": (x,y,w,h), "confidence": 0.89, ... }
frame = controller.get_latest_frame()    # Processed frame with overlay
```

---

### 6. `camera_factory.py` (Config Layer)

**Purpose:** Centralized factory for driver instantiation.

**How it works:**
1. Reads `ACTIVE_CAMERA_DRIVER` from config
2. Dynamically imports driver class
3. Instantiates with `CAMERA_HARDWARE_CONFIG`
4. Validates implementation at runtime

**Example Usage:**
```python
from Software.Config.camera_factory import CameraFactory

# Returns concrete driver based on config
camera = CameraFactory.create()  # Returns OpenCVCamera or Picamera2Camera

# Upper layers only see CameraInterface
camera.open()
camera.start_stream()
```

**Why it matters:** Single source of truth for hardware selection. No conditional imports scattered across codebase.

---

## 🛠️ Development Guidelines

### Architecture Rules

1. **Never import drivers directly** — Always use `CameraFactory`
2. **Respect layer boundaries:**
   - App → Control → Service → Interface → Driver
   - Lower layers never import from upper layers
3. **Keep services stateless** or thread-safe
4. **No hardware logic** in Control/Service layers

### Adding a New Camera Driver

**Steps:**

1. Create `Software/Drivers/my_camera.py`
2. Inherit from `CameraInterface`
3. Implement all abstract methods
4. Update `camera_factory.py`
5. Write tests

**Example Template:**

```python
from Software.Interface.camera_interface import (
    CameraInterface,
    CameraConfig,
    Frame,
    CameraOpenError,
)

class MyCamera(CameraInterface):
    def __init__(self, device_index=0, **kwargs):
        super().__init__()
        self._device = device_index
        self._name = "MyCamera"

    def open(self, config=None):
        # Initialize hardware
        self._is_open = True

    def close(self):
        # Release hardware
        self._is_open = False

    def start_stream(self):
        self._is_streaming = True

    def stop_stream(self):
        self._is_streaming = False

    def read(self, timeout=2.0):
        # Capture and return Frame
        pass

    def flush(self):
        pass

    def capture(self, path=None):
        pass

    def set_config(self, config):
        pass

    def capabilities(self):
        return {}
```

### Adding a New Service

**Guidelines:**

1. Create `Software/Service/my_service.py`
2. Keep it stateless or use locks for thread safety
3. No direct hardware access (use existing services)
4. Write unit tests in `Software/Tests/`

**Example:**

```python
class MyService:
    def __init__(self):
        # Initialize resources
        pass

    def process(self, data):
        # Stateless processing
        return result
```

---

## 🧪 Testing

### Running Tests

```bash
# Run all tests
python3 -m pytest Software/Tests/ -v

# Run specific test file
python3 -m pytest Software/Tests/test_camera.py -v

# Run with coverage
pip install pytest-cov
python3 -m pytest Software/Tests/ --cov=Software --cov-report=html
```

### Manual Testing

```bash
# Test camera access
python3 -c "from Software.Config.camera_factory import CameraFactory; \
            cam = CameraFactory.create(); \
            cam.open(); \
            print('Camera OK')"

# Test YOLO model
python3 -c "from Software.Service.yolo_detector_service import YoloDetectorService; \
            detector = YoloDetectorService('Software/Service/ML_Models/license_plate_detector.pt'); \
            print('Model loaded OK')"
```

---

## 🐛 Troubleshooting

### Camera Not Detected

**Problem:** Camera fails to open

```bash
# Check available video devices
ls /dev/video*

# Test OpenCV access
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Opened:', cap.isOpened())"

# Check permissions
groups  # Should include 'video'
sudo usermod -a -G video $USER  # Add user to video group
# Logout and login again
```

### Low FPS on Raspberry Pi

**Solutions:**

1. **Reduce resolution:**
   ```python
   # In camera_factory.py
   "default_resolution": (320, 240),  # Even lower
   ```

2. **Lower framerate:**
   ```python
   "default_framerate": 10.0,
   ```

3. **Use lighter YOLO model:**
   - Replace `license_plate_detector.pt` with `yolov8n.pt` (nano version)

4. **Disable debug overlays:**
   ```python
   # In lpd_control.py, comment out:
   # self._draw_overlay(processed, x, y, w, h, conf)
   ```

### Permission Denied on `/dev/video0`

```bash
# Add user to video group
sudo usermod -a -G video $USER

# Or run with sudo (not recommended for production)
sudo python3 Software/App/main.py
```

### YOLO Model Not Found

```bash
# Check model path
ls Software/Service/ML_Models/license_plate_detector.pt

# If missing, download or train your own
# See: https://docs.ultralytics.com/
```

### Import Errors

```bash
# Ensure you're in project root
cd raspberry-lpd

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or install as package
pip install -e .
```

---

## 📦 Requirements Summary

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Raspberry Pi | Pi 3B | Pi 4 (4GB+) |
| Camera | USB 2.0 webcam | Pi Camera Module v2/v3 |
| RAM | 1GB | 2GB+ |
| SD Card | 8GB | 16GB+ (Class 10) |
| Power Supply | 2.5A | 3A (official) |

### Software Requirements

**Python:** 3.8 or higher

**Core Dependencies:**
- `opencv-python` (4.x) — Image processing and camera I/O
- `ultralytics` — YOLO object detection
- `numpy` — Numerical operations

**Optional Dependencies:**
- `picamera2` — Raspberry Pi Camera Module support (future)
- `pytest` — Unit testing
- `tesseract` / `easyocr` — OCR (future implementation)

### Operating Systems

| OS | Status |
|----|--------|
| Raspberry Pi OS (Bullseye/Bookworm) | ✅ Fully supported |
| Ubuntu 20.04+ | ✅ Supported |
| Debian 11+ | ✅ Supported |
| macOS | ⚠️ Development only |
| Windows 10+ | ⚠️ Development only |

---

## 🗺️ Roadmap

### Phase 1: Core Detection (Current)
- [x] YOLO-based license plate detection
- [x] OpenCV camera driver
- [x] Layered architecture
- [x] Thread-safe processing pipeline

### Phase 2: OCR Integration
- [ ] Implement OCR service (Tesseract or EasyOCR)
- [ ] Plate text extraction and validation
- [ ] Result confidence scoring
- [ ] Multi-language support

### Phase 3: Hardware Expansion
- [ ] Picamera2 driver for Raspberry Pi Camera Module
- [ ] Multi-camera support
- [ ] Hardware acceleration (Coral TPU, Neural Compute Stick)

### Phase 4: Data Persistence
- [ ] SQLite/PostgreSQL database integration
- [ ] Detection history logging
- [ ] Image archiving system
- [ ] Export to CSV/JSON

### Phase 5: Remote Access
- [ ] REST API (Flask/FastAPI)
- [ ] Web dashboard (React/Vue)
- [ ] Real-time monitoring
- [ ] Mobile app support

### Phase 6: Optimization
- [ ] Performance tuning for Pi Zero
- [ ] Battery power optimization
- [ ] Edge processing (on-device analytics)
- [ ] Docker containerization

### Future Enhancements
- [ ] Vehicle tracking and counting
- [ ] Parking violation detection
- [ ] Integration with access control systems
- [ ] Cloud sync and backup

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. **Follow the architecture:**
   - Respect layer boundaries
   - Use existing abstractions
   - Keep drivers isolated
4. **Write tests:**
   - Unit tests for new services
   - Integration tests for workflows
5. **Update documentation:**
   - Code comments
   - README updates if needed
6. **Submit pull request:**
   - Clear description of changes
   - Reference related issues

### Code Style

- **Python:** Follow PEP 8
- **Imports:** Use absolute imports (`from Software.Service...`)
- **Type hints:** Use where appropriate
- **Docstrings:** Google-style for public APIs

### Architecture Principles

✅ **DO:**
- Use `CameraFactory` for hardware access
- Keep services stateless or thread-safe
- Write unit tests for new components
- Follow layer separation strictly

❌ **DON'T:**
- Import drivers directly in upper layers
- Add hardware logic to Control/Service layers
- Create circular dependencies
- Modify interfaces without updating all implementations

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📞 Contact & Support

### Questions or Issues?

- **GitHub Issues:** [https://github.com/Andresse2020/EiSINe-Project](https://github.com/Andresse2020/EiSINe-Project)
- **Email:** brisel.bassinga@gmail.com
- **Documentation:** See inline code comments and docstrings

### Useful Links

- [Ultralytics YOLO Documentation](https://docs.ultralytics.com/)
- [OpenCV Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [Raspberry Pi Documentation](https://www.raspberrypi.com/documentation/)
- [Picamera2 Manual](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)

---

## 🙏 Acknowledgments

- **Ultralytics** for YOLO implementation
- **OpenCV** community for image processing tools
- **Raspberry Pi Foundation** for accessible hardware

---

## 📝 Notes for Continuators

### Critical Information

1. **Hardware Abstraction:**
   - ALL camera hardware logic is in `Drivers/` directory
   - NEVER modify other layers for hardware changes
   - Use `CameraFactory` exclusively for instantiation

2. **Model Path:**
   - YOLO model path is hardcoded in `yolo_detector_service.py`
   - Update if you move the `ML_Models/` directory

3. **Headless Operation:**
   - System designed for headless deployment
   - No GUI dependencies required
   - Display logic is optional (in `main.py`)

4. **Platform Switching:**
   - To switch between PC and Raspberry Pi: Edit `camera_factory.py` ONLY
   - Everything else remains identical

5. **Thread Safety:**
   - Frame buffer in `CameraService` uses locks
   - Detection results in `LPDControl` use locks
   - Never access shared state without locking

### Quick Start Checklist

- [ ] Install dependencies (see [Installation](#-installation))
- [ ] Place YOLO model in `Software/Service/ML_Models/`
- [ ] Configure camera driver in `camera_factory.py`
- [ ] Test camera access: `ls /dev/video*`
- [ ] Run tests: `pytest Software/Tests/`
- [ ] Load launch script: `source launch.sh`
- [ ] Launch system: `run_app` (or `python3 -m Software.App.main`)

### Launch Script Usage

The `launch.sh` file defines convenient bash aliases but does NOT execute the application directly. Proper usage:

```bash
# ✅ CORRECT: Source the script to load aliases
source launch.sh
# Output: ✅ Launch alias 'run_app and show_video' has been loaded.

# Then use the aliases
run_app         # Launches Software.App.main
show_video      # Launches Software.Tools.debug_display

# ❌ INCORRECT: Running as executable won't load aliases
./launch.sh     # This won't work (aliases only exist in subshell)
```

**Alternative:** You can add `source /path/to/EiSINe-Project/Software/launch.sh` to your `~/.bashrc` to load aliases permanently.

---

**Last Updated:** February 5, 2024  
**Version:** 1.0.0  
**Status:** Active Development

---