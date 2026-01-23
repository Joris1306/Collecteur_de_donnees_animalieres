import requests
import json
import os
# import random
# from faker import Faker
BASE_PATH = os.path.dirname(__file__)
def main():
    url = "http://127.0.0.1:5000/api/data"

    with open(os.path.join(BASE_PATH,'data.json'),'r') as f:
        payload = json.load(f)

    response = requests.post(url, json=payload)
    print(response.json())

if __name__ == "__main__":
    main()