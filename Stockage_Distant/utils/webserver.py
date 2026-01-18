import queue
from flask import jsonify, render_template, Response, request
import sqlite3
import datetime
import json

from utils import web_map
from utils.sql_db import sql_db
from utils.data_receiver import data_receiver
from utlitaires import app, logging, get_properties


class webserver:
    @staticmethod
    def init_sql_table():
        sql_db.create_stat_table()
        sql_db.create_main_table()
        sql_db.create_camera_table()

    @app.route("/events")
    def events():
        """Server-Sent Events endpoint for real-time updates"""
        def event_stream():
            # Create a queue for this client
            messages = queue.Queue(maxsize=10)
            
            # Register this client
            with data_receiver._listeners_lock:
                data_receiver._update_listeners.append(messages)
            
            try:
                while True:
                    try:
                        # Wait for new message with timeout
                        msg = messages.get(timeout=30)
                        yield f"data: {json.dumps(msg)}\n\n"
                    except queue.Empty:
                        # Send keepalive comment to prevent timeout
                        yield ": keepalive\n\n"
            finally:
                # Unregister this client on disconnect
                with data_receiver._listeners_lock:
                    if messages in data_receiver._update_listeners:
                        data_receiver._update_listeners.remove(messages)
        
        return Response(event_stream(), mimetype="text/event-stream")

    @app.route("/")
    def index():
        try:
            # Ensure DB tables exist before querying
            webserver.init_sql_table()

            conn = sql_db.get_db()
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT * FROM {sql_db.MAIN_TABLE}
                ORDER BY DATE_SERVER DESC
                LIMIT 9
            """)
            rows = cursor.fetchall()
            conn.close()

            # Convert sqlite3.Row objects to plain dicts and normalize types
            images = []
            for r in rows:
                d = dict(r)
                # Ensure numeric types for temperature and humidity
                try:
                    d['TEMPERATURE'] = float(d.get('TEMPERATURE')) if d.get('TEMPERATURE') is not None else None
                except Exception:
                    d['TEMPERATURE'] = None

                try:
                    d['HUMIDITE'] = float(d.get('HUMIDITE')) if d.get('HUMIDITE') is not None else None
                except Exception:
                    d['HUMIDITE'] = None

                images.append(d)

            # images.reverse()
            return render_template("index.html", images=images)
        except sqlite3.OperationalError as e:
            logging.error(f"sqlite3.OperationalError : {e}")
            return render_template("index.html", images=[])
        except Exception as e:
            logging.error(e)
            return render_template("index.html", images=[])
    
    @app.route("/image/<int:cam_id>")
    def image(cam_id):
        try:
            # Ensure DB tables exist before querying
            webserver.init_sql_table()

            conn = sql_db.get_db()
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT * FROM {sql_db.MAIN_TABLE}
                WHERE CAMERA_ID={cam_id}
                ORDER BY DATE_SERVER DESC
                LIMIT 9;
            """)
            rows = cursor.fetchall()
            conn.close()

            # Convert sqlite3.Row objects to plain dicts and normalize types
            images = []
            for r in rows:
                d = dict(r)
                # Ensure numeric types for temperature and humidity
                try:
                    d['TEMPERATURE'] = float(d.get('TEMPERATURE')) if d.get('TEMPERATURE') is not None else None
                except Exception:
                    d['TEMPERATURE'] = None

                try:
                    d['HUMIDITE'] = float(d.get('HUMIDITE')) if d.get('HUMIDITE') is not None else None
                except Exception:
                    d['HUMIDITE'] = None

                images.append(d)

            # images.reverse()
            # logging.info(images)
            return render_template("index.html", images=images)
        except sqlite3.OperationalError as e:
            logging.error(f"sqlite3.OperationalError : {e}")
            return render_template("index.html", images=[])
        except Exception as e:
            logging.error(e)
            return render_template("index.html", images=[])

    @app.route("/map/submap")
    def submap():
        return render_template("map.html")
    
    @app.route("/map")
    def map():
        try:
            # Ensure DB tables exist before querying
            webserver.init_sql_table()

            conn = sql_db.get_db()
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT *
                FROM (
                    SELECT *,
                        ROW_NUMBER() OVER (
                            PARTITION BY CAM_ID ORDER BY UPDATE_DATE DESC
                        ) AS RN
                    FROM {sql_db.CAM_TABLE}
                )
                WHERE RN = 1;
            """)
            rows = cursor.fetchall()
            conn.close()
            cam_list = {}
            for row in rows:
                cam_list[row["CAM_ID"]] = [row["LAST_LAT"], row["LAST_LONG"]]

            web_map.init_cam_list(cam_list)
            web_map.save_map()
            return render_template("index_map.html")
        except Exception as e:
            logging.error(e)
            return render_template("error.html")

    @app.route("/cam")
    def cam():
        webserver.init_sql_table()
        conn = sql_db.get_db()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT *
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY CAM_ID ORDER BY UPDATE_DATE DESC
                    ) AS RN
                FROM {sql_db.CAM_TABLE}
            )
            WHERE RN = 1;
        """)
        rows = cursor.fetchall()
        conn.close()
        cam_list = []
        for row in rows:
            cam_list.append({"id":row["CAM_ID"], "battery":f"{row["BATTERY"]} %", "location":[row["LAST_LAT"],row["LAST_LONG"]]})
        

        return render_template("cam.html", cam_list=cam_list)

    def get_battery_data(cam_id):
        conn = sql_db.get_db()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM {sql_db.CAM_TABLE}
            WHERE CAM_ID = {cam_id}
            ORDER BY UPDATE_DATE
        """)
        rows = cursor.fetchall()
        conn.close()
        battery_data = []
        for row in rows:
            battery_data.append(
                {
                    "UPDATE_DATE":datetime.datetime.fromisoformat(row["UPDATE_DATE"]), 
                    "BATTERY":row["BATTERY"]
                }
            )
        return battery_data

    @app.route('/battery/<int:cam_id>/graph')
    def battery_graph(cam_id):
        return render_template('battery_graph.html', cam_id=cam_id)

    @app.route('/battery/<int:cam_id>/data')
    def battery_data(cam_id):
        battery_data = webserver.get_battery_data(cam_id)

        battery_data.sort(key=lambda x: x['UPDATE_DATE'])

        return jsonify([
            {
                "UPDATE_DATE": entry["UPDATE_DATE"].isoformat(),
                "BATTERY": entry["BATTERY"]
            }
            for entry in battery_data
        ])
    
    # Data reception routes
    properties = get_properties()
    METADATA_PATH = properties.get('METADATA_PATH')
    METAIMAGE_PATH = properties.get('IMAGE_PATH')
    TEST_PATH = properties.get('TEST_PATH')
    
    @app.route(METADATA_PATH, methods=['POST'])
    def receive_metadata():
        # logging.info(request.headers)
        # logging.info(request.data)  # raw bytes
        champ_data = ['IMG.TYPE','IMG.WIDTH','IMG.HEIGHT','DATE.YEAR','DATE.MONTH','DATE.DAY','DATE.HOUR','DATE.MINUTE','DATE.SECOND','GPS.LAT','GPS.LONG','WHEATER.TEMP','WHEATER.HUM','CAM.ID','CAM.BATTERY']
        # champ_data = []
        try:
            data = request.data

            for champ in champ_data:
                if (champ not in data.decode().strip()):
                    return 'missing data',400

            data_receiver._io_queue.put_nowait({'type': 'metadata', 'data': data})
        except queue.Full:
            return 'server busy', 503

        # Return immediately to minimize interaction time with the webpage
        
        return "OK"

    @app.route(METAIMAGE_PATH, methods=['POST'])
    def receive_image():
        logging.info(f"{'NEW RECEPTION':=^50}")
        img_data = request.data  # raw bytes
        logging.info(f"Received {len(img_data)} bytes")
        # logging.info(f"Received {img_data}")
        logging.info(f"Received type {type(img_data)}")

        if not img_data:
            logging.info(f"no data received")
            return "No data received", 400

        try:
            data_receiver._io_queue.put_nowait({'type': 'image', 'data': img_data})
        except queue.Full:
            return 'server busy', 503

        return 'OK'
    
    @app.route(TEST_PATH, methods=['POST'])
    def receive_test():
        data = request.data

        logging.info(data)

        return 'OK'
    