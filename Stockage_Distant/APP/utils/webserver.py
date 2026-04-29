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
import hmac
from flask import g
from io import BytesIO


from io import StringIO
from pathlib import Path
from urllib.parse import quote
from utlitaires import app, logging, get_properties, JSON_API_KEY

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font

    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    Workbook = None  # type: ignore
    Font = None  # type: ignore
    logging.warning(
        "openpyxl not installed. XLSX export will not be available. Install with: pip install openpyxl"
    )
from utils import web_map
from utils.sql_db import sql_db
from utils.data_receiver import data_receiver
from utils.ai_settings import get_ai_settings, set_ai_settings

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

def t(key: str, default: str = "", **kwargs) -> str:
    # 1) try current lang
    lang = get_lang()
    data = _load_lang_file(lang)

    def _get(data_dict):
        if key in data_dict and isinstance(data_dict[key], str):
            return data_dict[key]
        cur = data_dict
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur if isinstance(cur, str) else None

    v = _get(data)
    if v is not None:
        if kwargs:
            try:
                return v % kwargs
            except (TypeError, ValueError, KeyError):
                return v
        return v

    # 2) fallback to English
    v = _get(_load_lang_file("en"))
    if v is not None:
        if kwargs:
            try:
                return v % kwargs
            except (TypeError, ValueError, KeyError):
                return v
        return v

    # 3) last fallback
    if default and kwargs:
        try:
            return default % kwargs
        except (TypeError, ValueError, KeyError):
            return default
    return default or key





