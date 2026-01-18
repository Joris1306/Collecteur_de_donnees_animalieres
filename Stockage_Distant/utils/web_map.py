import folium
import webbrowser
import os

from utlitaires import BASE_PATH 

class web_map:
    MAP_URL = 'map.html'
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
            "default_location": [47.368, -1.386],
            "default_zoom": 13
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
        webbrowser.open_new_tab(web_map.MAP_URL)

    @staticmethod
    def save_map():
        web_map.map_world.save(os.path.join(BASE_PATH, "templates", "map.html"))