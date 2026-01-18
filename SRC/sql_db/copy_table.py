import sqlite3
import os
import json

BASE_PATH = os.path.dirname(__file__)
DB_NAME = os.path.join(BASE_PATH,"app.db")


def create_main_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"""
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
        ID_ANIMAL INTEGER,
        BATTERIE TEXT,
        CAMERA_ID INTEGER NOT NULL
    )
    """)

    conn.commit()
    conn.close()

def main():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    query = "PRAGMA table_info(MAIN);"
    # query = "select * from main;"

    cursor.execute(query)

    result = cursor.fetchall()

    # print(result)
    column = [row[1] for row in result]
    print(column)

    query = "select * from main;"
    cursor.execute(query)

    result = cursor.fetchall()

    # data = []
    # for row in result:
    #     print(row)
    #     data.append(dict(zip(column, row)))

    # print(data)

    # with open(os.path.join(BASE_PATH,'data.json'),'w') as f:
    #     json.dump(data,f)
    with open(os.path.join(BASE_PATH,'data.json'),'r') as f:
        data = json.load(f)

    cursor.execute('DROP TABLE MAIN')

    create_main_table()
    print(column)

    for d in data:
        # data_to_insert = [d.get(col) for col in column]
        # print(data_to_insert)
        query = f"""
        INSERT INTO MAIN ({", ".join(column)})
        VALUES ({", ".join([f"'{d.get(col)}'" for col in column])})
        """
        
        cursor.execute(query)

    query = "select * from main;"
    cursor.execute(query)

    result = cursor.fetchall()

    print(result)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    main()