class webserver:
    _INGEST_MAX_METADATA_BYTES = 128 * 1024
    _INGEST_MAX_IMAGE_BYTES = 12 * 1024 * 1024

    @staticmethod
    def _load_api_keys() -> dict:
        try:
            with open(JSON_API_KEY, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {}

    @staticmethod
    def _get_ingest_token() -> str:
        # Env var has priority (safer for production than committed JSON).
        # env_token = (os.environ.get("INGEST_API_KEY") or "").strip()
        env_token = get_properties().get("INGEST_API_KEY", "").strip()
        if env_token:
            return env_token

        keys = webserver._load_api_keys()
        return str(keys.get("INGEST_API_KEY", "")).strip()

    @staticmethod
    def _is_ip_allowed() -> bool:
        # Optional allowlist for fixed microcontroller IP(s):
        # env INGEST_ALLOW_IPS="192.168.1.40,192.168.1.41"
        env_allow = (os.environ.get("INGEST_ALLOW_IPS") or "").strip()
        keys = webserver._load_api_keys()
        json_allow = keys.get("INGEST_ALLOW_IPS", [])

        allowed = []
        if env_allow:
            allowed.extend([p.strip() for p in env_allow.split(",") if p.strip()])
        if isinstance(json_allow, list):
            allowed.extend([str(p).strip() for p in json_allow if str(p).strip()])

        # No allowlist configured => allow all IPs.
        if not allowed:
            return True

        forwarded = request.headers.get("X-Forwarded-For", "")
        client_ip = forwarded.split(",")[0].strip() if forwarded else (request.remote_addr or "")
        return client_ip in allowed

    @staticmethod
    def _check_ingest_auth():
        # Keep this simple for microcontroller firmware: token in header or query.
        expected = webserver._get_ingest_token()
        if not expected:
            return False, ("ingest token not configured", 503)

        provided = (request.headers.get("X-API-Key") or request.args.get("key") or "").strip()
        if not provided or not hmac.compare_digest(provided, expected):
            return False, ("unauthorized", 401)

        if not webserver._is_ip_allowed():
            return False, ("forbidden", 403)

        return True, None

    @staticmethod
    def _read_limited_body(max_bytes: int):
        if request.content_length is not None and request.content_length > max_bytes:
            return None, ("payload too large", 413)

        data = request.get_data(cache=False, as_text=False)
        if len(data) > max_bytes:
            return None, ("payload too large", 413)

        return data, None

    @staticmethod
    def init_sql_table():
        sql_db.create_stat_table()
        sql_db.create_main_table()
        sql_db.create_camera_table()
        sql_db.create_IA_table()

    @staticmethod
    def _normalize_image_row(row):
        d = dict(row)
        try:
            temp_value = d.get("TEMPERATURE")
            d["TEMPERATURE"] = (
                float(temp_value)
                if temp_value is not None
                else None
            )
        except Exception:
            d["TEMPERATURE"] = None
        try:
            hum_value = d.get("HUMIDITE")
            d["HUMIDITE"] = (
                float(hum_value)
                if hum_value is not None
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
                img_path = d["IMAGE_TRAITEE"]
                # Extract relative path if it's an absolute path (old data before fix)
                if img_path.startswith('/') or '\\' in img_path:
                    # Extract just the relative part after 'static/'
                    if '/static/' in img_path:
                        img_path = img_path.split('/static/')[-1]
                    elif '\\static\\' in img_path:
                        img_path = img_path.split('\\static\\')[-1]
                d["CHEMIN_IMAGE"] = img_path
            elif d.get("IMAGE_REPERTOIRE") is not None:
                d["CHEMIN_IMAGE"] = d["IMAGE_REPERTOIRE"]
        except Exception:
            pass

        try:
            conf_value = d.get("CONFIANCE")
            d["CONFIANCE"] = (
                float(conf_value)
                if conf_value is not None
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

            # Show both ETAT=0 (no issue) and ETAT=2 (human detected - alert)
            where = ["(ETAT = 0 OR ETAT = 2)"]
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

            images = [webserver._normalize_image_row(r) for r in rows]

            image_ids = [img.get("ID") for img in images if img.get("ID") is not None]
            detected_map = {}
            if image_ids:
                placeholders = ",".join(["?"] * len(image_ids))
                cursor.execute(
                    f"""
                    SELECT IMAGE_ID, ANIMAL, CONFIANCE
                    FROM {sql_db.IA_TABLE}
                    WHERE IMAGE_ID IN ({placeholders})
                    ORDER BY CONFIANCE DESC
                    """,
                    image_ids,
                )

                ia_rows = cursor.fetchall()
                for r in ia_rows:
                    animal = r["ANIMAL"]
                    if not animal:
                        continue
                    conf_value = r["CONFIANCE"]
                    try:
                        conf_value = float(conf_value) if conf_value is not None else None
                    except Exception:
                        conf_value = None

                    detected_map.setdefault(r["IMAGE_ID"], []).append(
                        {"ANIMAL": animal, "CONFIANCE": conf_value}
                    )

            for img in images:
                img["DETECTED_ANIMALS"] = detected_map.get(img.get("ID"), [])

            conn.close()

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
        if not OPENPYXL_AVAILABLE:
            raise ImportError("openpyxl is not installed. Please install it with: pip install openpyxl")
        
        assert Workbook is not None, "Workbook should be available"
        assert Font is not None, "Font should be available"
        
        # Create Excel file
        wb = Workbook()
        ws = wb.active
        if ws is None:
            raise ValueError("Failed to create worksheet")
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
                    cell.hyperlink = f"images/{os.path.basename(value)}"  # type: ignore
                    cell.value = f"📷 {os.path.basename(value)}"  # type: ignore
                    cell.font = Font(color="0563C1", underline="single")
                else:
                    cell.value = value

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter  # type: ignore
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

            sql_db.remove_img(str(image_id))
            
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
                    temp_value = d.get("TEMPERATURE")
                    d["TEMPERATURE"] = (
                        float(temp_value)
                        if temp_value is not None
                        else None
                    )
                except Exception:
                    d["TEMPERATURE"] = None

                try:
                    hum_value = d.get("HUMIDITE")
                    d["HUMIDITE"] = (
                        float(hum_value)
                        if hum_value is not None
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

    @app.route("/config/ai", methods=["GET", "POST"])
    @login_required
    @role_required("dev")
    def config_ai():
        error = None
        message = None
        settings = get_ai_settings()

        if request.method == "POST":
            active_model = (request.form.get("active_model") or "speciesnet-default").strip()
            custom_model_path = (request.form.get("custom_model_path") or "").strip()

            try:
                settings = set_ai_settings(active_model, custom_model_path)
                message = t("config_ai.saved")
                sql_db.log_event(
                    event_type="ai_config_updated",
                    description=f"AI model changed to {settings.get('active_model')} by {session.get('user')}",
                    cam_id=None,
                    image_id=None,
                )
            except ValueError as e:
                error = str(e)
            except Exception as e:
                error = f"Unexpected error while saving AI config: {e}"

        return render_template(
            "config_ai.html",
            settings=settings,
            error=error,
            message=message,
        )

    # Data reception routes
    properties = get_properties()
    METADATA_PATH = properties.get("METADATA_PATH")
    METAIMAGE_PATH = properties.get("IMAGE_PATH")
    TEST_PATH = properties.get("TEST_PATH")

    @app.route(METADATA_PATH, methods=["POST"])
    def receive_metadata():
        auth_ok, auth_err = webserver._check_ingest_auth()
        if not auth_ok:
            if auth_err is None:
                return "unauthorized", 401
            msg, code = auth_err
            return msg, code

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
            data, read_err = webserver._read_limited_body(webserver._INGEST_MAX_METADATA_BYTES)
            if read_err:
                msg, code = read_err
                return msg, code
            if data is None:
                return "invalid payload", 400

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
        auth_ok, auth_err = webserver._check_ingest_auth()
        if not auth_ok:
            if auth_err is None:
                return "unauthorized", 401
            msg, code = auth_err
            return msg, code

        logging.info(f"{'NEW RECEPTION':=^50}")
        img_data, read_err = webserver._read_limited_body(webserver._INGEST_MAX_IMAGE_BYTES)
        if read_err:
            msg, code = read_err
            return msg, code
        if img_data is None:
            return "No data received", 400
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
    def set_lang(lang):
        lang = str(lang or "").lower()
        if lang in SUPPORTED_LANGS:
            session["lang"] = lang
            _load_lang_file.cache_clear()  
        return redirect(request.referrer or url_for("home"))


