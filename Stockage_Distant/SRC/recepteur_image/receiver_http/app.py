from flask import Flask, request
import datetime
import os
from PIL import Image
import binascii

app = Flask(__name__)
SAVE_FOLDER = "received_images"

if not os.path.exists(os.path.join(os.path.dirname(__file__),SAVE_FOLDER)):
    os.path.exists(os.path.join(os.path.dirname(__file__),SAVE_FOLDER))

class IMAGE:
    def __init__(self, data):
        self.data = data
    
    def build_image(self):
        mode = "RGB"
        width = 512
        height = 512
        hex_bytes = bytes.fromhex(self.data)
        img = Image.frombytes(mode, (width, height), hex_bytes)
        img.save(os.path.join(os.path.dirname(__file__),SAVE_FOLDER,f"output.png"))

@app.route('/upload', methods=['POST'])
def upload_image():
    img_data = request.data  # raw bytes
    # print(f"Received {len(img_data)} bytes")
    # print(f"Received {img_data}")
    # print(f"Received type {type(img_data)}")

    if not img_data:
        print(f"no data received")
        return "No data received", 400

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(os.path.dirname(__file__),SAVE_FOLDER,f"image_.txt")

    hex_str = " ".join(f"{b:02x}" for b in img_data)
    try:
        with open(os.path.join(os.path.dirname(__file__),"received_images","output.txt"),"w") as f:
            f.write(hex_str)
    except Exception as e:
        print(f"Error: {e}")
        return "OK"

    # print(hex_str)

    width = 512
    height = 512
    mode = "RGB"  # grayscale: 1 byte per pixel

    # 1. Clean and convert to bytes
    hex_bytes = bytes.fromhex(hex_str)

    try:
        img = Image.frombytes(mode, (width, height), hex_bytes)
        img.save(os.path.join(os.path.dirname(__file__),SAVE_FOLDER,f"output.png"))
    except Exception as e:
        print(f"Error: {e}")
        return "OK"
        
    with open(filename, 'wb') as f:
        f.write(img_data)

    print(f"Saved {filename}")
    return "OK"

app.run(host="0.0.0.0", port=5050)
