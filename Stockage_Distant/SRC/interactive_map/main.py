import folium
from IPython.display import display
import os
import webbrowser
import sys

class web_map:
    zoom_position = 'Saint Mars-du-desert'
    default_param = {
        "France": {
            "default_location": [46.2276, 2.2137],
            "default_zoom": 6
            },
        "Saint Mars-du-desert":{
            "default_location": [47.373, -1.379],
            "default_zoom": 13
        }
    }

    default_location = default_param[zoom_position]["default_location"]
    default_zoom = default_param[zoom_position]["default_zoom"]
    map_world = folium.Map(location=default_location, zoom_start=default_zoom)

    @staticmethod
    def init_cam_list(cam_list:dict[str, list[float]]):
        web_map.cam_list = cam_list

        for cam in cam_list:
            folium.Marker(cam_list[cam], popup=cam).add_to(web_map.map_world)

    @staticmethod
    def open_map():
        webbrowser.open("file://" + os.path.abspath("map.html"))

    @staticmethod
    def save_map():
        web_map.map_world.save("map.html")
    

def main():
    cities = {
        "Tokyo": [35.6895, 139.6917],
        "Delhi": [28.7041, 77.1025],
        "Shanghai": [31.2304, 121.4737],
        "Sao Paulo": [-23.5505, -46.6333],
        "Mexico City": [19.4326, -99.1332],
        "Saint Mars-du-desert": [47.373, -1.379],
    }

    web_map.init_cam_list(cities)
    web_map.save_map()
    web_map.open_map()

if __name__ == "__main__":
    main()