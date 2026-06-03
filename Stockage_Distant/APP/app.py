from utlitaires import app,get_properties,my_ip
import os
import threading
from utlitaires import data_receiver
import logging

if __name__ == "__main__":
    properties = get_properties()
    debug_mode = os.environ.get("FLASK_DEBUG", "0").strip().lower() in {"1", "true", "yes", "on"}
    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.setLevel(logging.WARNING)
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not debug_mode:
        threading.Thread(target=data_receiver._io_worker, daemon=True).start()

    logging.info(f"Starting Flask app on http://{my_ip()}:{properties.get('PORT')} with debug mode {'enabled' if debug_mode else 'disabled'}")
    
    app.run(
        port=properties.get('PORT'),
        # host=properties.get('LOCALHOST'),
        host=my_ip(),
        debug=debug_mode
    )
