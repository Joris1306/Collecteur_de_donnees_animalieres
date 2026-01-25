from utlitaires import app,get_properties,my_ip
import os
import threading
from utlitaires import data_receiver



if __name__ == "__main__":
    properties = get_properties()
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        threading.Thread(target=data_receiver._io_worker, daemon=True).start()

    app.run(
        port=properties.get('PORT'),
        # host=properties.get('LOCALHOST'),
        host=my_ip(),
        debug=True
    )
