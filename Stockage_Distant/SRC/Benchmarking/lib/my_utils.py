import sys
import os
import pathlib
import datetime
import inspect
import json
from typing import Any,Union
import ctypes
import threading
import queue
import time
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageTk

# from lib.my_utils import log
# _ = log()

def data_path(*paths : str) -> str:
    """chemin renvoyé est absolu par rapport au .py ou .exe 

    Args:
        *filename (str): nom de données invariables (dossier TEMPLATES)

    Returns:
        str: chemin absolu de filename
    """
    rel_path = os.path.join(*paths)

    if hasattr(sys, '_MEIPASS'):
        path = os.path.join(getattr(sys, '_MEIPASS'),rel_path)
    else:
        path = current_path(rel_path)

    return path

def current_path(*paths : str) -> str:
    """chemin renvoyé est absolu par rapport au .py ou .exe 

    Args:
        filename (str): nom de fichier ou chemin relatif vers le fichier

    Returns:
        str: chemin absolu de filename
    """
    rel_path = os.path.join(*paths)
    base = os.path.abspath(sys.argv[0]) # chemin du script/exécutable en cours.
    base_path = os.path.dirname(base) # chemin absolu du repertoire parent du script/exécutable
    return os.path.join(base_path, rel_path) # concaténation du chemin absolu et du fichier en parametre     

def parent_dir(*paths: Union[str, os.PathLike],step=1) -> str:
    """
    Retourne un chemin absolu construit à partir des chemins relatifs fournis,
    en le combinant avec le répertoire parent du premier élément.
    
    Le chemin résultant est absolu et normalisé (supprime les '..' et '.' inutiles).
    
    Args:
        *paths: Un ou plusieurs chemins relatifs ou noms de fichier.
        step (int, optional): Nombre de niveaux de parent à remonter
        
    Returns:
        str: Chemin absolu combiné avec le parent du premier élément.
        
    Exemples:
        >>> parent_dir("fichier.txt")
        '/chemin/vers/parent/fichier.txt'
        
        >>> parent_dir("dossier", "sous-dossier", "fichier.txt")
        '/chemin/vers/parent/dossier/sous-dossier/fichier.txt'
    """
    # Convertit le premier chemin en objet Path et obtient son parent absolu
    base_path = pathlib.Path(sys.argv[0]).parent.absolute()
    for _ in range(step):
        base_path = base_path.parent
    
    # Combine avec les chemins supplémentaires
    full_path = base_path.joinpath(*paths)
    
    # Retourne le chemin normalisé sous forme de chaîne
    return str(full_path.resolve())

