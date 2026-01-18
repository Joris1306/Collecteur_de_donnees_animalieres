from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/data', methods=['POST'])
def receive_json():

    # debug
    # print(request.method)
    # print(request.url)
    # print(request.args)
    # print(request.headers)
    # print(request.data)  # raw bytes

    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({"error": "Invalid JSON"}), 400

    print(data)
    return jsonify({"received": data})

if __name__ == '__main__':
    app.run(debug=True)