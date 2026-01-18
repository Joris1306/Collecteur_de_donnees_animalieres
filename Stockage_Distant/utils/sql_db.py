import sqlite3
import os
import datetime


from utils.image_reconstructor import image_reconstructor
from utlitaires import DB_PATH,logging,IMAGE_PATH


class sql_db:
    MAIN_TABLE = "MAIN"
    STAT_TABLE = "STATS"
    CAM_TABLE = "CAMERA"

    @staticmethod
    def get_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def create_camera_table():
        conn = sql_db.get_db()
        cursor = conn.cursor()
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {sql_db.CAM_TABLE} (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CAM_ID INTEGER NOT NULL,
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
    def formate_date(data:dict):
        try:
            annee = data.get('DATE.YEAR')
            mois = data.get('DATE.MONTH')
            jours = data.get('DATE.DAY')
            heures = data.get('DATE.HOUR')
            minutes = data.get('DATE.MINUTE')
            secondes = data.get('DATE.SECOND')
            date = f"{annee}-{mois}-{jours}_{heures}:{minutes}:{secondes}"
            date = datetime.datetime.strptime(date, "%Y-%m-%d_%H:%M:%S")
            return date.strftime("%Y-%m-%d_%H:%M:%S")
        except Exception as e:
            logging.error(f"Error : {e}")
            return None #sql_db.date_now()


    @staticmethod
    def path_from_buffer(data:dict):
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
            logging.error(f"error in path_from_buffer : {e}")
            logging.error(f"img_buffer = {img_buffer[:15]}[...]")
            logging.error(f"width = {width}")
            logging.error(f"height = {height}")
            logging.error(f"format_ = {format_}")
            
            return None
    
    @staticmethod
    def date_now():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    @staticmethod
    def insert_img(data:dict):
        try:
            sql_db.create_stat_table()
            sql_db.create_main_table()

            conn = sql_db.get_db()
            cursor = conn.cursor()
            cursor.execute(f"""
            INSERT INTO {sql_db.MAIN_TABLE} (DATE_SERVER, DATE_TRAP, GEOLOCALISATION_LAT, GEOLOCALISATION_LONG, TEMPERATURE, HUMIDITE, IMAGE_REPERTOIRE, BATTERIE, CAMERA_ID)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
                (
                    sql_db.formate_date(data),
                    sql_db.date_now(),
                    data.get('GPS.LAT'),
                    data.get('GPS.LONG'), 
                    data.get('WHEATER.TEMP'), 
                    data.get('WHEATER.HUM'), 
                    sql_db.path_from_buffer(data), 
                    data.get('CAM.BATTERY'),
                    data.get('CAM.ID')
                )
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
        finally:
            conn.commit()
            conn.close()