def project_root():
    """Returns the consistent project root regardless of execution location"""
    # If frozen (PyInstaller), use _MEIPASS else use the directory containing this file
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS')
    else:
        # Go up one level from the current file's directory
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
def load_json(data_file_path : str) -> dict:
    """Charge un fichier JSON en gérant le BOM UTF-8 si présent.
    
    Args:
        data_file_path (str): Chemin vers le fichier JSON à charger
        
    Returns:
        dict: Données chargées depuis le fichier JSON
        
    Exits:
        En cas d'erreur de décodage JSON ou autre exception, le programme s'arrête
        après avoir loggé l'erreur.
    """
    data = {}
    try:
        # Use utf-8-sig encoding which handles BOM automatically
        with open(data_file_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        log.log_error(f"{'JSON decode error':=^40}")
        log.log_error(f"File: {data_file_path}")
        log.log_error(f"Error: {str(e)}")
        log.log_error(f"fin de programme")
        sys.exit(1)
    except Exception as e:
        log.log_error(f"{'load_json error':=^40}")
        log.log_error(f"File: {data_file_path}")
        log.log_error(f"Error: {str(e)}")
        log.log_error(f"fin de programme")
        sys.exit(1)

    return data

def save_json(data_file_path : str, data : dict[Any,Any] | list[Any] | tuple[Any]) -> None:
    """Sauvegarde des données dans un fichier JSON.
    
    Args:
        data_file_path (str): Chemin du fichier de sortie
        data (dict): Données à sérialiser en JSON
        
    Exits:
        En cas d'erreur pendant la sauvegarde, le programme s'arrête
        après avoir loggé l'erreur avec des informations de débogage.
    """
    try:
        if os.path.exists(os.path.dirname(data_file_path)):
            os.makedirs(os.path.dirname(data_file_path),exist_ok=True)
        with open(data_file_path, 'w',encoding='utf-8') as file:
            json.dump(data, file,ensure_ascii=False)

    except Exception as e:
        frame = inspect.currentframe()
        line = inspect.getframeinfo(frame).lineno if frame else -1
        log.log_error(f"{"save_json erreur":=^40}")
        log.log_error(f"{__file__}:{line} error={e}")
        log.log_error(f"fin de programme")
        sys.exit(1)

def flatten(lst):
    """applati la liste lst 
    ex. lst = [1,2,3,[4,5,5],7]
    flatten(lst) = [1,2,3,4,5,6,7]
        
    Args:
        lst (List[Any,...]|Tuple[Any,...]): liste/tuple à applatir

    Yields:
        Any: _description_
    """
    for item in lst:
        if isinstance(item, list):
            for subitem in flatten(item):
                yield subitem
        else:
            yield item

def emoji_img(text):
    try:
        img_path = parent_dir("flag",f"{text}-flag-png-large.jpg",step=0)
        flag_img = Image.open(img_path)  # Replace with actual path
        flag_img = flag_img.resize((80, 50), Image.LANCZOS) # type: ignore
        return ImageTk.PhotoImage(flag_img)
    except Exception as e:
        frame = inspect.currentframe()
        line = inspect.getframeinfo(frame).lineno if frame else -1
        log.log_error(f"{__file__}:{line} error")
        log.log_error(e)
        log.log_error(f"img_path = {img_path}")
        log.log_error("fin de programme")
        sys.exit(1)

def parse_file_size(size:str):
    units = {'KB':1e3, 'MB':1e6, 'GB':1e9, 'TB':1e12, 'PB':1e15, 'EB':1e18, 'ZB':1e21, 'YB':1e24,'B': 1}
    for unit,factor in units.items():
        if size.endswith(unit):
            # print(f"size = {size}")
            # print(f"size[:-len(unit)] = size[:-len({unit})] = size[:{-len(unit)}] = {size[:-len(unit)]}")
            size = size[:-len(unit)]
            return int(float(size)*factor)
    else:
        return 1

class log:
    """Classe utilitaire thread-safe pour la journalisation (logging) des événements.
    
    Attributes:
        LOG_FILENAME (str): Nom du fichier de log
        LOG_FILEPATH (str): Chemin absolu du fichier de log
        __started (bool): Flag indiquant si le système de log a été initialisé
        file_log (stream): lien vers le fichier de log
    """
    
    # Singleton implementation
    _instance = None
    _lock = threading.Lock()
    
    # Logging thread and queue
    _log_queue = queue.Queue()
    _log_thread = None
    _running = False

    count_info = 0
    count_debug = 0
    count_warning = 0
    count_error = 0

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._initialize()
        return cls._instance

    @classmethod
    def _initialize(cls):
        """Initialise le système de logging."""
        cls.PROJECT_ROOT = parent_dir(step=0)
        cls.LOG_FILENAME = current_path(cls.PROJECT_ROOT, 'logfile.log')
        cls.LOG_FILEPATH = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), cls.LOG_FILENAME)
        # print(f"cls.PROJECT_ROOT = {cls.PROJECT_ROOT}")
        # print(f"cls.LOG_FILENAME = {cls.LOG_FILENAME}")
        # print(f"cls.LOG_FILEPATH = {cls.LOG_FILEPATH} ")
        # sys.exit(0)

        # Ensure log directory exists
        os.makedirs(os.path.dirname(cls.LOG_FILEPATH), exist_ok=True)
        
        max_file_size = '1MB'
        max_file_size_bytes = parse_file_size(max_file_size)
        if os.path.getsize(cls.LOG_FILEPATH) > max_file_size_bytes:
            os.makedirs(os.path.join(cls.PROJECT_ROOT, 'logs'), exist_ok=True)
            shutil.move(cls.LOG_FILEPATH, os.path.join(cls.PROJECT_ROOT, 'logs', f"logfile_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"))
            log.clean()


        # Start the logging thread
        cls._running = True
        cls._log_thread = threading.Thread(
            target=cls._logger_worker,
            daemon=False,
            name="LoggingThread"
        )
        cls._log_thread.start()
        
        # Write initial marker
        cls._log_queue.put(('start', None))

    @classmethod
    def _logger_worker(cls):
        """Worker thread qui traite les messages de log."""
        with open(cls.LOG_FILEPATH, 'a', encoding='utf-8') as log_file:
            while cls._running or not cls._log_queue.empty():
                try:
                    message_type, content = cls._log_queue.get(timeout=0.1)
                    
                    if message_type == 'start':
                        log_file.write(f"{datetime.datetime.now()} {'START':=^100}\n")
                    elif message_type == 'log':
                        level, message = content
                        log_file.write(f"{datetime.datetime.now()} {f"[{level}]":<10} {message}\n")
                    elif message_type == 'clean':
                        log_file.close()
                        while os.path.exists(cls.LOG_FILEPATH):
                            try:
                                os.remove(cls.LOG_FILEPATH)
                            except:
                                time.sleep(0.1)
                        log_file = open(cls.LOG_FILEPATH, 'a', encoding='utf-8')
                    elif message_type == 'close':
                        log_file.write(f"{datetime.datetime.now()} {'END':=^100}\n")
                    log_file.flush()
                    cls._log_queue.task_done()
                except queue.Empty:
                    continue

    @staticmethod
    def log_error(error_str):
        """Log un message d'erreur."""
        if error_str == "fin de programme":
            POP_UP.pop_up("fin de programme")
        log._log_queue.put(('log', ('ERROR', error_str)))
        log.count_error += 1

    @staticmethod
    def log_debug(debug_str, debug_level=0):
        """Log un message de debug."""
        if debug_level > -1:
            log._log_queue.put(('log', ('DEBUG', debug_str)))
            log.count_debug += 1

    @staticmethod
    def log_info(info_str):
        """Log un message d'information."""
        log._log_queue.put(('log', ('INFO', info_str)))
        log.count_info += 1

    @staticmethod
    def log_warning(warning_str):
        """Log un message d'avertissement."""
        log._log_queue.put(('log', ('WARNING', warning_str)))
        log.count_warning += 1

    @staticmethod
    def clean():
        """Réinitialise le fichier de log."""
        log._log_queue.put(('clean', None))

    @staticmethod
    def close(print_stdout = False):
        """Ferme proprement le système de logging."""

        # Prepare table data - transposed version
        headers = ["","INFO", "DEBUG", "WARNING", "ERROR"]
        counts = ["Compte",log.count_info, log.count_debug, log.count_warning, log.count_error]

        # Calculate column widths
        col_widths = [max(len(str(item)) for item in col) 
                     for col in zip(headers, counts)]
        # print(f"col_widths = {col_widths}")
        # for col in zip(headers, counts):
        #     for item in col:
        #         print(item)

        # Add extra space for headers
        col_widths = [max(width, len("Compte")) for width in col_widths]
        # print(f"col_widths = {col_widths}")

        # Build horizontal separator
        separator = "+-" + "-+-".join("-" * width for width in col_widths) + "-+"

        # Print table
        log._log_queue.put(('log', ('INFO', separator)))
        if print_stdout:
            print(separator)
        
        header_iter = [f"{headers[i]:^{col_widths[i]}}" for i in range(len(headers))]
        head = "| " + " | ".join(header_iter) + " |"
        log._log_queue.put(('log', ('INFO', head)))
        if print_stdout:
            print(head)
        log._log_queue.put(('log', ('INFO', separator)))
        if print_stdout:
            print(separator)
        
        dat = "| " + " | ".join(
            f"{str(count):^{width}}" for count, width in zip(counts, col_widths)
        ) + " |"
        log._log_queue.put(('log', ('INFO', dat)))
        if print_stdout:
            print(dat)
        
        log._log_queue.put(('log', ('INFO', separator)))
        if print_stdout:
            print(separator)
                      
        log._log_queue.put(('close', None))
        log._running = False
        if log._log_thread:
            log._log_thread.join(timeout=1)

