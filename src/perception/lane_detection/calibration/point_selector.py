import cv2
import numpy as np

def select_perspective_points(video_path):
    """click 4 points in order: BL, BR, TR, TL"""
    cap = cv2.VideoCapture(video_path)
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"Resolution: {width} x {height}\n")
    
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        return None
    
    points = []
    
    def mouse_callback(event, x, y, flags, param):
        nonlocal points
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < 4:
            points.append([x, y])
            print(f"Point {len(points)}: ({x}, {y})")
    
    cv2.namedWindow('Click 4 Points')
    cv2.setMouseCallback('Click 4 Points', mouse_callback)
    
    while len(points) < 4:
        display = frame.copy()
        for pt in points:
            cv2.circle(display, tuple(pt), 8, (0, 255, 0), -1)
        cv2.imshow('Click 4 Points', display)
        cv2.waitKey(1)
    
    cv2.destroyAllWindows()
    return np.float32(points)


if __name__ == "__main__":
    video_path = "/Users/julian/Documents/github/self-driving-project/nl_highway.mp4"
    points = select_perspective_points(video_path)
