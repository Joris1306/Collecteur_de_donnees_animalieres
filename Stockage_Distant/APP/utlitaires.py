import os
from flask import Flask, request, jsonify, render_template, Response
from PIL import Image,ImageFile
import io
import numpy as np
import cv2
import datetime
import sqlite3
from sqlalchemy import func
import json
import queue
import threading
import ast
import folium
import webbrowser
import time
import socket
import logging
import secrets


logging.basicConfig(level=logging.DEBUG)

BASE_PATH = os.path.dirname(__file__)
JSON_CONFIG = os.path.join(BASE_PATH,'JSON','config.json')
JSON_API_KEY = os.path.join(BASE_PATH,'JSON','API_KEY.json')
JSON_PROPERTIES = os.path.join(BASE_PATH,'JSON','settings.json')

# store images inside the flask static folder so url_for('static', filename=...) works
IMAGE_PATH = os.path.join(BASE_PATH, 'static', 'images')
os.makedirs(IMAGE_PATH, exist_ok=True)

DB_PATH = os.path.join(BASE_PATH,'app.db')

app = Flask(__name__)
# Configure Flask session secret key. Prefer env var; fallback to a random token.
app.secret_key = (
    os.environ.get("FLASK_SECRET_KEY")
    or os.environ.get("SECRET_KEY")
    or secrets.token_hex(32)
)

def get_properties():
    with open(JSON_PROPERTIES, "r") as f:
        return json.load(f)
    
def my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


# Import utils after defining app and constants (avoid circular imports)
from utils.image_reconstructor import image_reconstructor
from utils.data_receiver import data_receiver
from utils.sql_db import sql_db
from utils.webserver import webserver
from utils.web_map import web_map



def main():
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        threading.Thread(target=data_receiver._io_worker, daemon=True).start()
    # app.run(debug=True)
    # import here to avoid circular import (sample_data_example imports this module)
    import sample

    file = 'pic2'
    buff = sample.load_sample.sample_image(file)

    image = image_reconstructor.jpeg_buff_to_image(buff)

    image.show()

    Image.open(os.path.join(sample.SAMPLE_PATH, f"{file}.webp")).show()

if __name__ == "__main__":
    main()