import os
import json
import requests
import sys
import datetime
import random
import utlitaires
from typing import Literal

BASE_PATH = os.path.dirname(__file__)
SAMPLE_PATH = os.path.join(BASE_PATH,'SAMPLE')

class metadata_trap:
    @staticmethod
    def get_weather():
        with open(utlitaires.JSON_API_KEY,'r') as f:
            data = json.load(f)
        api_key = data.get('WHEATER')
        # print(api_key)
        city = "Saint-Mars-du-Désert,FR"  # specify country to avoid ambiguity
        URL = "https://api.openweathermap.org/data/2.5/weather"

        params = {
            "q": city,
            "appid": api_key,
            "units": "metric",   # Celsius
            "lang": "en"
        }

        response = requests.get(URL, params=params)
        data = response.json()

        if response.status_code == 200:
            return data["main"]
        else:
            print("Error:", data)
            sys.exit(sys.EXIT_FAILURE)

    @staticmethod
    def get_default_data():
        with open(os.path.join(BASE_PATH,'JSON','config.json'),'r') as f:
            data = json.load(f)

        liste_key = [key for key,_ in data.items()]
        # print(liste_key)
        default_data = {}
        # with open(os.path.join(BASE_PATH,'SAMPLE','stream.txt'), 'r') as f:
        #     buffer = f.read()
            
        # default_data['IMG'] = buffer
        default_data['IMG.TYPE'] = 'JPEG' # modifié en fonction du buffer
        default_data['IMG.WIDTH'] = 320
        default_data['IMG.HEIGHT'] = 240
        weather = metadata_trap.get_weather()
        # print(weather)
        default_data['WHEATER.TEMP'] = weather.get('temp')
        default_data['WHEATER.HUM'] = weather.get('humidity')
        # default_data['GPS.LONG'] = -1.379
        # default_data['GPS.LAT'] = 47.373
        default_data['GPS.LONG'] = -1.5159
        default_data['GPS.LAT'] = 47.2819
        _date = datetime.datetime.now()
        default_data['DATE.YEAR'] = _date.year
        default_data['DATE.MONTH'] = _date.month
        default_data['DATE.DAY'] = _date.day
        default_data['DATE.HOUR'] = _date.hour
        default_data['DATE.MINUTE'] = _date.minute
        default_data['DATE.SECOND'] = _date.second
        default_data['CAM.BATTERY'] = random.randrange(0,100)
        default_data['CAM.ID'] = 3

        return default_data

    @staticmethod
    def init_default_data():
        default_data = metadata_trap.get_default_data()
        with open(os.path.join(BASE_PATH,'SAMPLE','data.json'), "w") as f:
            json.dump(default_data, f)

class json_emitter:
    properties = utlitaires.get_properties()
    RECEIVER_IP = properties.get(properties.get('IP'))
    RECEIVER_PORT = properties.get('PORT')
    METADATA_PATH = properties.get('METADATA_PATH')
    IMAGE_PATH = properties.get('IMAGE_PATH')
    @staticmethod
    def send_data(data):
        url = f"http://{json_emitter.RECEIVER_IP}:{json_emitter.RECEIVER_PORT}{json_emitter.METADATA_PATH}?key={utlitaires.get_properties().get('INGEST_API_KEY')}"


        response = requests.post(url, data=data)
        print(response)

    @staticmethod
    def send_image(image_buff):
        url = f"http://{json_emitter.RECEIVER_IP}:{json_emitter.RECEIVER_PORT}{json_emitter.IMAGE_PATH}?key={utlitaires.get_properties().get('INGEST_API_KEY')}"

        response = requests.post(url, data=image_buff)
        print(response)

class load_sample:
    @staticmethod
    def sample_image(pic = Literal['pic0','pic1','pic2','pic3','pic4']):
        try:
            with open(os.path.join(SAMPLE_PATH,f'{pic}_buffer.txt'), 'r') as f:
                data = f.read()
            data = data.replace('\n','')
            return data
        except Exception as e:
            print(f"Error loading sample image: {e}")
            return None


def main():
    # check si le serveur est en ligne
    url = f"http://{json_emitter.RECEIVER_IP}:{json_emitter.RECEIVER_PORT}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Serveur en ligne")
        else:
            print("Serveur hors ligne")
    except Exception as e:
        print(f"Error checking server status: {e}")
        sys.exit(1)

    

    data = metadata_trap.get_default_data()

    # with open(os.path.join(BASE_PATH,'SAMPLE','data.json'), 'r') as f:
    #     data = json.load(f)

    # data['IMG'] = load_sample.sample_image('pic0')
    # print(str(data))
    
    json_emitter.send_image(load_sample.sample_image('pic5'))

    # with open(os.path.join(SAMPLE_PATH,'mouse.txt'), 'r') as f:
    #     buf = f.read()

    # json_emitter.send_image(buf)

    json_emitter.send_data(str(data))


if __name__ == "__main__":
    main()