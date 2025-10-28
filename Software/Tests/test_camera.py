# Software/Tests/test_camera.py
"""
Camera test using the CameraFactory abstraction.

This script validates the entire configuration and factory chain:
  - The correct driver is selected via CameraFactory
  - The CameraInterface contract is respected
  - Frames can be streamed and captured without direct driver knowledge

The test is fully hardware-agnostic.
It will automatically use the backend defined in:
    Software/Config/camera_factory.py
"""

import time
from pathlib import Path

from Software.Config import CameraFactory


def main() -> None:
    print("🔍 [Camera Test - Factory Mode] Starting...")

    # ------------------------------------------------------------------
    # 1. Create the camera via the Factory (App knows nothing else)
    # ------------------------------------------------------------------
    cam = CameraFactory.create()
    print(f"✅ Camera instance created: {type(cam).__name__}")

    try:
        # ------------------------------------------------------------------
        # 2. Open and start streaming
        # ------------------------------------------------------------------
        cam.open()
        cam.start_stream()
        print("🎥 Streaming started...")

        # ------------------------------------------------------------------
        # 3. Capture multiple frames to verify streaming
        # ------------------------------------------------------------------
        frame_count = 0
        t_start = time.monotonic()

        for _ in range(30):
            frame = cam.read(timeout=2.0)
            frame_count += 1

        elapsed = time.monotonic() - t_start
        fps_measured = frame_count / elapsed
        print(f"📸 Captured {frame_count} frames in {elapsed:.2f}s → {fps_measured:.1f} FPS")

        # ------------------------------------------------------------------
        # 4. Take a still image (photo)
        # ------------------------------------------------------------------
        output_dir = Path(__file__).parent
        snapshot_path = output_dir / "test_capture_factory.jpg"

        frame = cam.capture(str(snapshot_path))
        print(f"🖼️ Still image saved at: {snapshot_path.resolve()}")
        print(f"   Resolution: {frame.width}x{frame.height}, Format: {frame.pixel_format}")

        # ------------------------------------------------------------------
        # 5. Stop and close
        # ------------------------------------------------------------------
        cam.stop_stream()
        print("🛑 Streaming stopped.")

    except Exception as e:
        print(f"❌ Error during camera test: {e}")

    finally:
        cam.close()
        print("🔒 Camera closed.")


if __name__ == "__main__":
    main()
