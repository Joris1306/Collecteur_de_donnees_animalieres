import folium
import webbrowser
import os
import sys
from pathlib import Path

# Add parent directory to path so this script can be run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utlitaires import BASE_PATH 

class web_map:
    MAP_URL = os.path.join(BASE_PATH, "templates", "map.html")
    zoom_position = 'Polytech'
    default_param = {
        "France": {
            "default_location": [46.2276, 2.2137],
            "default_zoom": 6
            },
        "Saint Mars-du-desert":{
            "default_location": [47.373, -1.379],
            "default_zoom": 13
        },
        "Polytech": {
            "default_location": [47.2819, -1.5159],
            "default_zoom": 14
        }
    }

    default_location = default_param[zoom_position]["default_location"]
    default_zoom = default_param[zoom_position]["default_zoom"]
    map_world = folium.Map(location=default_location, zoom_start=default_zoom)

    @staticmethod
    def init_cam_list(cam_list: dict[str, list[float]]):
        web_map.cam_list = cam_list

        for cam, coords in cam_list.items():
            popup_html = f'''
            <h3>Camera {cam}</h3>
            <a href="#" onclick="window.top.location.href='/battery/{cam}/graph'; return false;">
                Open Battery
            </a>
            <a href="#" onclick="window.top.location.href='/image/{cam}'; return false;">
                Open Image
            </a>
            '''

            folium.Marker(
                coords,
                popup=popup_html
            ).add_to(web_map.map_world) 

    @staticmethod
    def open_map():
        map_path = Path(web_map.MAP_URL).resolve()
        if not map_path.exists():
            web_map.save_map()
        return webbrowser.open_new_tab(map_path.as_uri())

    @staticmethod
    def save_map():
        return web_map.map_world.save(web_map.MAP_URL)

# Module-level wrappers for convenient imports
def init_cam_list(cam_list: dict[str, list[float]]):
    return web_map.init_cam_list(cam_list)


def open_map():
    return web_map.open_map()


def save_map():
    return web_map.save_map()


def main():
    print(f"{'Testing web_map module':=^100}")
    web_map.save_map()
    print(f"Map saved to {web_map.MAP_URL}")
    if web_map.open_map():
        print(f"Map opened in a new tab")
    else:
        print(f"Failed to open map")

if __name__ == "__main__":
    main()