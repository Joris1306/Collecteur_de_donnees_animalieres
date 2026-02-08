import queue
from flask import (
    jsonify,
    render_template,
    Response,
    request,
    redirect,
    url_for,
    session,
)
import sqlite3
import datetime
import json
import csv
import os
import zipfile
from flask import g
from io import BytesIO


from io import StringIO
from pathlib import Path
from urllib.parse import quote
from utlitaires import app, logging, get_properties

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    logging.warning(
        "openpyxl not installed. XLSX export will not be available. Install with: pip install openpyxl"
    )
from utils import web_map
from utils.sql_db import sql_db
from utils.data_receiver import data_receiver

from utils.auth import (
    login_required,
    role_required,
    verify_password,
    is_logged_in,
    block_user,
    unblock_user,
    is_user_blocked,
    get_user_role,
)


from functools import lru_cache
from pathlib import Path
from flask import request, session
import json

# ===== i18n =====
LANG_DIR = Path(__file__).resolve().parent.parent / "lang" 
SUPPORTED_LANGS = {"fr", "en", "cn"}
DEFAULT_LANG = "en"

def get_lang() -> str:
    lang = (request.args.get("lang") or session.get("lang") or DEFAULT_LANG).lower()
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    session["lang"] = lang
    return lang

@lru_cache(maxsize=16)
def _load_lang_file(lang_code: str) -> dict:
    path = LANG_DIR / f"{lang_code}.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def t(key: str, default: str = "") -> str:
    # 1) try current lang
    lang = get_lang()
    data = _load_lang_file(lang)

    def _get(data_dict):
        cur = data_dict
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur if isinstance(cur, str) else None

    v = _get(data)
    if v is not None:
        return v

    # 2) fallback to English
    v = _get(_load_lang_file("en"))
    if v is not None:
        return v

    # 3) last fallback
    return default or key





