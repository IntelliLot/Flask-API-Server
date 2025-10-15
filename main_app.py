#!/usr/bin/env python3
"""
YOLOv8 Parking Detection System - Main Application Entry Point

A professional parking detection system using YOLOv8 for vehicle detection
and intelligent occupancy monitoring.

Usage:
    python main_app.py --mode video --input video.mp4 --output result.mp4
    python main_app.py --mode realtime --input video.mp4
    python main_app.py --mode image --input image.jpg --output result.jpg
    python main_app.py --interactive
"""

import argparse
import sys
import os
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parking_detection import ParkingDetectionSystem, CONFIG
from parking_detection.utils.helpers import log_system_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('parking_detection.log')
    ]
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="YOLOv8 Parking Detection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process video to file
  python main_app.py --mode video --input carPark.mp4 --output result.mp4
  
  # Real-time processing with display
  python main_app.py --mode realtime --input carPark.mp4
  
  # Live camera processing
  python main_app.py --mode camera
  
  # Live camera with specific camera index
  python main_app.py --mode camera --camera-index 1
  
  # Process single image
  python main_app.py --mode image --input carParkImg.png --output result.jpg
  
  # Interactive mode
  python main_app.py --interactive
        """
    )
    
    parser.add_argument('--mode', choices=['video', 'realtime', 'image', 'camera'], 
                       help='Processing mode')
    parser.add_argument('--input', '-i', help='Input file path')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    parser.add_argument('--camera-index', type=int, default=0, 
                       help='Camera device index for camera mode (default: 0)')
    parser.add_argument('--model', help='YOLOv8 model path (optional)')
    parser.add_argument('--positions', help='Parking positions file path (optional)')
    parser.add_argument('--coordinates', help='JSON file with parking slot coordinates (optional)')
    parser.add_argument('--confidence', type=float, help='Detection confidence threshold')
    parser.add_argument('--interactive', action='store_true', 
                       help='Run in interactive mode')
    parser.add_argument('--debug', action='store_true', 
                       help='Enable debug mode')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    return parser.parse_args()

def interactive_mode():
    """Run the application in interactive mode"""
    print("🚀 YOLOv8 Parking Detection System - Interactive Mode")
    print("=" * 60)
    
    # Check for default files
    default_video = "carPark.mp4"
    default_image = "carParkImg.png"
    
    while True:
        print("\nSelect processing mode:")
        print("1. Process video to file")
        print("2. Real-time video processing")
        print("3. Process single image")
        print("4. Live camera processing")
        print("5. System information")
        print("6. Exit")
        
        try:
            choice = input("\nEnter choice (1-6): ").strip()
            
            if choice == '1':
                # Video to file processing
                input_path = input(f"Enter video path [{default_video}]: ").strip() or default_video
                if not os.path.exists(input_path):
                    print(f"❌ File not found: {input_path}")
                    continue
                
                output_path = input("Enter output path (optional): ").strip() or None
                
                print("🎬 Processing video...")
                try:
                    system = ParkingDetectionSystem()
                    result_path = system.process_video_to_file(input_path, output_path)
                    print(f"✅ Video processing completed: {result_path}")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
            elif choice == '2':
                # Real-time processing
                input_path = input(f"Enter video path [{default_video}]: ").strip() or default_video
                if not os.path.exists(input_path):
                    print(f"❌ File not found: {input_path}")
                    continue
                
                print("🎬 Starting real-time processing...")
                print("Press 'q' to quit, 's' to save frame, 'p' to pause")
                try:
                    system = ParkingDetectionSystem()
                    system.process_video_realtime(input_path)
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
            elif choice == '3':
                # Single image processing
                input_path = input(f"Enter image path [{default_image}]: ").strip() or default_image
                if not os.path.exists(input_path):
                    print(f"❌ File not found: {input_path}")
                    continue
                
                output_path = input("Enter output path (optional): ").strip() or None
                
                print("🖼️ Processing image...")
                try:
                    system = ParkingDetectionSystem()
                    result_path = system.process_single_image(input_path, output_path)
                    print(f"✅ Image processing completed: {result_path}")
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
            elif choice == '4':
                # Live camera processing
                camera_index = input("Enter camera index [0]: ").strip()
                camera_index = int(camera_index) if camera_index.isdigit() else 0
                
                print("📷 Starting live camera processing...")
                print("Press 'q' to quit, 's' to save frame, 'p' to pause, 'r' to record")
                try:
                    system = ParkingDetectionSystem()
                    system.process_camera_realtime(camera_index)
                except Exception as e:
                    print(f"❌ Error: {e}")
                    
            elif choice == '5':
                # System information
                print("\n" + "=" * 60)
                print("📊 SYSTEM INFORMATION")
                print("=" * 60)
                log_system_info()
                
                try:
                    system = ParkingDetectionSystem()
                    status = system.get_system_status()
                    for key, value in status.items():
                        print(f"{key}: {value}")
                except Exception as e:
                    print(f"System status unavailable: {e}")
                    
            elif choice == '6':
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-6.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            print("\n👋 Interactive session ended.")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            break

def main():
    """Main application entry point"""
    args = parse_arguments()
    
    # Configure global settings based on arguments
    if args.debug:
        CONFIG.debug = True
        CONFIG.verbose_logging = True
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.verbose:
        CONFIG.verbose_logging = True
    
    if args.confidence:
        CONFIG.model.confidence_threshold = args.confidence
    
    # Run interactive mode if requested
    if args.interactive:
        interactive_mode()
        return
    
    # Validate arguments for non-interactive mode
    if not args.mode:
        print("❌ Error: --mode is required when not using --interactive")
        print("Use --help for usage information")
        sys.exit(1)
    
    # Input validation - not required for camera mode
    if args.mode != 'camera':
        if not args.input:
            print("❌ Error: --input is required for non-camera modes")
            print("Use --help for usage information")
            sys.exit(1)
        
        if not os.path.exists(args.input):
            print(f"❌ Error: Input file not found: {args.input}")
            sys.exit(1)
    
    try:
        # Load coordinates from JSON file if provided
        parking_coordinates = None
        if args.coordinates:
            if not os.path.exists(args.coordinates):
                print(f"❌ Error: Coordinates file not found: {args.coordinates}")
                sys.exit(1)
            
            import json
            logger.info(f"Loading coordinates from: {args.coordinates}")
            with open(args.coordinates, 'r') as f:
                coord_data = json.load(f)
                # Support both list of [x, y] and list of tuples
                if isinstance(coord_data, list):
                    parking_coordinates = [tuple(coord) if isinstance(coord, list) else coord 
                                         for coord in coord_data]
                    logger.info(f"Loaded {len(parking_coordinates)} parking coordinates from JSON")
                else:
                    print("❌ Error: Coordinates JSON must be a list of [x, y] coordinates")
                    sys.exit(1)
        
        # Initialize system
        logger.info("Initializing parking detection system...")
        system = ParkingDetectionSystem(
            model_path=args.model,
            parking_positions_file=args.positions,
            parking_positions=parking_coordinates
        )
        
        # Process based on mode
        if args.mode == 'video':
            logger.info("Starting video processing...")
            result_path = system.process_video_to_file(args.input, args.output)
            print(f"✅ Video processing completed: {result_path}")
            
        elif args.mode == 'realtime':
            logger.info("Starting real-time processing...")
            system.process_video_realtime(args.input)
            print("✅ Real-time processing completed")
            
        elif args.mode == 'camera':
            logger.info("Starting live camera processing...")
            system.process_camera_realtime(args.camera_index)
            print("✅ Live camera processing completed")
            
        elif args.mode == 'image':
            logger.info("Starting image processing...")
            result_path = system.process_single_image(args.input, args.output)
            print(f"✅ Image processing completed: {result_path}")
    
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        print("\n👋 Processing stopped by user")
    
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ Error: {e}")
        if CONFIG.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
