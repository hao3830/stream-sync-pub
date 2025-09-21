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
        while True:

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
                
                cv2.imwrite(os.path.join(cam_dir, file_name), frame_data["frame"])
                with open(os.path.join(cam_dir, "logs.txt"), "a") as f:
                    f.write(f"{ips[cap_id]}<>{step:06d}<>{curr_t.timestamp()}<>{formatted_t}\n")

            max_dts.append(np.max(timestamps) - np.min(timestamps))

    except KeyboardInterrupt:
        pass