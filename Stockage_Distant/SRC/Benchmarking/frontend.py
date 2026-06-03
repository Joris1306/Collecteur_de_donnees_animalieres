import tkinter as tk
from tkinter import ttk
import sqlite3
import inspect
import re

from lib.my_utils import current_path,log
_ = log()

class win:
    def __init__(self, root):
        self.root = root
        self.root.title("Frontend")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width = screen_width 
        height = screen_height 
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.create_widget()
    
    def create_widget(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack()

        self.combo_table = ttk.Combobox(self.main_frame)
        self.combo_table.pack()

        self.load_data()

        self.table_frame = ttk.Frame(self.root)
        self.table_frame.pack()

        self.button_load = ttk.Button(self.main_frame,text="Load",command=self.load_table)
        self.button_load.pack()

        self.button_ok = ttk.Button(self.main_frame,text="OK",command=self.fin)
        self.button_ok.pack()

        self.filter_var = tk.StringVar()
        self.sort_column = None
        self.sort_reverse = False

    def load_data(self):
        data = load_table_name()
        # print(data)
        self.combo_table['values'] = data
    
    def load_table_column(self):
        table_name = self.combo_table.get()
        table_col = load_table_column(table_name)
        self.columns = [table_col[i][1] for i in range(len(table_col))]
        
        if hasattr(self, "table"):
            self.table.destroy()
        self.table = ttk.Treeview(self.table_frame, columns=self.columns, show="headings")

        # Define headings with sorting
        for col in self.columns:
            self.table.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.table.column(col, width=100)

        self.table.pack(fill="both", expand=True)

    def load_table(self):
        self.load_table_column()
        table_name = self.combo_table.get()
        self.all_rows = load_table(table_name)
        self.display_rows(self.all_rows)

    def display_rows(self, rows):
        for i in self.table.get_children():
            self.table.delete(i)
        for row in rows:
            self.table.insert("", "end", values=row)

    def sort_by_column(self, col):
        col_index = self.columns.index(col)
        self.sort_reverse = not self.sort_reverse
        sorted_rows = sorted(self.all_rows, key=lambda x: x[col_index], reverse=self.sort_reverse)
        self.display_rows(sorted_rows)

    def on_filter(self, event=None):
        filter_text = self.filter_var.get().lower()
        # Show only the first row that matches the filter
        for row in self.all_rows:
            if any(filter_text == str(cell).lower() for cell in row):
                self.display_rows([row])
                return
        # If no match, clear table
        self.display_rows([])

    def fin(self):
        self.root.destroy()

class ihm:
    def __init__(self, root):
        log.log_info("initialisation")
        self.root = root
        self.root.title("Frontend")
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        # width = 3 * screen_width // 4
        # height = 3 * screen_height // 4
        width = screen_width
        height = screen_height
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        self.create_widget()
        # for ev in ("<<ComboboxSelected>>", "<<ListboxSelect>>"):
        #     self.root.bind_all(ev, self.handle_event)
    
    def create_widget(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack()

        self.main_frame_left = ttk.Frame(self.main_frame)
        self.main_frame_left.grid(row=0,column=0)

        self.main_frame_right = ttk.Frame(self.main_frame)
        self.main_frame_right.grid(row=0,column=1)

        self.second_frame = ttk.Frame(self.root)
        self.second_frame.pack(fill="x", expand=True)

        self.micro_frame = ttk.Frame(self.main_frame_left)
        self.micro_frame.pack(fill="x", expand=True)

        self.micro_combo_table_label = ttk.Label(self.micro_frame,text="Microcontroleur")
        self.micro_combo_table_label.pack()

        self.micro_combo_table = ttk.Combobox(self.micro_frame)
        self.micro_combo_table.pack()

        self.micro_combo_table.bind("<<ComboboxSelected>>", self.combo_event_handler)

        self.transmission_frame = ttk.Frame(self.main_frame_left)
        self.transmission_frame.pack(fill="x", expand=True)

        self.transmission_combo_table_label = ttk.Label(self.transmission_frame,text="Transmission")
        self.transmission_combo_table_label.pack()

        self.transmission_combo_table = ttk.Combobox(self.transmission_frame)
        self.transmission_combo_table.pack()

        self.transmission_combo_table.bind("<<ComboboxSelected>>", self.combo_event_handler)
        
        self.camera_frame = ttk.Frame(self.main_frame_left)
        self.camera_frame.pack(fill="x", expand=True)

        self.camera_combo_table_label = ttk.Label(self.camera_frame,text="Camera")
        self.camera_combo_table_label.pack()

        self.camera_combo_table = ttk.Combobox(self.camera_frame)
        self.camera_combo_table.pack()

        self.camera_combo_table.bind("<<ComboboxSelected>>", self.combo_event_handler)

        self.autre_capteur_frame = ttk.Frame(self.main_frame_left)
        self.autre_capteur_frame.pack(fill="x", expand=True)

        self.autre_capteur_listbox_label = ttk.Label(self.autre_capteur_frame,text="Autre(s) capteur(s)")
        self.autre_capteur_listbox_label.pack()

        self.autre_capteur_listbox = tk.Listbox(self.autre_capteur_frame,selectmode="multiple")
        self.autre_capteur_listbox.pack()

        self.autre_capteur_listbox.bind("<<ListboxSelect>>", self.listbox_event_handler)

        self.prix_frame = ttk.Frame(self.main_frame_right)
        self.prix_frame.pack(fill="x", expand=True)

        self.prix_label = ttk.Label(self.prix_frame,text="Prix")
        self.prix_label.pack()

        self.prix_entry = tk.Text(self.prix_frame,height=10,state="disabled")
        self.prix_entry.pack()

        self.puissance_frame = ttk.Frame(self.main_frame_right)
        self.puissance_frame.pack(fill="x", expand=True)

        self.puissance_label = ttk.Label(self.puissance_frame,text="Puissance consommée")
        self.puissance_label.pack()

        self.puissance_entry = tk.Text(self.puissance_frame,height=10,state="disabled")
        self.puissance_entry.pack()

        self.good_frame = ttk.Frame(self.main_frame_right)
        self.good_frame.pack(fill="x", expand=True)

        self.good_label = ttk.Label(self.good_frame,text="Good")
        self.good_label.pack()

        self.good_entry = tk.Text(self.good_frame,height=10,state="disabled")
        self.good_entry.pack()

        self.bad_frame = ttk.Frame(self.main_frame_right)
        self.bad_frame.pack(fill="x", expand=True)

        self.bad_label = ttk.Label(self.bad_frame,text="Bad")
        self.bad_label.pack()

        self.bad_entry = tk.Text(self.bad_frame,height=10,state="disabled")
        self.bad_entry.pack()

        self.button_validate = ttk.Button(self.second_frame,text="valider",command=self.handle_event)
        self.button_validate.pack()

        self.button_quit = ttk.Button(self.second_frame,text="quitter",command=self.fin)
        self.button_quit.pack()
        
        self.load_data()

    def combo_event_handler(self,*args):
        # self.autre_capteur_curselection = self.autre_capteur_listbox.curselection()
        # log.log_debug(f"{ihm.combo_event_handler.__qualname__} : autre_capteur_curselection = {self.autre_capteur_curselection}")
        self.handle_event(*args)

        self.autre_capteur_listbox.selection_clear(0, tk.END)
        if hasattr(self, "autre_capteur_curselection"):
            for idx in self.autre_capteur_curselection:
                if idx < self.autre_capteur_listbox.size():
                    self.autre_capteur_listbox.selection_set(idx)
            log.log_debug(f"{ihm.combo_event_handler.__qualname__} : autre_capteur_curselection = {self.autre_capteur_curselection}")

        return "break"
    
    def listbox_event_handler(self,*args):
        self.autre_capteur_curselection = self.autre_capteur_listbox.curselection()

        log.log_debug(f"{ihm.listbox_event_handler.__qualname__} : autre_capteur_curselection = {self.autre_capteur_curselection}")

        self.handle_event(*args)
        
        log.log_debug(f"{ihm.listbox_event_handler.__qualname__} : autre_capteur_curselection = {self.autre_capteur_curselection}")
        
        return "break"

    def load_data(self):
        # print(f"loaded data = {load_table_name()}")
        uc = list(set(load_table("Compare_uc")))
        self.micro_combo_table['values'] = [uc[i][1] for i in range(len(uc))]

        transmission = list(set(load_table("Compare_transmission")))
        self.transmission_combo_table['values'] = [transmission[i][1] for i in range(len(transmission))]

        camera = list(set(load_table("Compare_camera")))
        self.camera_combo_table['values'] = [camera[i][1] for i in range(len(camera))]

        autre_capteur = list(set(load_table("Compare_Capteur")))
        # print(autre_capteur)
        column_identifiant = 1
        for i in range(len(autre_capteur)):
            self.autre_capteur_listbox.insert(i, autre_capteur[i][column_identifiant])

    def load_table(self):
        pass

    def handle_event(self,*args, **kwargs):
        # self.autre_capteur_curselection = self.autre_capteur_listbox.curselection()
        # if kwargs is not None and kwargs != {}:
        #     print(kwargs)
        # if args is not None and args != ():
        #     print(args)

        self.prix_entry.configure(state='normal')
        self.prix_entry.delete("1.0", "end")
        self.prix_entry.insert(
            "1.0", 
            get_prix(
                self.micro_combo_table.get(),
                self.transmission_combo_table.get(),
                self.camera_combo_table.get(),
                [self.autre_capteur_listbox.get(i) for i in self.autre_capteur_listbox.curselection()]
            )
        )
        self.prix_entry.configure(state='disabled')

        self.puissance_entry.configure(state='normal')
        self.puissance_entry.delete("1.0", "end")
        self.puissance_entry.insert(
            "1.0", 
            get_puissance(
                self.micro_combo_table.get(),
                self.transmission_combo_table.get(),
                self.camera_combo_table.get(),
                [self.autre_capteur_listbox.get(i) for i in self.autre_capteur_listbox.curselection()]
            )
        )
        self.puissance_entry.configure(state='disabled')

        self.good_entry.configure(state='normal')
        self.good_entry.delete("1.0", "end")
        self.good_entry.insert(
            "1.0", 
            get_good(
                self.micro_combo_table.get(),
                self.transmission_combo_table.get(),
                self.camera_combo_table.get(),
                [self.autre_capteur_listbox.get(i) for i in self.autre_capteur_listbox.curselection()]
            )
        )
        self.good_entry.configure(state='disabled')

        self.bad_entry.configure(state='normal')
        self.bad_entry.delete("1.0", "end")
        self.bad_entry.insert(
            "1.0",
            get_bad(
                self.micro_combo_table.get(),
                self.transmission_combo_table.get(),
                self.camera_combo_table.get(),
                [self.autre_capteur_listbox.get(i) for i in self.autre_capteur_listbox.curselection()]
            )
        )
        self.bad_entry.configure(state='disabled')

        

    def fin(self):
        self.root.destroy()


def get_prix(uc,transmission,camera,autre_capteur):
    db_path = current_path("benchmark.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if uc != "":
        query = f"select PRIX_INDICATIF from Compare_uc where MICROCONTROLEUR_CARTE = '{uc}';"
        # print(query)
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_uc = {data}")
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        # print(data)
        data_uc = data if type(data) == str else ""
    else:
        data_uc = ""
    
    if transmission != "":
        query = f"select PRIX_ESTIMATION from Compare_transmission where MODE = '{transmission}';"
        cur.execute(query)
        # print(f"data_transmission = {data}")
        data = cur.fetchall()
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        transmission = data if type(data) == str else ""
    else:
        transmission = ""

    if camera != "":
        query = f"select PRIX_INDICATIF from Compare_Camera where CAMERA = '{camera}';"
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_camera = {data}")
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        camera_data = data if type(data) == str else ""
    else:
        camera_data = ""
    
    if autre_capteur != []:
        # print(f"autre_capteur = {autre_capteur}")
        case_order = " ".join(
            [f"WHEN '{capteur}' THEN {i}\n" for i, capteur in enumerate(autre_capteur)]
        )
        
        query = f"""
            SELECT PRIX_DE_REFERENCE_AMAZON
            FROM Compare_Capteur
            WHERE NOM_DU_CAPTEUR IN ({','.join([f"'{capteur}'" for capteur in autre_capteur])})
            ORDER BY CASE NOM_DU_CAPTEUR\n\t{case_order}\nEND
            LIMIT {len(autre_capteur)};
        """
        # print(query)
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_autre_capteur = {data}")
        # autre_capteur = data if type(data) == str else ""
        autre_capteur_data = dict(zip(autre_capteur,[d[0] for d in data]))
    else:
        autre_capteur_data = ""

    # extraction et calcul des prix
    total = 0
    if data_uc != "":
        match = re.match(r"([-+]?\d*\.?\d+)", data_uc)
        if match:
            value = float(match.group(1))
            total += value
        else:
            data_uc = f"Erreur dans '{data_uc}'"
    if transmission != "":
        match = re.match(r"([-+]?\d*\.?\d+)", transmission)
        if match:
            value = float(match.group(1))
            transmission = value
            total += value
        else:
            transmission = f"Erreur dans '{transmission}'"
    if camera_data != "":
        match = re.match(r"([-+]?\d*\.?\d+)", camera_data)
        if match:
            value = float(match.group(1))
            camera = value 
            total += value
        else:
            camera = f"Erreur dans '{camera_data}'"
    if autre_capteur_data != "":
        autre_capteur = {}
        for i,(key,value) in enumerate(autre_capteur_data.items()):
            match = re.match(r"([-+]?\d*\.?\d+)", value)
            if match:
                value = float(match.group(1))
                autre_capteur[key] = value
                total += value
            else:
                autre_capteur[key] = f"Erreur dans '{value}'"

    conn.close()
    return f"UC : {data_uc} €\nTransmission : {transmission} €\nCamera : {camera} €\nAutre capteur : {autre_capteur}\nTotal : {total} €"


def get_puissance(uc,transmission,camera,autre_capteur):
    db_path = current_path("benchmark.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if uc != "":
        query = f"select PUISSANCE from Compare_uc where MICROCONTROLEUR_CARTE = '{uc}';"
        # print(query)
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_uc = {data}")
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        # print(data)
        data_uc = data if type(data) == str else ""
    else:
        data_uc = ""
    if transmission != "":
        query = f"select ENERGIE from Compare_transmission where MODE = '{transmission}';"
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_transmission = {data}")
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        transmission = data if type(data) == str else ""
    if camera != "":
        query = f"select POINTS_FORTS from Compare_Camera where CAMERA = '{camera}';"
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_camera = {data}")
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        camera_data = data if type(data) == str else ""
    else:
        camera_data = ""
    
    if autre_capteur != []:
        # print(f"autre_capteur = {autre_capteur}")
        case_order = " ".join(
            [f"WHEN '{capteur}' THEN {i}\n" for i, capteur in enumerate(autre_capteur)]
        )
        
        query = f"""
            SELECT DISTINCT(PUISSANCE)
            FROM Compare_Capteur
            WHERE NOM_DU_CAPTEUR IN ({','.join([f"'{capteur}'" for capteur in autre_capteur])})
            ORDER BY CASE NOM_DU_CAPTEUR\n\t{case_order}\nEND
            LIMIT {len(autre_capteur)};
        """
        # print(query)
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_autre_capteur = {data}")
        # autre_capteur = data if type(data) == str else ""
        autre_capteur_data = dict(zip(autre_capteur,[d[0] for d in data]))
    else:
        autre_capteur_data = ""

    # extraction et calcul des puissances
    total = 0
    if data_uc != "":
        match = re.match(r"([-+]?\d*\.?\d+)", data_uc)
        if match:
            value = float(match.group(1))
            total += value
    if transmission != "":
        match = re.match(r"([-+]?\d*\.?\d+)", transmission)
        if match:
            value = float(match.group(1))
            total += value
    if camera_data != "":
        match = re.match(r"([-+]?\d*\.?\d+)", camera_data)
        if match:
            value = float(match.group(1))
            camera = value 
            total += value
        else:
            camera = f"Erreur dans '{camera_data}'"
    if autre_capteur_data != "":
        autre_capteur = {}
        for i,(key,value) in enumerate(autre_capteur_data.items()):
            match = re.match(r"([-+]?\d*\.?\d+)", value)
            if match:
                value = float(match.group(1))
                autre_capteur[key] = value
                total += value
            else:
                autre_capteur[key] = f"Erreur dans '{value}'"

    conn.close()
    return f"UC : {data_uc} w\nTransmission : {transmission} w\nCamera : {"N/A"} w\nAutre capteur : {autre_capteur}\nTotal : {total} w"


def get_good(uc,transmission,camera,autre_capteur):
    db_path = current_path("benchmark.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if uc != "":
        query = f"select POINTS_FORTS from Compare_uc where MICROCONTROLEUR_CARTE = '{uc}';"
        # print(query)
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_uc = {data}")
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        # print(data)
        data_uc = data if type(data) == str else ""
    else:
        data_uc = ""

    if transmission != "":
        query = f"select INCONVENIENTS from Compare_transmission where MODE = '{transmission}';"
        cur.execute(query)
        # print(f"data_transmission = {data}")
        data = cur.fetchall()
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        transmission = data if type(data) == str else ""
    else:
        transmission = ""
    
    if camera != "":
        query = f"select POINTS_FORTS from Compare_Camera where CAMERA = '{camera}';"
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_camera = {data}")
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        camera = data if type(data) == str else ""
    else:
        camera = ""
    
    if autre_capteur != []:
        # print(f"autre_capteur = {autre_capteur}")
        case_order = " ".join(
            [f"WHEN '{capteur}' THEN {i}\n" for i, capteur in enumerate(autre_capteur)]
        )
        
        query = f"""
            SELECT DISTINCT(AVANTAGES)
            FROM Compare_Capteur
            WHERE NOM_DU_CAPTEUR IN ({','.join([f"'{capteur}'" for capteur in autre_capteur])})
            ORDER BY CASE NOM_DU_CAPTEUR\n\t{case_order}\nEND
            LIMIT {len(autre_capteur)};
        """
        # print(query)
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_autre_capteur = {data}")
        # autre_capteur = data if type(data) == str else ""
        autre_capteur = dict(zip(autre_capteur,[d[0] for d in data]))
    else:
        autre_capteur = ""

    conn.close()
    return f"UC : {data_uc}\nTransmission : {transmission}\nCamera : {camera}\nAutre capteur : {autre_capteur}"


def get_bad(uc,transmission,camera,autre_capteur):
    db_path = current_path("benchmark.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    if uc != "":
        query = f"select POINTS_FAIBLES from Compare_uc where MICROCONTROLEUR_CARTE = '{uc}';"
        # print(query)
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_uc = {data}")
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        # print(data)
        data_uc = data if type(data) == str else ""
    else:
        data_uc = ""

    if transmission != "":
        query = f"select AVANTAGES from Compare_transmission where MODE = '{transmission}';"
        cur.execute(query)
        # print(f"data_transmission = {data}")
        data = cur.fetchall()
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        transmission = data if type(data) == str else ""
    else:
        transmission = ""
    
    if camera != "":
        query = f"select POINTS_FAIBLES from Compare_Camera where CAMERA = '{camera}';"
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_camera = {data}")
        if type(data) == list:
            if len(data) != 0:
                if type(data[0]) == tuple:
                    if len(data[0]) != 0:
                        data = data[0][0]
        camera = data if type(data) == str else ""
    else:
        camera = ""
    
    if autre_capteur != []:
        # print(f"autre_capteur = {autre_capteur}")
        case_order = " ".join(
            [f"WHEN '{capteur}' THEN {i}\n" for i, capteur in enumerate(autre_capteur)]
        )
        
        query = f"""
            SELECT DISTINCT(INCONVENIENTS)
            FROM Compare_Capteur
            WHERE NOM_DU_CAPTEUR IN ({','.join([f"'{capteur}'" for capteur in autre_capteur])})
            ORDER BY CASE NOM_DU_CAPTEUR\n\t{case_order}\nEND
            LIMIT {len(autre_capteur)};
        """
        # print(query)
        cur.execute(query)
        data = cur.fetchall()
        # print(f"data_autre_capteur = {data}")
        # autre_capteur = data if type(data) == str else ""
        autre_capteur = dict(zip(autre_capteur,[d[0] for d in data]))
    else:
        autre_capteur = ""

    conn.close()
    return f"UC : {data_uc}\nTransmission : {transmission}\nCamera : {camera}\nAutre capteur : {autre_capteur}"

def load_table_name():
    """list all table

    Returns:
        data (list): list of all table name
    """
    db_path = current_path("benchmark.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    data = cur.fetchall()
    # print(data)
    conn.close()
    return data

def load_table(table):
    if table is None:
        return
    db_path = current_path("benchmark.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(f"select * from {table};")
    data = cur.fetchall()
    # print(data)
    conn.close()
    return data

def load_table_column(table):
    """list all the column name in the table

    Args:
        table (_type_): table name

    Returns:
        data (list): list of all the column name
    """
    db_path = current_path("benchmark.db")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(f"PRAGMA table_info('{table}');")
    data = cur.fetchall()
    # print(data)
    conn.close()
    return data

def main():
    try:
        root = tk.Tk()
        fen = ihm(root)
        # fen = win(root)
        root.mainloop()
    except Exception as e:
        log.log_error(e)
    finally:
        log.close()

if __name__ == "__main__":
    main()