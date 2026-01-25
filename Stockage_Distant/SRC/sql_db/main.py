import sqlite3
import os
import json
import datetime
from PIL import Image
import io

BASE_PATH = os.path.dirname(__file__)
DB_NAME = os.path.join(BASE_PATH,"app.db")
IMAGE_PATH = os.path.join(BASE_PATH,"images")

def create_stat_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS STATS (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        NAME TEXT NOT NULL,
        COUNT INTEGER
    )
    """)

    conn.commit()
    conn.close()
    
def create_main_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS MAIN (
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
        ID_ANIMAL INTEGER FOREIGN KEY,
        BATTERIE TEXT
    )
    """)

    conn.commit()
    conn.close()

def formate_date(data:dict):
    annee = data.get('DATE.YEAR')
    mois = data.get('DATE.MONTH')
    jours = data.get('DATE.DAY')
    heures = data.get('DATE.HOUR')
    minutes = data.get('DATE.MINUTE')
    secondes = data.get('DATE.SECOND')
    date = f"{annee}-{mois}-{jours}_{heures}:{minutes}:{secondes}"
    date = datetime.datetime.strptime(date, "%Y-%m-%d_%H:%M:%S")
    return date.strftime("%Y-%m-%d %H:%M:%S")

def path_from_buffer(data:dict):
    img_buffer = data.get('IMG')

    hex_string = img_buffer.replace(" ", "")

    hex_bytes = bytes.fromhex(hex_string)

    image = Image.open(io.BytesIO(hex_bytes))

    image.save(os.path.join(IMAGE_PATH,f"{formate_date(data)}.png"))
    return os.path.join(IMAGE_PATH,f"{formate_date(data)}.png")

def insert_img(data:dict):
    create_stat_table()
    create_main_table()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO MAIN (DATE_SERVER, DATE_TRAP, GEOLOCALISATION_LAT, GEOLOCALISATION_LONG, TEMPERATURE, HUMIDITE, IMAGE_REPERTOIRE, BATTERIE)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, 
        (
            formate_date(data),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data.get('GPS.LAT'),
            data.get('GPS.LONG'), 
            data.get('WHEATER.TEMP'), 
            data.get('WHEATER.HUM'), 
            path_from_buffer(data), 
            data.get('CAM.BATTERY')
        )
    )

    conn.commit()
    conn.close()

def main():
    with open(os.path.join(BASE_PATH,'data.json'),'r') as f:
        data = json.load(f)
    insert_img(data)


if __name__ == "__main__":
    main()