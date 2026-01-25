import sqlite3
import openpyxl
import os
import json
import sys
import re

from lib.my_utils import current_path,save_json,log
    
def read_excel():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "Tab_compare.xlsx")
    wb = openpyxl.load_workbook(file_path)
    
    data = {}

    ignored_sheet = ["Exemple","Estimation Budget","Transmission","Camera","uc","Capteur","Compare PUISSANCE"]
    for ws in wb.worksheets:
        # ignore
        if ws.title in ignored_sheet:
            continue

        print(f"{ws.title:=^100}")
        data[ws.title] = {}

        ws_headers = []
        for n_row,row in enumerate(ws.rows):
            if n_row == 0: # header
                ws_headers = []
                for cell in row:
                    if cell.value is None:
                        continue
                    ws_headers.append(cell.value)
                print(ws_headers)
                continue
            else:
                str_row = [str(cell.value) for cell in row]
                data[ws.title][row[0].value] = dict(zip(ws_headers,str_row))
        
        data[ws.title]["header"] = ws_headers

    # print(data["Compare Transmission"])
    # json save
    # with open("data.json","w",encoding="utf-8") as f:
    #     json.dump(data,f,ensure_ascii=False,indent=4)

    # print(data)
    return data

def normalize_header(header):
    if header is None:
        return 'None'
    for item in header:
        if item is None:
            yield 'None'
            continue
        item = item.replace(" ","_")
        item = item.replace("/","_")
        item = item.replace("-","_")
        item = item.replace(".","_")
        item = item.replace("é","e")
        item = item.replace("û","u")
        item = item.replace("ô","o")
        item = item.replace("'","")
        item = item.replace("(","")
        item = item.replace(")","")
        item = "_".join(item.split("_"))
        item = re.sub(r'_+', '_', item)

        item = item.upper()

        yield item

def save_database(data):
    db_path = current_path("benchmark.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    for i,(key,value) in enumerate(data.items()):
        # if i != 0:
        #     sys.exit(0)

        header = value.get('header')
        table = key.replace(' ','_')
        print(f"data[{key}] = {header}")

        # Wrap column names in double quotes
        columns = [f'"{col}" VARCHAR(255)' for col in normalize_header(header)]
        id_col = f'ID_{key.split(" ")[-1]} INTEGER PRIMARY KEY'
        column = f"{id_col}, " + ", ".join(columns)
        req = f'CREATE TABLE IF NOT EXISTS "{table}" ({column});'
        print(req)
        cur.execute(req)

        print(value)

        for row in value.values():
            if type(row) != dict:
                continue
            # Wrap column names in double quotes for insert
            col_names = ', '.join([f'"{col}"' for col in normalize_header(header)])
            values = ', '.join([f'"{row[h]}"' for h in header])
            req = f'INSERT INTO "{table}" ({col_names}) VALUES ({values});'
            print(req)
            cur.execute(req)

        conn.commit()

    conn.close()

def clean_database():
    db_path = current_path("benchmark.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS Compare_Camera;")
    cur.execute("DROP TABLE IF EXISTS Compare_Transmission;")
    cur.execute("DROP TABLE IF EXISTS Compare_uc;")
    cur.execute("DROP TABLE IF EXISTS Compare_Capteur;")
    conn.commit()
    conn.close()

def main():
    data = read_excel()

    save_json("data.json",data)

    clean_database()

    save_database(data)

if __name__ == "__main__":
    main()