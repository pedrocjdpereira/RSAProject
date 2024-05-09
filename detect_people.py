import cv2
import torch

model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)  # Load standard YOLOv5 model
#json with data
data = {}


def determine_posture(y1,sitting_limit):
    # Calculate the y-coordinate of the middle point of the bounding box
    if y1 > sitting_limit:
        print("y1 value:",y1)
        return "seated"
    else:
        print("y1 value:",y1)
        return "standing"
    


def getSeats(video_path,sitting_limit):
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        standing_count = 0
        seated_count = 0
        seats_avaialble=8

        # Use YOLO to detect objects
        results = model(frame)

        # Process each detection
        for *xyxy, conf, cls in results.xyxy[0]:
            if results.names[int(cls)] == 'person':
                x1, y1, x2, y2 = map(int, xyxy)
                posture = determine_posture(y1, sitting_limit)
                color = (0, 0, 255) if posture == "standing" else (0, 255, 0)
                if posture == "standing":
                    standing_count += 1
                else:
                    seated_count += 1
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        cv2.line(frame, (0, sitting_limit), (frame.shape[1], sitting_limit), (255, 0, 0), 2)

        # Display the frame and return the data in JSON format
        json_data = {
            "standing": standing_count,
            "seated": seated_count,
            "seats_available": seats_avaialble-standing_count-seated_count
        }
        data.update(json_data)
        cv2.imshow('Video', frame)
        print(f"Current frame - Standing: {standing_count}, Seated: {seated_count},Seats Available: {seats_avaialble-standing_count-seated_count}")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    import sys
    video_path = sys.argv[1] if len(sys.argv) > 1 else 'path/to/video.mp4'
    sitting_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    main(video_path,sitting_limit)
