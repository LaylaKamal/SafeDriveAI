"""
Step 2: Camera module
Open camera, read frame, display for testing
"""
import cv2


def open_camera(device_id=0):
    """Open camera and return VideoCapture object"""
    return cv2.VideoCapture(device_id)


def read_frame(cap):
    """Read frame from camera - returns (success, frame)"""
    return cap.read()


def release_camera(cap):
    """Release camera"""
    cap.release()
    cv2.destroyAllWindows()


def run_camera_test():
    """Test run to verify camera works"""
    cap = open_camera(0)
    if not cap.isOpened():
        print("Error: Cannot open camera")
        return

    print("Camera running - Press ESC to exit")
    while True:
        success, frame = read_frame(cap)
        if not success:
            continue
        frame = cv2.flip(frame, 1)
        cv2.imshow("Camera Test", frame)
        if cv2.waitKey(5) & 0xFF == 27:
            break

    release_camera(cap)


if __name__ == "__main__":
    run_camera_test()
