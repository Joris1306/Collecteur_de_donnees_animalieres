import json
import os
import datetime
import random
import requests
import sys

BASE_PATH = os.path.dirname(__file__)

def get_weather():
    with open(os.path.join(BASE_PATH,'API_KEY.json'),'r') as f:
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
    
def init_default_data():
    with open(os.path.join(BASE_PATH,'config.json'),'r') as f:
        data = json.load(f)

    liste_key = [key for key,_ in data.items()]
    # print(liste_key)
    default_data = {}
    with open(os.path.join(BASE_PATH,'stream.txt'), 'r') as f:
        buffer = f.read()
        
    default_data['IMG'] = buffer
    weather = get_weather()
    # print(weather)
    default_data['WHEATER.TEMP'] = weather.get('temp')
    default_data['WHEATER.HUM'] = weather.get('humidity')
    default_data['GPS.LONG'] = -1.379
    default_data['GPS.LAT'] = 47.373
    _date = datetime.datetime.now()
    default_data['DATE.YEAR'] = _date.year
    default_data['DATE.MONTH'] = _date.month
    default_data['DATE.DAY'] = _date.day
    default_data['DATE.HOUR'] = _date.hour
    default_data['DATE.MINUTE'] = _date.minute
    default_data['DATE.SECOND'] = _date.second
    default_data['CAM.BATTERY'] = random.randrange(0,100)

    with open(os.path.join(BASE_PATH,'data.json'), "w") as f:
        json.dump(default_data, f)

def main():
    init_default_data()


if __name__ == "__main__":
    main()