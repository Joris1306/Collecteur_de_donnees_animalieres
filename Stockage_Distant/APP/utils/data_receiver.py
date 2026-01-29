import queue
import threading
import time
import json
from flask import request
import ast

from utlitaires import app,logging,get_properties
from utils.sql_db import sql_db


class data_receiver:

    data = {}
    _io_queue = queue.Queue()
    # in-memory temporary hex buffer (no files)
    # store raw bytes as a mutable buffer for safe chunked appends
    _temp_buffer = bytearray()
    _buffer_lock = threading.Lock()
    # SSE notification system
    _update_listeners = []
    _listeners_lock = threading.Lock()

    def _io_worker():
        while True:
            item = data_receiver._io_queue.get()
            try:
                if item['type'] == 'image':
                    data = item['data']
                    # convert incoming chunk to raw bytes and append to the byte buffer
                    chunk_bytes = None
                    if isinstance(data, (bytes, bytearray)):
                        # try to detect ASCII-encoded hex (with or without 0x prefixes)
                        try:
                            text = data.decode('ascii')
                            test_text = text.replace('0x', '').replace('0X', '')
                            if all(c in "0123456789abcdefABCDEF \n\r\t" for c in test_text):
                                # normalize, strip 0x prefixes and convert to bytes
                                cleaned = "".join(c for c in test_text if c in "0123456789abcdefABCDEF")
                                if cleaned:
                                    chunk_bytes = bytes.fromhex(cleaned)
                            else:
                                # treat as raw binary
                                chunk_bytes = bytes(data)
                        except UnicodeDecodeError:
                            # binary data
                            chunk_bytes = bytes(data)
                    elif isinstance(data, str):
                        test_data = data.replace('0x', '').replace('0X', '')
                        if all(c in "0123456789abcdefABCDEF \n\r\t " for c in test_data):
                            cleaned = "".join(c for c in test_data if c in "0123456789abcdefABCDEF")
                            if cleaned:
                                chunk_bytes = bytes.fromhex(cleaned)

                    if chunk_bytes is None:
                        # fallback: try to coerce to bytes
                        try:
                            chunk_bytes = bytes(data)
                        except Exception:
                            chunk_bytes = b""

                    # append bytes to in-memory buffer (thread-safe)
                    with data_receiver._buffer_lock:
                        data_receiver._temp_buffer.extend(chunk_bytes)
                    
                elif item['type'] == 'metadata':
                    # item['data'] is raw bytes; decode to string
                    try:
                        s = item["data"].decode().strip()
                    except Exception:
                        # fallback if already a string
                        s = item["data"].strip()

                    try:
                        metadata = json.loads(s)
                    except (ValueError, json.JSONDecodeError):
                        try:
                            metadata = ast.literal_eval(s)
                        except (ValueError, SyntaxError) as e:
                            logging.error("metadata parse error:", e)
                            metadata = {}

                    if not isinstance(metadata, dict):
                        metadata = {}

                    # attach the accumulated in-memory buffer as the IMG field (raw bytes).
                    # Wait briefly for trailing image chunks when needed (handles chunked senders).
                    timeout = 2.0
                    poll_interval = 0.05
                    start_time = time.time()

                    # take a snapshot (do not clear yet)
                    with data_receiver._buffer_lock:
                        content = bytes(data_receiver._temp_buffer)

                    # If incoming data looks like JPEG but missing EOI, wait a short time for remaining chunks
                    if (b'\xff\xd8' in content) and (b'\xff\xd9' not in content):
                        while time.time() - start_time < timeout:
                            time.sleep(poll_interval)
                            with data_receiver._buffer_lock:
                                content = bytes(data_receiver._temp_buffer)
                            if (b'\xff\xd8' in content) and (b'\xff\xd9' in content):
                                break

                    # clear buffer now that we've captured content snapshot
                    with data_receiver._buffer_lock:
                        data_receiver._temp_buffer = bytearray()

                    metadata["IMG"] = content
                    
                    
                    # store parsed metadata in the class-level data holder
                    data_receiver.data = metadata
                    metadata['IMAGE_REPERTOIRE'] = sql_db.path_from_buffer(metadata)

                    # 
                    # AI_CLASSIFICATION
                    # chemin de l'image reçu : metadata['IMAGE_REPERTOIRE']
                    # défintion de l'état ('ETAT')
                    # 
                    # metadata['ETAT'] = IA_CLASSIFICATION.get_etat(metadata['IMAGE_REPERTOIRE'])
                    #

                    sql_db.insert_img(metadata)

                    logging.info(f"{'metadata saved to sql':=^100}")
                    sql_db.log_event(
                        event_type="image received", 
                        description=f"Image received and stored in database from CAM.ID={metadata.get('CAM.ID')}", 
                        cam_id=metadata.get('CAM.ID'),
                        image_id=None,
                    )
                    
                    # Notify all SSE listeners about new data
                    with data_receiver._listeners_lock:
                        for listener_queue in data_receiver._update_listeners:
                            try:
                                listener_queue.put_nowait({'event': 'new_image', 'cam_id': metadata.get('CAM.ID')})
                            except queue.Full:
                                pass

            except queue.Empty:
                pass
            except Exception as e:
                logging.error(f"{item['type']} error")
                # logging.error(f"Received {item['data'][:16]}[...]{item['data'][-16:]}")
                logging.error(f"received = {item['data']}")
                # logging.error(f"data = {metadata}")
                logging.error("I/O worker error:", e)
            finally:
                logging.info("task done")
                data_receiver._io_queue.task_done()

