import sqlite3
import os
import sys
import datetime

# Add parent directory to path so this script can be run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.image_reconstructor import image_reconstructor
from utlitaires import DB_PATH,logging,IMAGE_PATH


class sql_db:
    MAIN_TABLE = "MAIN"
    STAT_TABLE = "STATS"
    CAM_TABLE = "CAMERA"
    JOURNAL_TABLE = "JOURNAL"
    IA_TABLE = "IA"

    @staticmethod
    def get_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    
    @staticmethod
    def create_camera_table():
        conn = sql_db.get_db()
        cursor = conn.cursor()
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {sql_db.CAM_TABLE} (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CAM_ID INTEGER NOT NULL UNIQUE,
            BATTERY TEXT,
            LAST_LAT TEXT,
            LAST_LONG TEXT,
            UPDATE_DATE DATETIME
        )
        """)

        conn.commit()
        conn.close()

    @staticmethod
    def create_stat_table():
        conn = sql_db.get_db()
        cursor = conn.cursor()
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {sql_db.STAT_TABLE} (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NAME TEXT NOT NULL,
            COUNT INTEGER,
            UPDATE_DATE DATETIME
        )
        """)

        conn.commit()
        conn.close()
    
    @staticmethod
    def create_main_table():
        conn = sql_db.get_db()
        cursor = conn.cursor()
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {sql_db.MAIN_TABLE} (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            DATE_SERVER DATETIME NOT NULL,
            DATE_TRAP DATETIME NOT NULL,
            GEOLOCALISATION_LAT TEXT NOT NULL,
            GEOLOCALISATION_LONG TEXT NOT NULL,
            TEMPERATURE TEXT NOT NULL,
            HUMIDITE TEXT NOT NULL,
            IMAGE_REPERTOIRE TEXT NOT NULL,
            IMAGE_TRAITEE TEXT,
            NOM_ANIMAL TEXT,
            ID_ANIMAL INTEGER,
            BATTERIE TEXT,
            CAMERA_ID INTEGER NOT NULL
        )
        """)
    
        conn.commit()
        conn.close()

    @staticmethod
    def create_journal_table():
        conn = sql_db.get_db()
        cursor = conn.cursor()
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {sql_db.JOURNAL_TABLE} (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            EVENT_TYPE TEXT NOT NULL,
            DESCRIPTION TEXT NOT NULL,
            CAM_ID INTEGER,
            IMAGE_ID INTEGER,
            TIMESTAMP DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()

    @staticmethod
    def create_IA_table():
        conn = sql_db.get_db()
        cursor = conn.cursor()
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {sql_db.IA_TABLE} (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            IMAGE_ID INT NOT NULL,
            ANIMAL TEXT,
            CONFIANCE REAL,
            DESCRIPTION TEXT,
            FOREIGN KEY (IMAGE_ID) REFERENCES {sql_db.MAIN_TABLE}(ID)
        )
        """)

        conn.commit()
        conn.close()

    @staticmethod
    def log_event(event_type, description, cam_id=None, image_id=None):
        """Log an event to the journal"""
        try:
            sql_db.create_journal_table()
            conn = sql_db.get_db()
            cursor = conn.cursor()
            cursor.execute(f"""
            INSERT INTO {sql_db.JOURNAL_TABLE} (EVENT_TYPE, DESCRIPTION, CAM_ID, IMAGE_ID)
            VALUES (?, ?, ?, ?)
            """, (event_type, description, cam_id, image_id))
            conn.commit()
            conn.close()
        except Exception as e:
            logging.error(f"Error logging event: {e}")


    @staticmethod
    def formate_date(data:dict):
        try:
            annee = data.get('DATE.YEAR')
            mois = data.get('DATE.MONTH')
            jours = data.get('DATE.DAY')
            heures = data.get('DATE.HOUR')
            minutes = data.get('DATE.MINUTE')
            secondes = data.get('DATE.SECOND')
            date = f"{annee}-{mois}-{jours}_{heures}-{minutes}-{secondes}"
            date = datetime.datetime.strptime(date, "%Y-%m-%d_%H-%M-%S")
            return date.strftime("%Y-%m-%d_%H-%M-%S")
        except Exception as e:
            logging.error(f"Error : {e}")
            return None #sql_db.date_now()


    @staticmethod
    def path_from_buffer(data:dict):
        img_buffer = None
        width = None
        height = None
        format_ = None
        try:
            img_buffer = data.get('IMG')
            width = data.get('IMG.WIDTH')
            height = data.get('IMG.HEIGHT')
            format_ = data.get('IMG.TYPE')

            # build a filename and save into the static/images folder
            filename = f"{sql_db.formate_date(data)}.png"
            image = image_reconstructor.buff_to_image(
                buf=img_buffer,
                width=width,
                heigth=height,
                format_=format_
            )

            image.save(os.path.join(IMAGE_PATH, filename))
            # return a path relative to the static folder so templates can use url_for('static', filename=path)
            return f"images/{filename}"
        
        except Exception as e:
            if img_buffer and width and height and format_:
                logging.error(f"error in path_from_buffer : {e}")
                if isinstance(img_buffer, (bytes, bytearray)) and len(img_buffer) >= 15:
                    logging.error(f"img_buffer = {img_buffer[:15]}[...]")
                else:
                    logging.error(f"img_buffer = {img_buffer}")
                logging.error(f"width = {width}")
                logging.error(f"height = {height}")
                logging.error(f"format_ = {format_}")

            sql_db.log_event(
                event_type="ERROR",
                description=f"Erreur de reconstruction d'image : e={e}\nimg_buffer = {str(img_buffer)[:50] if img_buffer else 'None'}[...]\nwidth = {width}\nheight = {height}\nformat_ = {format_}",
                cam_id=None,
                image_id=None
            )
            
            return None
    
    @staticmethod
    def date_now():
        return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
    @staticmethod
    def insert_img(data:dict):
        conn = None
        try:
            sql_db.create_stat_table()
            sql_db.create_main_table()
            sql_db.create_IA_table()

            conn = sql_db.get_db()
            cursor = conn.cursor()
            cursor.execute(f"""
            INSERT INTO {sql_db.MAIN_TABLE} (DATE_SERVER, DATE_TRAP, GEOLOCALISATION_LAT, GEOLOCALISATION_LONG, TEMPERATURE, HUMIDITE, IMAGE_REPERTOIRE,IMAGE_TRAITEE, BATTERIE, CAMERA_ID, ETAT)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
                (
                    sql_db.formate_date(data),
                    sql_db.date_now(),
                    data.get('GPS.LAT'),
                    data.get('GPS.LONG'), 
                    data.get('WHEATER.TEMP'), 
                    data.get('WHEATER.HUM'), 
                    data.get('IMAGE_REPERTOIRE'), 
                    data.get('IMAGE_TRAITEE'),
                    data.get('CAM.BATTERY'),
                    data.get('CAM.ID'),
                    data.get('ETAT')
                )
            )

            last_id = cursor.lastrowid

            detections = data.get('IA', []) or []
            primary_animal = None
            primary_conf = None

            for d in detections:
                animal = d.get('ANIMAL') or d.get('NOM_ANIMAL')
                conf_value = d.get('CONFIANCE')
                try:
                    conf_value = float(conf_value) if conf_value is not None else None
                except Exception:
                    conf_value = None

                if animal:
                    cursor.execute(f"""
                    INSERT INTO {sql_db.IA_TABLE} (IMAGE_ID, ANIMAL, CONFIANCE)
                    VALUES (?, ?, ?)
                    """, 
                        (
                            last_id,
                            animal,
                            conf_value
                        )
                    )

                if animal and (primary_conf is None or (conf_value is not None and conf_value > primary_conf)):
                    primary_animal = animal
                    primary_conf = conf_value

            if primary_animal:
                cursor.execute(
                    f"UPDATE {sql_db.MAIN_TABLE} SET NOM_ANIMAL = ? WHERE ID = ?",
                    (primary_animal, last_id),
                )
            
            cursor.execute(f"""
            INSERT INTO {sql_db.CAM_TABLE} (CAM_ID,BATTERY, LAST_LAT, LAST_LONG, UPDATE_DATE)
            VALUES (?, ?, ?, ?, ?)
            """, 
                (
                    data.get("CAM.ID"),
                    data.get('CAM.BATTERY'),
                    data.get('GPS.LAT'),
                    data.get('GPS.LONG'),
                    sql_db.date_now()
                )
            )

        except Exception as e:
            logging.error(f"{f"{"insert_img"} : {e}":^50}")
            logging.error(f"error : {e}")
            for key,value in data.items():
                if key != 'IMG':
                    logging.error(f"{key} : {value}")
            # logging.info(data)
            logging.error("end data")

            sql_db.log_event(
                event_type="ERROR",
                description=f"Error in insert_img : {e}",
                cam_id=data.get('CAM.ID'),
                image_id=None
            )

        finally:
            if conn:
                conn.commit()
                conn.close()

    @staticmethod
    def remove_img(img_id:str):
        conn = None
        try:
            conn = sql_db.get_db()
            cursor = conn.cursor()
            cam_id = None
            img_path = None
            img_processed_path = None
            cursor.execute(f"""
            SELECT * FROM {sql_db.MAIN_TABLE} WHERE ID=
            ?""", (img_id,))
            row = cursor.fetchone()
            if row:
                cam_id = row["CAMERA_ID"]
                img_path = row["IMAGE_REPERTOIRE"]
                img_processed_path = row["IMAGE_TRAITEE"]
            else:
                logging.error(f"Image with ID {img_id} not found.")
                return
            # Delete child rows first to satisfy IA(IMAGE_ID) -> MAIN(ID) FK.
            cursor.execute(f"""
            DELETE FROM {sql_db.IA_TABLE} WHERE IMAGE_ID=?
            """, (img_id,))
            cursor.execute(f"""
            DELETE FROM {sql_db.MAIN_TABLE} WHERE ID=?
            """, (img_id,))
            # if cam_id:
            #     cursor.execute(f"""
            #     DELETE FROM {sql_db.CAM_TABLE} WHERE CAM_ID=?
            #     """, (cam_id,))
            # also remove the image file from the filesystem
            full_path = os.path.join(IMAGE_PATH, os.path.basename(img_path))
            if os.path.exists(full_path):
                os.remove(full_path)

            if img_processed_path:
                processed_full_path = os.path.join(
                    os.path.dirname(IMAGE_PATH),
                    img_processed_path,
                )
                if os.path.exists(processed_full_path):
                    os.remove(processed_full_path)

        except Exception as e:
            logging.error(f"Error in remove_img : {e}")
        finally:
            if conn:
                conn.commit()
                conn.close()

    @staticmethod
    def rename_images_in_db():
        conn = sql_db.get_db()
        cursor = conn.cursor()
        cursor.execute(f"""
        select * from {sql_db.MAIN_TABLE};
        """)

        rows = cursor.fetchall()

        for row in rows:
            old_relative_path = row["IMAGE_REPERTOIRE"]
            
            # Get the filename without path
            filename = os.path.basename(old_relative_path)
            
            # Remove colons from filename
            new_filename = filename.replace(":", "_")
            
            # Build full paths (on disk)
            old_full_path = os.path.join(IMAGE_PATH, filename)
            new_full_path = os.path.join(IMAGE_PATH, new_filename)
            
            # Only process if filename has colons (i.e., changed)
            if filename != new_filename:
                try:
                    # Rename file on disk if it exists
                    if os.path.exists(old_full_path):
                        os.rename(old_full_path, new_full_path)
                        logging.info(f"Renamed file: {old_full_path} -> {new_full_path}")
                    
                    # Update database with new relative path (images/filename format)
                    new_relative_path = f"images/{new_filename}"
                    cursor.execute(f"""
                    UPDATE {sql_db.MAIN_TABLE}
                    SET IMAGE_REPERTOIRE = ?
                    WHERE ID = ?;
                    """, (new_relative_path, row["ID"]))
                    
                except Exception as e:
                    logging.error(f"Error renaming image {filename}: {e}")

        conn.commit()
        conn.close()

def main():
    sql_db.create_main_table()
    sql_db.create_stat_table()
    sql_db.create_camera_table()

    # sql_db.remove_img("396")



if __name__ == "__main__":
    main()