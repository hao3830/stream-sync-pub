import os
import cv2
import shutil
import ntplib
import time

import numpy as np

from multiprocessing import Process, Queue, shared_memory

from argparse import ArgumentParser
from datetime import datetime, timedelta
import signal
import sys

client = ntplib.NTPClient()
RUNNING = True               # <-- global flag instead of sys.exit()

def signal_handler(sig, frame):
    global RUNNING
    print(f"\nReceived signal {sig}. Stopping loop gracefully...")
    RUNNING = False

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)  # Docker stop
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C

def get_ntp_time():
    response = client.request('time.windows.com')
    return datetime.fromtimestamp(response.tx_time)



class VideoCapture(Process):
    def __init__(self,stream_path,id,img_size,fps,start_time,anchor,save_path):
        super(VideoCapture, self).__init__()
        self.stream_path = stream_path
        self.id = id
        self.img_size = img_size
        self.fps = fps
        self.start_time = datetime.now()
        self.anchor = anchor
        self.save_path = save_path + id + '.mp4'
        self.save_log = save_path + id + '.txt'
    
    def run(self):
        

        print("RUN camera ",self.id)
        cap = cv2.VideoCapture(self.stream_path, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        out_video = cv2.VideoWriter(self.save_path, cv2.VideoWriter_fourcc('m','p','4','v'),self.fps,self.img_size)

        out_log = open(self.save_log,'w')

        print(self.start_time, self.anchor)
        while(True):
            ret, frame = cap.read()
            current_time = datetime.now()
            curr_t = self.anchor + timedelta(seconds=(current_time - self.start_time).total_seconds())
            formatted_t = curr_t.strftime("%Y-%m-%d_%H-%M-%S-%f")
            # file_name = f"{step:06d}_{curr_t.timestamp()}_{formatted_t}"

            print(curr_t,file=out_log)

                                      
            frame = cv2.resize(frame,self.img_size,cv2.INTER_LINEAR)
            """  
            text = "Hello, OpenCV!"
            org = (50, 50)  # Bottom-left corner of the text string
            fontFace = cv2.FONT_HERSHEY_SIMPLEX
            fontScale = 1.5
            color = (0, 0, 255)  # Red color in BGR format
            thickness = 2
            lineType = cv2.LINE_AA # For anti-aliased text

            # Add the text to the image
            cv2.putText(frame, formatted_t, org, fontFace, fontScale, color, thickness, lineType)
            """
            
            out_video.write(frame)

            if not RUNNING:
                break

            # time.sleep(0.01)
        
        out_video.release()
        cap.release()
        print("Camera ",self.id," process ended.")

 
if __name__ == "__main__":
    video_save_folder  = "/home/aicv/record_data/"
    # Create video save folder if it does not exist
    if not os.path.exists(video_save_folder):
        os.makedirs(video_save_folder)

    start_time = datetime.now()
    anchor = get_ntp_time()

    cap0_source = 'rtsp://admin:t123456p@192.168.0.2:554/h264Preview_01_main'
    cap1_source = 'rtsp://admin:123456@192.168.0.3:554/h264Preview_01_main'
    cap2_source = 'rtsp://admin:123456@192.168.0.4:554/h264Preview_01_main'
    cap3_source = 'rtsp://admin:123456@192.168.0.5:554/h264Preview_01_main'
    cap4_source = 'rtsp://admin:123456@192.168.0.6:554/h264Preview_01_main'
    cap5_source = 'rtsp://admin:123456@192.168.0.7:554/h264Preview_01_main'
    cap6_source = 'rtsp://admin:123456@192.168.0.8:554/h264Preview_01_main'
    cap7_source = 'rtsp://admin:123456@192.168.0.9:554/h264Preview_01_main'

    fps = 25
    img_size = (960,540)

    # Camera Initialization

    cap0 = VideoCapture(cap0_source,'192.168.0.2',img_size,fps,start_time,anchor,video_save_folder)
    cap1 = VideoCapture(cap1_source,'192.168.0.3',img_size,fps,start_time,anchor,video_save_folder)
    cap2 = VideoCapture(cap2_source,'192.168.0.4',img_size,fps,start_time,anchor,video_save_folder)
    cap3 = VideoCapture(cap3_source,'192.168.0.5',img_size,fps,start_time,anchor,video_save_folder)
    cap4 = VideoCapture(cap4_source,'192.168.0.6',img_size,fps,start_time,anchor,video_save_folder)
    cap5 = VideoCapture(cap5_source,'192.168.0.7',img_size,fps,start_time,anchor,video_save_folder)
    cap6 = VideoCapture(cap5_source,'192.168.0.8',img_size,fps,start_time,anchor,video_save_folder)
    cap7 = VideoCapture(cap5_source,'192.168.0.9',img_size,fps,start_time,anchor,video_save_folder)

    # Start Process    
    cap0.start()
    cap1.start()
    cap2.start()
    cap3.start()
    cap4.start()
    cap5.start()
    cap6.start()
    cap7.start()

    while True:
        time.sleep(0.5)

        if not RUNNING:
            break
    
    cap0.terminate()
    cap0.join()
    cap1.terminate()
    cap1.join()
    cap2.terminate()
    cap2.join()
    cap3.terminate()
    cap3.join()
    cap4.terminate()
    cap4.join()
    cap5.terminate()
    cap5.join() 
    cap6.terminate()
    cap6.join()
    cap7.terminate()
    cap7.join()   

    print("All camera processes ended.")