class CHAR:
    """Classe utilitaire pour la gestion des caractères ASCII.
    
    Attributes:
        NULL (str): Caractère ASCII NULL
        SEPARATOR (str): Caractère ASCII Separator '|'
        COMMA (str): Caractère ASCII Comma ','
        OPEN_CURLY_BRACKETS (str): Caractère ASCII Open Curly Brackets '{'
        CLOSE_CURLY_BRACKETS (str): Caractère ASCII Close Curly Brackets '}'
        SPECIAL_SEPARATOR (str): Caractère ASCII Special Separator '}' + Separator + '{'
    """
    NULL = '\x00'

    SEPARATOR = '\u007C' #
    # SEPARATOR = "\u2016"  # Double Vertical Line
    # SEPARATOR = "\u2758"  # light Vertical Line
    # SEPARATOR = "\u205E"  # four dot
    # SEPARATOR = "\u2AFD"  # Double Solidus
    # SEPARATOR = "\u2E17"  # Double Oblique Hyphen
    # SEPARATOR = "\u241E"  # Symbol for Unit Separator
    # SEPARATOR = "\u2759"  # Shadowed White Vertical Bar
    
    COMMA = "\u201A" # Comma

    OPEN_CURLY_BRACKETS = "\u007B" # {
    CLOSE_CURLY_BRACKETS = "\u007D" # }

    SPECIAL_SEPARATOR = f"\u007D {SEPARATOR} \u007B"

class POP_UP:
    """Classe utilitaire pour la gestion des pop-up.
    
    Attributes:
        OK (int): Code de retour du pop-up OK
        CANCEL (int): Code de retour du pop-up annulation
    """
    OK = 1
    CANCEL = 2
    
    @staticmethod
    def pop_up(message, title="Warning !",flag_block=False):
        def window_message(message, title):
            try:
                if message == 'fin de programme':
                    ctypes.windll.user32.MessageBoxW(0, f"programme terminé anormalement", title, 48)
                else:
                    ctypes.windll.user32.MessageBoxW(0, message, title, 48)
            except Exception as e:
                log.log_error(f"{'window_message error':=^40}")
                log.log_error(f"Message: {message}")
                log.log_error(f"Title: {title}")
                log.log_error(f"Error: {str(e)}")
                log.log_error(f"fin de programme")
                sys.exit(1)

        if flag_block:
            window_message(message, title)
        else:
            thread = threading.Thread(target=window_message, args=(message, title))
            thread.start()

class tree:
    utilitaire = 'utils'
    librarie = 'lib'


