import socket
import sys
import os
import struct
from datetime import datetime

# --- Configuration ---
HOST = '' 
PORT = 5005
BUFFER_SIZE = 1024 # Max datagram size
# Directory where the reconstructed images will be saved
SAVE_DIR = "received_images"
# Size of the custom header prepended to each UDP packet (bytes)
HEADER_SIZE = 8 

# --- Image State Management ---
# Key: Image ID (int) -> Value: Dictionary holding segments
# {101: {1: <bytes>, 2: <bytes>, ...}, ...}
image_buffer = {}
# Key: Image ID (int) -> Value: Expected total number of segments (int)
image_segment_count = {}

# --- Helper Functions ---

def ensure_save_directory(directory):
    """Checks if the save directory exists and creates it if necessary."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def save_image_from_buffer(img_id):
    """Reassembles the image segments and saves the final JPEG file."""
    if img_id not in image_buffer:
        print(f"Error: Image ID {img_id} not in buffer.")
        return

    # Check if all segments are received
    expected_count = image_segment_count.get(img_id, 0)
    received_count = len(image_buffer[img_id])
    
    if received_count < expected_count:
        print(f"Image ID {img_id}: Missing segments ({received_count}/{expected_count}). Cannot save yet.")
        # NOTE: Here is where you would calculate missing indices and send a NACK back!
        # missing_indices = set(range(1, expected_count + 1)) - set(image_buffer[img_id].keys())
        # print(f"  Missing: {missing_indices}")
        return

    # 1. Sort the segments by index
    sorted_segments = sorted(image_buffer[img_id].items())
    
    # 2. Concatenate the raw image data
    # We only take the payload (the second element of the tuple: [1])
    full_jpeg_data = b"".join([payload for index, payload in sorted_segments])
    
    # 3. Save the image file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"image_{img_id}_{timestamp}.jpg"
    filepath = os.path.join(SAVE_DIR, filename)

    try:
        with open(filepath, 'wb') as f:
            f.write(full_jpeg_data)
        
        print(f"\n✅ IMAGE SAVED: {filename}")
        print(f"   Size: {len(full_jpeg_data) / 1024:.2f} KB")
        
        # 4. Clean up the buffer to free memory
        del image_buffer[img_id]
        del image_segment_count[img_id]

    except Exception as e:
        print(f"Error saving file: {e}")

# --- Setup ---
print("Starting UDP Receiver...")
ensure_save_directory(SAVE_DIR)

try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))
    print(f"Socket bound to {HOST or 'all interfaces'} on port {PORT}. Waiting for data...")
except socket.error as msg:
    print(f"Failed to create or bind socket. Error: {str(msg)}")
    sys.exit()


# --- Main Data Reception Loop ---
# 

while True:
    try:
        # sock.recvfrom is blocking, waits here until data is received
        data, addr = sock.recvfrom(BUFFER_SIZE)
        
        # 1. Check minimum size
        if len(data) < HEADER_SIZE:
            print(f"[Received] Too small packet ({len(data)} bytes) from {addr[0]}. Dropping.")
            continue
        
        # 2. Parse the custom 8-byte header
        # Structure: H=Image ID (2), H=Total Segments (2), H=Segment Index (2), H=Data Length (2)
        # H H H H = 8 bytes total
        try:
            (img_id, total_segments, segment_index, data_len) = struct.unpack('>HHHH', data[:HEADER_SIZE])
            
            # The actual image payload is everything after the header
            image_payload = data[HEADER_SIZE:HEADER_SIZE + data_len]

        except struct.error as e:
            print(f"Error parsing header data: {e}. Received data length: {len(data)}")
            continue

        # 3. Initialize state for a new image ID if needed
        if img_id not in image_buffer:
            image_buffer[img_id] = {}
            image_segment_count[img_id] = total_segments
            print(f"\n[New Image] ID: {img_id}. Total expected segments: {total_segments}.")

        # 4. Store the segment in the buffer
        if segment_index in image_buffer[img_id]:
             # Simple duplicate check
            print(f"[Warning] Duplicate segment {segment_index} for Image ID {img_id} from {addr[0]}. Ignoring.")
        else:
            image_buffer[img_id][segment_index] = image_payload
            print(f"[Received Segment] ID: {img_id} | Index: {segment_index} | Size: {len(image_payload)} bytes")

            # 5. Check for completion and save
            if len(image_buffer[img_id]) == image_segment_count[img_id]:
                print(f"--- All {total_segments} segments received for Image ID {img_id} ---")
                save_image_from_buffer(img_id)

    except KeyboardInterrupt:
        print("\nReceiver stopped by user.")
        break
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        break

# Close the socket when the script exits
sock.close()
print("Socket closed. Exiting.")