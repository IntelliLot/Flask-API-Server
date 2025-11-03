#!/usr/bin/env python3
"""
Interactive Coordinate Picker for Parking Slots
Allows users to visually select parking slot coordinates from a camera frame
"""

import cv2
import json
import sys
import numpy as np


class CoordinatePicker:
    def __init__(self, config_path='config.json'):
        self.config_path = config_path
        self.config = self.load_config()
        self.coordinates = []
        self.current_rect = None
        self.drawing = False
        self.image = None
        self.display_image = None

    def load_config(self):
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ Configuration file '{self.config_path}' not found!")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing configuration file: {e}")
            sys.exit(1)

    def capture_test_frame(self):
        """Capture a test frame from camera"""
        camera_type = self.config.get('camera_type', 'usb')

        try:
            if camera_type == 'picamera':
                try:
                    from picamera2 import Picamera2
                    print("Initializing Pi Camera...")
                    picam2 = Picamera2()
                    config = picam2.create_still_configuration(
                        main={"size": (1280, 720)})
                    picam2.configure(config)
                    picam2.start()
                    import time
                    time.sleep(2)
                    frame = picam2.capture_array()
                    picam2.stop()
                    picam2.close()
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    return frame
                except ImportError:
                    print("❌ picamera2 not available")
                    return None

            elif camera_type == 'rtsp':
                rtsp_url = self.config.get('rtsp_url')
                print(f"Connecting to RTSP stream: {rtsp_url}")
                cap = cv2.VideoCapture(rtsp_url)
            else:
                camera_index = self.config.get('camera_index', 0)
                print(f"Opening USB camera {camera_index}...")
                cap = cv2.VideoCapture(camera_index)

            if not cap.isOpened():
                print(f"❌ Failed to open camera")
                return None

            print("Capturing test frame...")
            ret, frame = cap.read()
            cap.release()

            if not ret:
                print("❌ Failed to capture frame")
                return None

            return frame

        except Exception as e:
            print(f"❌ Error capturing frame: {e}")
            return None

    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for drawing rectangles"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.current_rect = [x, y, x, y]

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                self.current_rect[2] = x
                self.current_rect[3] = y
                self.update_display()

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            self.current_rect[2] = x
            self.current_rect[3] = y

            # Normalize coordinates (ensure x1 < x2, y1 < y2)
            x1, y1 = min(self.current_rect[0], self.current_rect[2]), min(
                self.current_rect[1], self.current_rect[3])
            x2, y2 = max(self.current_rect[0], self.current_rect[2]), max(
                self.current_rect[1], self.current_rect[3])

            # Only add if rectangle has area
            if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                self.coordinates.append([x1, y1, x2, y2])
                print(
                    f"✅ Slot {len(self.coordinates)} added: [{x1}, {y1}, {x2}, {y2}]")

            self.current_rect = None
            self.update_display()

    def update_display(self):
        """Update the display with current rectangles"""
        self.display_image = self.image.copy()

        # Draw existing rectangles
        for idx, coord in enumerate(self.coordinates):
            x1, y1, x2, y2 = coord
            cv2.rectangle(self.display_image, (x1, y1),
                          (x2, y2), (0, 255, 0), 2)
            cv2.putText(self.display_image, f"#{idx+1}", (x1+5, y1+20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Draw current rectangle being drawn
        if self.current_rect:
            x1, y1, x2, y2 = self.current_rect
            cv2.rectangle(self.display_image, (x1, y1),
                          (x2, y2), (0, 255, 255), 2)

        # Add instructions
        instructions = [
            "INSTRUCTIONS:",
            "- Click and drag to draw parking slots",
            "- Press 'u' to undo last slot",
            "- Press 's' to save and exit",
            "- Press 'q' to quit without saving",
            f"Slots defined: {len(self.coordinates)}"
        ]

        y_offset = 30
        for line in instructions:
            cv2.putText(self.display_image, line, (10, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y_offset += 25

        cv2.imshow('Coordinate Picker', self.display_image)

    def save_coordinates(self):
        """Save coordinates to config file"""
        self.config['coordinates'] = self.coordinates

        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"\n✅ Coordinates saved to {self.config_path}")
            print(f"   Total slots: {len(self.coordinates)}")
            return True
        except Exception as e:
            print(f"\n❌ Error saving coordinates: {e}")
            return False

    def run(self):
        """Run the coordinate picker"""
        print("\n" + "="*60)
        print("PARKING SLOT COORDINATE PICKER")
        print("="*60 + "\n")

        # Load existing coordinates if any
        existing_coords = self.config.get('coordinates', [])
        if existing_coords:
            print(f"⚠️  Found {len(existing_coords)} existing coordinates")
            response = input("Keep existing coordinates? (y/n): ").lower()
            if response == 'y':
                self.coordinates = existing_coords
                print("✅ Loaded existing coordinates")
            else:
                print("🗑️  Starting fresh")

        # Capture test frame
        print("\nCapturing frame from camera...")
        self.image = self.capture_test_frame()

        if self.image is None:
            print("❌ Failed to capture frame. Cannot continue.")
            return

        print(f"✅ Frame captured: {self.image.shape[1]}x{self.image.shape[0]}")
        print("\nStarting coordinate picker...")
        print("Draw rectangles around each parking slot\n")

        # Setup window and mouse callback
        cv2.namedWindow('Coordinate Picker')
        cv2.setMouseCallback('Coordinate Picker', self.mouse_callback)

        self.update_display()

        # Main loop
        while True:
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("\n🚫 Cancelled without saving")
                break

            elif key == ord('s'):
                if len(self.coordinates) == 0:
                    print(
                        "\n⚠️  No coordinates defined. Press 's' again to save empty list or 'q' to cancel")
                    key2 = cv2.waitKey(0) & 0xFF
                    if key2 == ord('s'):
                        self.save_coordinates()
                        break
                    continue

                self.save_coordinates()
                break

            elif key == ord('u'):
                if self.coordinates:
                    removed = self.coordinates.pop()
                    print(
                        f"↩️  Undone slot {len(self.coordinates)+1}: {removed}")
                    self.update_display()

        cv2.destroyAllWindows()


def main():
    config_file = 'config.json'

    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    picker = CoordinatePicker(config_file)
    picker.run()


if __name__ == "__main__":
    main()
