"""
Debug video viewer (development-only).

This tool displays:
    - the raw camera feed,
    - the processed feed (optional, once DetectionService exists).

It must NOT be shipped in production.  
It runs only on desktop systems that support OpenCV windows.

Usage:
    python3 -m Software.Tools.debug_display
"""

from __future__ import annotations
import time
import cv2

from Software.Service import CameraService
# Future:
from Software.Control import LPDControl


def main() -> None:
    print("🔍 [DebugDisplay] Starting viewer...")

    # -----------------------------------------------------------
    # Initialize services
    # -----------------------------------------------------------
    cam_service = CameraService()
    cam_service.start()
    print("📡 CameraService started.")

    det_control = LPDControl(cam_service)
    det_control.start()
    print("🧠 LPDControl started.")

    try:
        while True:

            # ---------------------------------------------------
            # Fetch latest raw frame
            # ---------------------------------------------------
            frame = cam_service.get_latest()
            if frame is not None:
                cv2.imshow("Raw Feed", frame.data)

            # ---------------------------------------------------
            # If detection service exists, show processed frame
            # ---------------------------------------------------
            processed = det_control.get_latest_frame()
            if processed is not None:
                cv2.imshow("Processed Feed", processed)

            # ---------------------------------------------------
            # Handle quitting gracefully
            # ---------------------------------------------------
            key = cv2.waitKey(1)
            if key == ord('q'):
                print("🔚 Exiting viewer...")
                break

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\n🛑 KeyboardInterrupt detected. Stopping viewer...")

    finally:
        print("🛑 Stopping services...")

        # Stop camera service
        cam_service.stop()
        print("🔒 CameraService stopped.")

        # Stop detection (when implemented)
        # det_control.stop()
        # print("🔒 LPDControl stopped.")

        # Close OpenCV windows
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

        print("🪟 All windows closed.")
        print("✔️ Shutdown complete. Bye!")


if __name__ == "__main__":
    main()
