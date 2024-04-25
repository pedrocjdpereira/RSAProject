import cv2
import torch
import mediapipe as mp

# Initialize MediaPipe Pose.
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False, model_complexity=1, enable_segmentation=False, min_detection_confidence=0.5)

# Load YOLO model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

def classify_posture(landmarks, image_height):
    # Assuming left side keypoints; adjust as necessary for accuracy.
    hip_y = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y * image_height
    knee_y = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y * image_height
    # Simple heuristic: if the hip is above the knee, consider the person standing.
    return "seated" if hip_y >= knee_y else "standing"

def process_frame(frame):
    # Convert frame to RGB for MediaPipe
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # Detect poses
    results = pose.process(frame_rgb)
    return results

def main(video_path):
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        standing_count = 0  # Reset counts for each frame
        seated_count = 0

        # Use YOLO to detect people
        results = model(frame)

        # Process each detection
        for *xyxy, conf, cls in results.xyxy[0]:
            if results.names[int(cls)] == 'person':
                x1, y1, x2, y2 = map(int, xyxy)
                # Crop the person subimage
                person_img = frame[y1:y2, x1:x2]
                # Analyze posture with MediaPipe
                mp_results = process_frame(person_img)
                if mp_results.pose_landmarks:
                    posture = classify_posture(mp_results.pose_landmarks.landmark, person_img.shape[0])
                    color = (0, 255, 0) if posture == "standing" else (0, 0, 255)
                    if posture == "standing":
                        standing_count += 1
                    else:
                        seated_count += 1
                else:
                    color = (128, 128, 128)  # Default color if no posture detected
                # Draw bounding box around the person
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Display the frame
        cv2.imshow('Video', frame)
        # Print the counts for the current frame
        print(f"Current frame - Standing: {standing_count}, Seated: {seated_count}")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import sys
    video_path = sys.argv[1] if len(sys.argv) > 1 else 'path/to/video.mp4'
    main(video_path)
