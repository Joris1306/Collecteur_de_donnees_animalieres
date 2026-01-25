import queue
from flask import jsonify, render_template, Response, request, redirect, url_for, session
import sqlite3
import datetime
import json

from utils import web_map
from utils.sql_db import sql_db
from utils.data_receiver import data_receiver
from utlitaires import app, logging, get_properties
from auth import login_required, verify_password, is_logged_in, block_user, unblock_user, is_user_blocked


class webserver:
    @staticmethod
    def init_sql_table():
        sql_db.create_stat_table()
        sql_db.create_main_table()
        sql_db.create_camera_table()

    # ====== LOGIN ROUTES ======
    @app.route("/login", methods=['GET', 'POST'])
    def login_page():
        """Handle login page and authentication"""
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            
            if verify_password(username, password):
                session['user'] = username
                logging.info(f"User '{username}' logged in successfully")
                next_page = request.args.get('next')
                # Validate next_page to prevent open redirect
                if next_page and next_page.startswith('/'):
                    return redirect(next_page)
                return redirect(url_for('index'))
            else:
                logging.warning(f"Failed login attempt for user '{username}'")
                return render_template('login.html', error='Invalid username or password'), 401
        
        if is_logged_in():
            return redirect(url_for('index'))
        
        return render_template('login.html')
    
    @app.route("/logout")
    def logout():
        """Handle user logout"""
        if 'user' in session:
            username = session['user']
            logging.info(f"User '{username}' logged out")
        session.clear()
        return redirect(url_for('login_page'))

    # ====== PROTECTED PAGE ROUTES ======
    @app.route("/events")
    @login_required
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
    @login_required
    def home():
        return render_template("home.html")

    
    @app.route("/main")
    @login_required
    def index():
        try:
            webserver.init_sql_table()

            date_from = request.args.get("from", "")
            date_to   = request.args.get("to", "")
            sort      = request.args.get("sort", "desc")
            cam_id    = request.args.get("cam_id", "")

            order = "DESC" if sort != "asc" else "ASC"

            where = ["ETAT = 0"]
            params = []

            if cam_id:
                where.append("CAMERA_ID = ?")
                params.append(int(cam_id))

            if date_from:
                where.append("date(DATE_SERVER) >= date(?)")
                params.append(date_from)

            if date_to:
                where.append("date(DATE_SERVER) <= date(?)")
                params.append(date_to)

            where_sql = " AND ".join(where)

            conn = sql_db.get_db()
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM {sql_db.MAIN_TABLE}
                WHERE {where_sql}
                ORDER BY DATE_SERVER {order};
            """, params)

            rows = cursor.fetchall()
            conn.close()

            images = []
            for r in rows:
                d = dict(r)
                try:
                    d['TEMPERATURE'] = float(d.get('TEMPERATURE')) if d.get('TEMPERATURE') is not None else None
                except Exception:
                    d['TEMPERATURE'] = None
                try:
                    d['HUMIDITE'] = float(d.get('HUMIDITE')) if d.get('HUMIDITE') is not None else None
                except Exception:
                    d['HUMIDITE'] = None
                images.append(d)

            return render_template(
                "index.html",
                images=images,
                date_from=date_from,
                date_to=date_to,
                sort=sort,
                cam_id=cam_id
            )

        except sqlite3.OperationalError as e:
            logging.error(f"sqlite3.OperationalError : {e}")
            return render_template("index.html", images=[])
        except Exception as e:
            logging.error(e)
            return render_template("index.html", images=[])


    @app.route("/main/hidden")
    @login_required
    def index_hidden():
        try:
            webserver.init_sql_table()

            date_from = request.args.get("from", "")
            date_to   = request.args.get("to", "")
            sort      = request.args.get("sort", "desc")
            cam_id    = request.args.get("cam_id", "")

            order = "DESC" if sort != "asc" else "ASC"

            where = ["ETAT <> 0"]
            params = []

            if cam_id:
                where.append("CAMERA_ID = ?")
                params.append(int(cam_id))

            if date_from:
                where.append("date(DATE_SERVER) >= date(?)")
                params.append(date_from)

            if date_to:
                where.append("date(DATE_SERVER) <= date(?)")
                params.append(date_to)

            where_sql = " AND ".join(where)

            conn = sql_db.get_db()
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT * FROM {sql_db.MAIN_TABLE}
                WHERE {where_sql}
                ORDER BY DATE_SERVER {order};
            """, params)

            rows = cursor.fetchall()
            conn.close()

            images = []
            for r in rows:
                d = dict(r)
                try:
                    d['TEMPERATURE'] = float(d.get('TEMPERATURE')) if d.get('TEMPERATURE') is not None else None
                except Exception:
                    d['TEMPERATURE'] = None
                try:
                    d['HUMIDITE'] = float(d.get('HUMIDITE')) if d.get('HUMIDITE') is not None else None
                except Exception:
                    d['HUMIDITE'] = None
                images.append(d)

            return render_template(
                "index.html",
                images=images,
                date_from=date_from,
                date_to=date_to,
                sort=sort,
                cam_id=cam_id
            )

        except sqlite3.OperationalError as e:
            logging.error(f"sqlite3.OperationalError : {e}")
            return render_template("index.html", images=[])
        except Exception as e:
            logging.error(e)
            return render_template("index.html", images=[])


    @app.route("/image/<int:cam_id>")
    @login_required
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
    @login_required
    def submap():
        return render_template("map.html")
    
    @app.route("/map")
    @login_required
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
    @login_required
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
    @login_required
    def battery_graph(cam_id):
        return render_template('battery_graph.html', cam_id=cam_id)

    @app.route('/battery/<int:cam_id>/data')
    @login_required
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
    
    # ====== ADMIN ROUTES FOR FORCE LOGOUT ======
    @app.route("/admin/block-user/<username>", methods=['POST'])
    @login_required
    def admin_block_user(username):
        """Admin: Block a user (force logout)"""
        current_user = session.get('user')
        
        # Only admin can block users
        if current_user != 'admin':
            logging.warning(f"Unauthorized block attempt by '{current_user}' on user '{username}'")
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Cannot block yourself
        if username == current_user:
            return jsonify({'error': 'Cannot block yourself'}), 400
        
        if block_user(username):
            logging.critical(f"Admin '{current_user}' blocked user '{username}'")
            return jsonify({'status': 'success', 'message': f'User {username} has been blocked'}), 200
        else:
            return jsonify({'error': f'User {username} not found'}), 404

    @app.route("/admin/unblock-user/<username>", methods=['POST'])
    @login_required
    def admin_unblock_user(username):
        """Admin: Unblock a user"""
        current_user = session.get('user')
        
        if current_user != 'admin':
            logging.warning(f"Unauthorized unblock attempt by '{current_user}' on user '{username}'")
            return jsonify({'error': 'Unauthorized'}), 403
        
        if unblock_user(username):
            logging.info(f"Admin '{current_user}' unblocked user '{username}'")
            return jsonify({'status': 'success', 'message': f'User {username} has been unblocked'}), 200
        else:
            return jsonify({'error': f'User {username} not found'}), 404

    @app.route("/admin/user-status/<username>", methods=['GET'])
    @login_required
    def admin_user_status(username):
        """Admin: Check user status"""
        current_user = session.get('user')
        
        if current_user != 'admin':
            logging.warning(f"Unauthorized status check attempt by '{current_user}' on user '{username}'")
            return jsonify({'error': 'Unauthorized'}), 403
        
        is_blocked = is_user_blocked(username)
        return jsonify({
            'username': username,
            'blocked': is_blocked,
            'status': 'blocked' if is_blocked else 'active'
        }), 200
    
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
    
