import cv2
import torch
import os
import time

class PeopleDetector:
    def __init__(self, path_to_video, sitting_param) -> None:
        self.video_path = path_to_video
        self.sitting_limit = int(sitting_param)
        self.model = torch.hub.load('yolov5', 'custom', 'yolov5/yolov5s.pt', source='local')
        self.vid_capt_ready = False
        self.last_frame = None
        #json with data
        self.data = {}

    def determine_posture(self,y1,sitting_limit):
        # Calculate the y-coordinate of the middle point of the bounding box
        if y1 > sitting_limit:
            #print("y1 value:",y1)
            return "seated"
        else:
            #print("y1 value:",y1)
            return "standing"
        
    def signal_handler(signal, frame):
        # Handle Ctrl+C
        print("Ctrl+C detected. Exiting...")
        os._exit(0)  # Terminate the program forcefully
        
    def getData(self):
        return self.data
    
    def discardFrames(self): 
        cap = cv2.VideoCapture(self.video_path)

        self.vid_capt_ready = True

        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        print(f"Processing {frames} frames") 

        while True:
            try:
                success, frame = cap.read()
            except Exception as e:
                print(f"ERROR Reading frame: {e}")
            if success:
                print("discard frame")
                self.last_frame = frame
            else:
                break

        cap.release()

    def getSeats(self):
        while not self.vid_capt_ready:
            time.sleep(1)
            
        i = 0
        while True:
            i += 1
            frame = self.last_frame

            standing_count = 0
            seated_count = 0
            seats_available=8

            # Use YOLO to detect objects
            results = self.model(frame)

            # Process each detection
            for *xyxy, conf, cls in results.xyxy[0]:
                if results.names[int(cls)] == 'person':
                    x1, y1, x2, y2 = map(int, xyxy)
                    posture = self.determine_posture(y1, self.sitting_limit)
                    color = (0, 0, 255) if posture == "standing" else (0, 255, 0)
                    if posture == "standing":
                        standing_count += 1
                    else:
                        seated_count += 1
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            cv2.line(frame, (0, self.sitting_limit), (frame.shape[1], self.sitting_limit), (255, 0, 0), 2)

            # Display the frame and return the data in JSON format
            json_data = {
                "standing": standing_count,
                "seated": seated_count,
                "seats_available": seats_available-seated_count
            }
            self.data.update(json_data)
            #cv2.imshow('Video', frame)
            print(f"Current frame {i} - Standing: {standing_count}, Seated: {seated_count},Seats Available: {seats_available-seated_count}")

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("waitKey")
                break
        
        cv2.destroyAllWindows()

    def getSeatsVideo(self):
        while True:
            cap = cv2.VideoCapture(self.video_path)

            frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            print(f"Processing {frames} frames")
            i = 0
            while True:
                i += 1
                ret, frame = cap.read()
                if not ret:
                    print("no frames")
                    break

                standing_count = 0
                seated_count = 0
                seats_avaialble=8

                # Use YOLO to detect objects
                results = self.model(frame)

                # Process each detection
                for *xyxy, conf, cls in results.xyxy[0]:
                    if results.names[int(cls)] == 'person':
                        x1, y1, x2, y2 = map(int, xyxy)
                        posture = self.determine_posture(y1, self.sitting_limit)
                        color = (0, 0, 255) if posture == "standing" else (0, 255, 0)
                        if posture == "standing":
                            standing_count += 1
                        else:
                            seated_count += 1
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                cv2.line(frame, (0, self.sitting_limit), (frame.shape[1], self.sitting_limit), (255, 0, 0), 2)

                # Display the frame and return the data in JSON format
                json_data = {
                    "standing": standing_count,
                    "seated": seated_count,
                    "seats_available": seats_avaialble-standing_count-seated_count
                }
                self.data.update(json_data)
                #cv2.imshow('Video', frame)
                print(f"Current frame {i} - Standing: {standing_count}, Seated: {seated_count},Seats Available: {seats_avaialble-seated_count}")

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print("waitKey")
                    break
            
            print("Restarting video...")
            cap.release()
            cv2.destroyAllWindows()
