import argparse
import time
from pymavlink import mavutil

def main():
    parser = argparse.ArgumentParser(description="Listen for MAVLink messages.")
    parser.add_argument("--device", type=str, default="udpin:0.0.0.0:14550", help="MAVLink connection string (default: udpin:0.0.0.0:14550)")
    args = parser.parse_args()

    print(f"Connecting to {args.device}...")
    mav = mavutil.mavlink_connection(args.device)

    print("Waiting for heartbeat...")
    mav.wait_heartbeat()
    print("Heartbeat received!")

    while True:
        msg = mav.recv_match(blocking=True)
        if not msg:
            continue
            
        if msg.get_type() == "BAD_DATA":
            continue

        print(f"[{msg.get_srcSystem()}/{msg.get_srcComponent()}] {msg.get_type()}: {msg}")

if __name__ == "__main__":
    main()
