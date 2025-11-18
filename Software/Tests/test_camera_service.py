# Software/Tests/test_camera_service.py
"""
Test for the CameraService layer.

This test validates:
  - correct instantiation of the service,
  - background acquisition thread,
  - latest-frame cache functionality,
  - direct still-image capture,
  - clean shutdown of the service.

It does NOT depend on any specific camera driver.
The active driver is selected by CameraFactory.
"""

import time
from pathlib import Path

from Software.Service.camera_service import CameraService


def main() -> None:
    print("🔍 [CameraService Test] Starting...")

    # ------------------------------------------------------------------
    # 1. Create the service
    # ------------------------------------------------------------------
    service = CameraService()
    print("✅ CameraService created")

    try:
        # ------------------------------------------------------------------
        # 2. Start the service (opens camera + starts thread)
        # ------------------------------------------------------------------
        service.start()
        print("🎥 CameraService started")

        # Give some time for the background thread to fetch frames
        time.sleep(0.5)

        # ------------------------------------------------------------------
        # 3. Get the latest frame
        # ------------------------------------------------------------------
        frame = service.get_latest()

        if frame is None:
            raise RuntimeError("No frame retrieved — camera may not be streaming.")

        print(f"📸 Latest frame: {frame.width}x{frame.height} px, {frame.pixel_format}")

        # ------------------------------------------------------------------
        # 4. Test still-image capture
        # ------------------------------------------------------------------
        output_path = Path(__file__).parent / "service_capture.jpg"
        service.capture(str(output_path))

        print(f"🖼️ Still image saved at: {output_path.resolve()}")

        # ------------------------------------------------------------------
        # 5. Validate that the thread is still running
        # ------------------------------------------------------------------
        if not service.is_running():
            raise RuntimeError("Service thread unexpectedly stopped.")

        print("⚙️ Background thread is running correctly")

    except Exception as e:
        print(f"❌ Error during CameraService test: {e}")

    finally:
        # ------------------------------------------------------------------
        # 6. Clean shutdown
        # ------------------------------------------------------------------
        service.stop()
        print("🔒 CameraService stopped cleanly")


if __name__ == "__main__":
    main()