class webserver:
    @staticmethod
    def init_sql_table():
        sql_db.create_stat_table()
        sql_db.create_main_table()
        sql_db.create_camera_table()

    @staticmethod
    def _normalize_image_row(row):
        d = dict(row)
        try:
            d["TEMPERATURE"] = (
                float(d.get("TEMPERATURE"))
                if d.get("TEMPERATURE") is not None
                else None
            )
        except Exception:
            d["TEMPERATURE"] = None
        try:
            d["HUMIDITE"] = (
                float(d.get("HUMIDITE"))
                if d.get("HUMIDITE") is not None
                else None
            )
        except Exception:
            d["HUMIDITE"] = None

        try:
            d["DATE_SERVER"] = datetime.datetime.fromisoformat(
                d["DATE_SERVER"]
            ).strftime("%H:%M:%S %d/%m/%Y")
        except Exception:
            pass

        try:
            if d.get("IMAGE_TRAITEE") is not None:
                d["CHEMIN_IMAGE"] = d["IMAGE_TRAITEE"]
            elif d.get("IMAGE_REPERTOIRE") is not None:
                d["CHEMIN_IMAGE"] = d["IMAGE_REPERTOIRE"]
        except Exception:
            pass

        try:
            d["CONFIANCE"] = (
                float(d.get("CONFIANCE"))
                if d.get("CONFIANCE") is not None
                else 0.0
            )
        except Exception:
            d["CONFIANCE"] = 0.0

        return d

    # ====== LOGIN ROUTES ======
    @app.route("/login", methods=["GET", "POST"])
    def login_page():
        """Handle login page and authentication"""
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")

            if verify_password(username, password):
                session["user"] = username
                logging.info(f"User '{username}' logged in successfully")
                next_page = request.args.get("next")
                # Validate next_page to prevent open redirect
                if next_page and next_page.startswith("/"):
                    return redirect(next_page)
                return redirect(url_for("index"))
            else:
                logging.warning(f"Failed login attempt for user '{username}'")
                return (
                    render_template("login.html", error="Invalid username or password"),
                    401,
                )

        if is_logged_in():
            return redirect(url_for("index"))

        return render_template("login.html")

    @app.route("/set-lang/<lang>")
    def set_lang(lang):
        if lang not in ["en", "fr", "cn"]:
            lang = "en"
        session["lang"] = lang
        return redirect(request.referrer or url_for("home"))


    @app.route("/logout")
    def logout():
        """Handle user logout"""
        if "user" in session:
            username = session["user"]
            logging.info(f"User '{username}' logged out")
        session.clear()
        return redirect(url_for("login_page"))

    # Inject current user and role into all templates
    @app.context_processor
    def inject_user_context():
        user = session.get("user")
        role = get_user_role(user) if user else "user"
        return {
            "current_user": user,
            "current_role": role,
        }

    @app.context_processor
    def inject_i18n():
        return {
            "t": t,
            "current_lang": get_lang(),
        }


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
            date_to = request.args.get("to", "")
            sort = request.args.get("sort", "desc")
            cam_id = request.args.get("cam_id", "")

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
            cursor.execute(
                f"""
                SELECT * FROM {sql_db.MAIN_TABLE}
                WHERE {where_sql}
                ORDER BY DATE_SERVER {order};
            """,
                params,
            )

            rows = cursor.fetchall()
            conn.close()

            images = [webserver._normalize_image_row(r) for r in rows]

            return render_template(
                "index.html",
                images=images,
                date_from=date_from,
                date_to=date_to,
                sort=sort,
                cam_id=cam_id,
            )

        except sqlite3.OperationalError as e:
            logging.error(f"sqlite3.OperationalError : {e}")
            return render_template("index.html", images=[])
        except Exception as e:
            logging.error(e)
            return render_template("index.html", images=[])

    @app.route("/export")
    @login_required
    def export_csv():
        webserver.init_sql_table()

        # reuse filters
        date_from = request.args.get("from", "")
        date_to = request.args.get("to", "")
        sort = request.args.get("sort", "desc")
        cam_id = request.args.get("cam_id", "")
        format_type = request.args.get("format", "xlsx")  # default to xlsx

        order = "DESC" if sort != "asc" else "ASC"

        where = ["ETAT = 0"]
        params = []

        if cam_id and cam_id.isdigit():
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
        cursor.execute(
            f"""
            SELECT *
            FROM {sql_db.MAIN_TABLE}
            WHERE {where_sql}
            ORDER BY DATE_SERVER {order};
        """,
            params,
        )
        rows = cursor.fetchall()
        conn.close()

        data = [dict(r) for r in rows]

        # Export as XLSX if available and requested
        if format_type == "xlsx" and OPENPYXL_AVAILABLE:
            return webserver._export_xlsx(data)
        else:
            # Fallback to CSV
            return webserver._export_csv_fallback(data)

    @staticmethod
    def _export_xlsx(data):
        """Export data as XLSX with images bundled in a ZIP file"""
        # Create Excel file
        wb = Workbook()
        ws = wb.active
        ws.title = "Images Export"

        # Define headers
        if data:
            headers = list(data[0].keys())
        else:
            headers = [
                "ID",
                "DATE_SERVER",
                "CAMERA_ID",
                "TEMPERATURE",
                "HUMIDITE",
                "IMAGE_REPERTOIRE",
                "ETAT",
            ]

        # Write headers with bold font
        for col_num, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_num, value=header)
            cell.font = Font(bold=True)

        # Collect image files
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        image_files = []

        # Write data rows
        for row_num, row_data in enumerate(data, 2):
            for col_num, header in enumerate(headers, 1):
                value = row_data.get(header, "")
                cell = ws.cell(row=row_num, column=col_num)

                # Create relative hyperlink for IMAGE_REPERTOIRE column
                if header == "IMAGE_REPERTOIRE" and value:
                    image_path = os.path.join(base_path, "static", value)

                    # Store image info for zip
                    if os.path.exists(image_path):
                        image_files.append((image_path, value))

                    # Use relative path in Excel (images/ folder in zip)
                    cell.hyperlink = f"images/{os.path.basename(value)}"
                    cell.value = f"📷 {os.path.basename(value)}"
                    cell.font = Font(color="0563C1", underline="single")
                else:
                    cell.value = value

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Save Excel to BytesIO
        excel_buffer = BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)

        # Create ZIP file containing Excel and images
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add Excel file
            zip_file.writestr("export_images.xlsx", excel_buffer.getvalue())

            # Add all images to images/ folder in zip
            for image_path, relative_path in image_files:
                try:
                    with open(image_path, "rb") as img_file:
                        zip_file.writestr(
                            f"images/{os.path.basename(relative_path)}", img_file.read()
                        )
                except Exception as e:
                    logging.warning(f"Failed to add image {relative_path} to zip: {e}")

        zip_buffer.seek(0)

        return Response(
            zip_buffer.getvalue(),
            mimetype="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="export_images_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.zip"'
            },
        )

    @staticmethod
    def _export_csv_fallback(data):
        """Fallback CSV export"""
        output = StringIO()
        if data:
            fieldnames = list(data[0].keys())
        else:
            fieldnames = [
                "ID",
                "DATE_SERVER",
                "CAMERA_ID",
                "TEMPERATURE",
                "HUMIDITE",
                "IMAGE_REPERTOIRE",
                "ETAT",
            ]

        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for d in data:
            writer.writerow(d)

        return Response(
            output.getvalue(),
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="export_images_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv"'
            },
        )

    @app.route("/image/<int:image_id>/hide", methods=["POST"])
    @login_required
    def hide_image(image_id):
        """Soft delete: set ETAT=1 so it goes to /main/hidden"""
        try:
            webserver.init_sql_table()
            conn = sql_db.get_db()
            cursor = conn.cursor()
            
            # Get image info before hiding
            cursor.execute(f"SELECT CAMERA_ID, NOM_ANIMAL FROM {sql_db.MAIN_TABLE} WHERE ID = ?", (image_id,))
            row = cursor.fetchone()
            cam_id = row["CAMERA_ID"] if row else None
            animal = row["NOM_ANIMAL"] if row else "Unknown"
            
            cursor.execute(
                f"""
                UPDATE {sql_db.MAIN_TABLE}
                SET ETAT = 1
                WHERE ID = ?;
            """,
                (image_id,),
            )
            conn.commit()
            conn.close()
            
            # Log event
            sql_db.log_event(
                event_type="image_hidden",
                description=f"Image {image_id} hidden (detected: {animal})",
                cam_id=cam_id,
                image_id=image_id
            )
            
            return redirect(request.referrer or url_for("index"))
        except Exception as e:
            logging.error(e)
            return redirect(request.referrer or url_for("index"))

    @app.route("/image/<int:image_id>/delete", methods=["POST"])
    @login_required
    def delete_image(image_id):
        """Hard delete: remove DB row + delete image file"""
        try:
            webserver.init_sql_table()
            
            # Get image info before deleting
            conn = sql_db.get_db()
            cursor = conn.cursor()
            cursor.execute(f"SELECT CAMERA_ID FROM {sql_db.MAIN_TABLE} WHERE ID = ?", (image_id,))
            row = cursor.fetchone()
            cam_id = row["CAMERA_ID"] if row else None
            conn.close()

            sql_db.remove_img(image_id)
            
            # Log event
            sql_db.log_event(
                event_type="image_deleted",
                description=f"Image {image_id} permanently deleted",
                cam_id=cam_id,
                image_id=image_id
            )

            return redirect(request.referrer or url_for("index"))

        except Exception as e:
            logging.error(e)
            return redirect(request.referrer or url_for("index"))

    @app.route("/main/hidden")
    @login_required
    @role_required("dev")
    def index_hidden():
        try:
            webserver.init_sql_table()

            date_from = request.args.get("from", "")
            date_to = request.args.get("to", "")
            sort = request.args.get("sort", "desc")
            cam_id = request.args.get("cam_id", "")

            order = "DESC" if sort != "asc" else "ASC"

            where = ["(ETAT <> 0 OR ETAT IS NULL)"]
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
            cursor.execute(
                f"""
                SELECT * FROM {sql_db.MAIN_TABLE}
                WHERE {where_sql}
                ORDER BY DATE_SERVER {order};
            """,
                params,
            )

            rows = cursor.fetchall()
            conn.close()

            images = [webserver._normalize_image_row(r) for r in rows]

            return render_template(
                "index.html",
                images=images,
                date_from=date_from,
                date_to=date_to,
                sort=sort,
                cam_id=cam_id,
            )

        except sqlite3.OperationalError as e:
            logging.error(f"sqlite3.OperationalError : {e}")
            return render_template("index.html", images=[])
        except Exception as e:
            logging.error(e)
            return render_template("index.html", images=[])

    # ====== UNAUTHORIZED ROUTE ======
    @app.route("/unauthorized")
    def unauthorized():
        return render_template("unauthorized.html"), 403

    @app.route("/image/<int:cam_id>")
    @login_required
    def image(cam_id):
        try:
            # Ensure DB tables exist before querying
            webserver.init_sql_table()

            conn = sql_db.get_db()
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT * FROM {sql_db.MAIN_TABLE}
                WHERE CAMERA_ID={cam_id}
                ORDER BY DATE_SERVER DESC
                LIMIT 9;
            """
            )
            rows = cursor.fetchall()
            conn.close()

            # Convert sqlite3.Row objects to plain dicts and normalize types
            images = []
            for r in rows:
                d = dict(r)
                # Ensure numeric types for temperature and humidity
                try:
                    d["TEMPERATURE"] = (
                        float(d.get("TEMPERATURE"))
                        if d.get("TEMPERATURE") is not None
                        else None
                    )
                except Exception:
                    d["TEMPERATURE"] = None

                try:
                    d["HUMIDITE"] = (
                        float(d.get("HUMIDITE"))
                        if d.get("HUMIDITE") is not None
                        else None
                    )
                except Exception:
                    d["HUMIDITE"] = None

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

    @app.route("/map", endpoint="map")
    @login_required
    def map():
        try:
            # Ensure DB tables exist before querying
            webserver.init_sql_table()

            conn = sql_db.get_db()
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT *
                FROM (
                    SELECT *,
                        ROW_NUMBER() OVER (
                            PARTITION BY CAM_ID ORDER BY UPDATE_DATE DESC
                        ) AS RN
                    FROM {sql_db.CAM_TABLE}
                )
                WHERE RN = 1;
            """
            )
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
        cursor.execute(
            f"""
            SELECT *
            FROM (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY CAM_ID ORDER BY UPDATE_DATE DESC
                    ) AS RN
                FROM {sql_db.CAM_TABLE}
            )
            WHERE RN = 1;
        """
        )
        rows = cursor.fetchall()
        conn.close()
        cam_list = []
        for row in rows:
            cam_list.append(
                {
                    "id": row["CAM_ID"],
                    "battery": f"{row["BATTERY"]} %",
                    "location": [row["LAST_LAT"], row["LAST_LONG"]],
                }
            )

        return render_template("cam.html", cam_list=cam_list)

    @staticmethod
    def get_battery_data(cam_id):
        conn = sql_db.get_db()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT * FROM {sql_db.CAM_TABLE}
            WHERE CAM_ID = {cam_id}
            ORDER BY UPDATE_DATE
        """
        )
        rows = cursor.fetchall()
        conn.close()
        battery_data = []
        for row in rows:
            battery_data.append(
                {
                    "UPDATE_DATE": datetime.datetime.fromisoformat(row["UPDATE_DATE"]),
                    "BATTERY": row["BATTERY"],
                }
            )
        return battery_data

    @staticmethod
    def get_all_cameras():
        """Get list of all distinct cameras with their latest data"""
        conn = sql_db.get_db()
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT CAM_ID, BATTERY, UPDATE_DATE
            FROM {sql_db.CAM_TABLE}
            WHERE (CAM_ID, UPDATE_DATE) IN (
                SELECT CAM_ID, MAX(UPDATE_DATE)
                FROM {sql_db.CAM_TABLE}
                GROUP BY CAM_ID
            )
            ORDER BY CAM_ID
        """
        )
        rows = cursor.fetchall()
        conn.close()
        cameras = []
        for row in rows:
            cameras.append({
                "CAM_ID": row["CAM_ID"],
                "BATTERY": row["BATTERY"],
                "UPDATE_DATE": row["UPDATE_DATE"]
            })
        return cameras

    @app.route("/battery")
    @login_required
    def battery():
        """Display battery page with camera list and graph"""
        cameras = webserver.get_all_cameras()
        default_cam_id = cameras[0]["CAM_ID"] if cameras else None
        return render_template("battery.html", cameras=cameras, default_cam_id=default_cam_id)

    @app.route("/journal")
    @login_required
    @role_required("dev")
    def journal():
        """Display system journal with all events"""
        webserver.init_sql_table()
        sql_db.create_journal_table()
        
        # Get pagination params
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page
        
        conn = sql_db.get_db()
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute(f"SELECT COUNT(*) as count FROM {sql_db.JOURNAL_TABLE}")
        total_count = cursor.fetchone()["count"]
        
        # Get events
        cursor.execute(f"""
            SELECT * FROM {sql_db.JOURNAL_TABLE}
            ORDER BY TIMESTAMP DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return render_template('journal.html', events=events, page=page, total_pages=total_pages)

    @app.route("/battery/<int:cam_id>/graph")
    @login_required
    def battery_graph(cam_id):
        return render_template("battery_graph.html", cam_id=cam_id)

    @app.route("/battery/<int:cam_id>/data")
    @login_required
    def battery_data(cam_id):
        battery_data = webserver.get_battery_data(cam_id)

        battery_data.sort(key=lambda x: x["UPDATE_DATE"])

        return jsonify(
            [
                {
                    "UPDATE_DATE": entry["UPDATE_DATE"].isoformat(),
                    "BATTERY": entry["BATTERY"],
                }
                for entry in battery_data
            ]
        )

    # ====== ADMIN ROUTES FOR FORCE LOGOUT ======
    @app.route("/admin/block-user/<username>", methods=["POST"])
    @login_required
    @role_required("admin")
    def admin_block_user(username):
        """Admin: Block a user (force logout)"""
        current_user = session.get("user")

        # Only admin can block users
        if current_user != "admin":
            logging.warning(
                f"Unauthorized block attempt by '{current_user}' on user '{username}'"
            )
            return jsonify({"error": "Unauthorized"}), 403

        # Cannot block yourself
        if username == current_user:
            return jsonify({"error": "Cannot block yourself"}), 400

        if block_user(username):
            logging.critical(f"Admin '{current_user}' blocked user '{username}'")
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": f"User {username} has been blocked",
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": f"User {username} not found"}), 404

    @app.route("/admin/unblock-user/<username>", methods=["POST"])
    @login_required
    @role_required("admin")
    def admin_unblock_user(username):
        """Admin: Unblock a user"""
        current_user = session.get("user")

        if current_user != "admin":
            logging.warning(
                f"Unauthorized unblock attempt by '{current_user}' on user '{username}'"
            )
            return jsonify({"error": "Unauthorized"}), 403

        if unblock_user(username):
            logging.info(f"Admin '{current_user}' unblocked user '{username}'")
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": f"User {username} has been unblocked",
                    }
                ),
                200,
            )
        else:
            return jsonify({"error": f"User {username} not found"}), 404

    @app.route("/admin/user-status/<username>", methods=["GET"])
    @login_required
    @role_required("admin")
    def admin_user_status(username):
        """Admin: Check user status"""
        current_user = session.get("user")

        if current_user != "admin":
            logging.warning(
                f"Unauthorized status check attempt by '{current_user}' on user '{username}'"
            )
            return jsonify({"error": "Unauthorized"}), 403

        is_blocked = is_user_blocked(username)
        return (
            jsonify(
                {
                    "username": username,
                    "blocked": is_blocked,
                    "status": "blocked" if is_blocked else "active",
                }
            ),
            200,
        )

    # Data reception routes
    properties = get_properties()
    METADATA_PATH = properties.get("METADATA_PATH")
    METAIMAGE_PATH = properties.get("IMAGE_PATH")
    TEST_PATH = properties.get("TEST_PATH")

    @app.route(METADATA_PATH, methods=["POST"])
    def receive_metadata():
        # logging.info(request.headers)
        # logging.info(request.data)  # raw bytes
        champ_data = [
            "IMG.TYPE",
            "IMG.WIDTH",
            "IMG.HEIGHT",
            "DATE.YEAR",
            "DATE.MONTH",
            "DATE.DAY",
            "DATE.HOUR",
            "DATE.MINUTE",
            "DATE.SECOND",
            "GPS.LAT",
            "GPS.LONG",
            "WHEATER.TEMP",
            "WHEATER.HUM",
            "CAM.ID",
            "CAM.BATTERY",
        ]
        # champ_data = []
        try:
            data = request.data

            for champ in champ_data:
                if champ not in data.decode().strip():
                    return "missing data", 400

            data_receiver._io_queue.put_nowait({"type": "metadata", "data": data})
        except queue.Full:
            return "server busy", 503

        # Return immediately to minimize interaction time with the webpage

        return "OK"

    @app.route(METAIMAGE_PATH, methods=["POST"])
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
            data_receiver._io_queue.put_nowait({"type": "image", "data": img_data})
        except queue.Full:
            return "server busy", 503

        return "OK"

    @app.route(TEST_PATH, methods=["POST"])
    def receive_test():
        data = request.data

        logging.info(data)

        return "OK"
        
    @app.route("/set-lang/<lang>")
    @login_required
    def set_lang(lang):
        lang = (lang or "").lower()
        if lang in SUPPORTED_LANGS:
            session["lang"] = lang
            _load_lang_file.cache_clear()  
        return redirect(request.referrer or url_for("home"))


