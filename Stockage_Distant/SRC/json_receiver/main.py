from flask import Flask, request, jsonify
import os
import threading
import queue
import datetime
import json

BASE_PATH = os.path.dirname(__file__)
SAVE_FOLDER = "received_images"

if not os.path.exists(os.path.join(BASE_PATH, SAVE_FOLDER)):
    os.makedirs(os.path.join(BASE_PATH, SAVE_FOLDER))

app = Flask(__name__)

# Queue and worker to offload blocking file I/O from request handlers
_io_queue = queue.Queue()

def _io_worker():
    while True:
        item = _io_queue.get()
        try:
            if item['type'] == 'image':
                data = item['data']
                # convert to hex (keeps compatibility with existing downstream code)
                hex_str = " ".join(f"{b:02x}" for b in data)
                with open(os.path.join(BASE_PATH, SAVE_FOLDER, "buff.txt"), "a") as f:
                    f.write(hex_str)
                
            elif item['type'] == 'json':
                data = item['data']
                with open(os.path.join(BASE_PATH, SAVE_FOLDER, "data.json"), "w") as f:
                    f.write(data.decode('utf-8'))

                # copy buff.txt content into image.txt then clear buff.txt
                try:
                    with open(os.path.join(BASE_PATH, SAVE_FOLDER, "buff.txt"), "r") as f:
                        content = f.read()
                except FileNotFoundError:
                    content = ""

                with open(os.path.join(BASE_PATH, SAVE_FOLDER, "image.txt"), "w") as f:
                    f.write(content)

                with open(os.path.join(BASE_PATH, SAVE_FOLDER, "buff.txt"), "w") as f:
                    f.write("")

                data["IMG"] = content

                print(data)

                with open(os.path.join(BASE_PATH, SAVE_FOLDER, "data.json"), "w") as f:
                    json.dump(data, f)

        except Exception as e:
            print("I/O worker error:", e)
        finally:
            _io_queue.task_done()

# Start background worker
threading.Thread(target=_io_worker, daemon=True).start()


@app.route('/api/data', methods=['POST'])
def receive_json():

    # print(request.headers)
    # print(request.data)  # raw bytes

    data = request.data

    # if not request.is_json:
    #     return jsonify({"error": "Request must be JSON"}), 400

    # data = request.get_json(silent=True)
    # if data is None:
    #     return jsonify({"error": "Invalid JSON"}), 400

    try:
        _io_queue.put_nowait({'type': 'json', 'data': data})
    except queue.Full:
        return jsonify({'error': 'server busy'}), 503

    # Return immediately to minimize interaction time with the webpage
    
    return "OK"


@app.route('/api/image', methods=['POST'])
def receive_image():
    img_data = request.data  # raw bytes
    # print(f"Received {len(img_data)} bytes")
    # print(f"Received {img_data}")
    # print(f"Received type {type(img_data)}")

    if not img_data:
        print(f"no data received")
        return "No data received", 400

    try:
        _io_queue.put_nowait({'type': 'image', 'data': img_data})
    except queue.Full:
        return 'server busy', 503

    return 'OK'


@app.route('/api/test', methods=['POST'])
def receive_donnee():
    data = request.data
    if data is None:
        return "No data", 400

    print(data)
    return "OK"


if __name__ == '__main__':
    HOST = "10.187.206.173"
    PORT = 5050
    app.run(
        host=HOST,
        port=PORT,
        debug=True,
        use_reloader=False
    )