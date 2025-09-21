import os
import cv2
import shutil
import ntplib

import numpy as np

from argparse import ArgumentParser
from datetime import datetime, timedelta
from stream_sync import StreamSynchronizer

client = ntplib.NTPClient()

def get_ntp_time():
    response = client.request('time.windows.com')
    return datetime.fromtimestamp(response.tx_time)

start_time = datetime.now()
anchor = get_ntp_time()

import signal
import sys
cap_writers = []
RUNNING = True               # <-- global flag instead of sys.exit()

def signal_handler(sig, frame):
    global RUNNING
    print(f"\nReceived signal {sig}. Stopping loop gracefully...")
    RUNNING = False

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)  # Docker stop
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--save", type=str, default="vis")
    parser.add_argument("--ip_path", type=str, default="ips.txt")
    
    
    args = parser.parse_args()
    
    SAVE = args.save
    IP_PATH = args.ip_path
    with open(IP_PATH, "r") as f:
        ips = f.readlines()
    ips = [ip.strip() for ip in ips]
    
    if os.path.exists(SAVE):
        # remove the save directory
        shutil.rmtree(SAVE)
    
    os.makedirs(SAVE, exist_ok=True)
    
    cams = [
        {"source": f"rtsp://admin:123456@{ip}:554/h264Preview_01_main",
         "calibration_parameters": "camera_calibration/calibration_parameters/0",
         "frame_width": 1920,
         "frame_height": 1080,
         "frame_rate": 15.0} for ip in ips]

    stream_synchronizer = StreamSynchronizer(cams)


    try:
        step = 0
        max_dts = []
        
        for cap_id, cam in enumerate(cams):
            cam_dir = os.path.join(SAVE, str(cap_id))
            os.makedirs(cam_dir, exist_ok=True)
            cap_writers.append(cv2.VideoWriter(os.path.join(SAVE, str(cap_id), "video.avi"), cv2.VideoWriter_fourcc(*'XVID'), cam["frame_rate"], (1920, 1080)))

                
        while RUNNING:

            print("##### Step", step, "#####")
            step += 1;

            frame_packet = stream_synchronizer.get_frame_packet()

            if not frame_packet:
                raise RuntimeError("Received invalid Frame Packet")
            
            
            timestamps = []
            for cap_id, frame_data in frame_packet.items():

                print("cap_id:", cap_id, "| frame_status", frame_data["frame_status"], end=" ")
                # show frame only if it is valid
                if frame_data["frame_status"] != "FRAME_OKAY":
                    print()
                    continue

                # compute the maximum inter-packet time delta
                timestamps.append(frame_data["timestamp"])
                cam_dir = os.path.join(SAVE, str(cap_id))
                os.makedirs(cam_dir, exist_ok=True)
                
                curr_t = anchor + timedelta(seconds=(datetime.now() - start_time).total_seconds())
                formatted_t = curr_t.strftime("%Y-%m-%d_%H-%M-%S-%f")
                file_name = f"{step:06d}_{curr_t.timestamp()}_{formatted_t}.png"
                
                # cv2.imwrite(os.path.join(cam_dir, file_name), frame_data["frame"])
                image = cv2.resize(frame_data["frame"], (1920, 1080))
                cap_writers[cap_id].write(image)
                with open(os.path.join(cam_dir, "logs.txt"), "a") as f:
                    f.write(f"{ips[cap_id]}<>{step:06d}<>{curr_t.timestamp()}<>{formatted_t}<>{os.path.join(cam_dir, file_name)}\n")

            max_dts.append(np.max(timestamps) - np.min(timestamps))
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # 27 = ESC
                print("Quit key pressed. Releasing writers and exiting...")
                break

    except KeyboardInterrupt:
        pass
    finally:
        # clean, single-point release so headers/trailers are written
        for i, w in enumerate(cap_writers):
            try:
                w.release()
            except Exception:
                pass
        cv2.destroyAllWindows()
        print("All writers released. Goodbye.")
