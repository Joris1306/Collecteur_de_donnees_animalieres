# equivalent de script.sh

import os
import subprocess
import json
import pathlib
import shutil

def flatten(liste):
    for item in liste:
        if isinstance(item, list):
            for subitem in flatten(item):
                yield subitem
        else:
            yield item

def load_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def predict_species(image_path):
    JSON_FILE = 'file.json'
    JSON_ADAPTED = f'adapted_{JSON_FILE}'
    IMG_FOLDER = pathlib.Path(image_path).parent
    OUTPUT = 'output'
    try:
        shutil.copyfile(JSON_FILE,os.path.join('temp',JSON_FILE))
        os.remove(JSON_FILE)
        os.remove(JSON_ADAPTED)
    except:
        print("No files to remove")
    python_path = os.path.join(pathlib.Path.home(), '.venv3.12', 'bin', 'python') #'~/.venv3.12/bin/python'

    subprocess.run(
        [
            f'{python_path}',
            '-m',
            'speciesnet.scripts.run_model',
            '--folders',
            f'{IMG_FOLDER}',
            '--predictions_json', 
            f'{JSON_FILE}'
        ], 
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    subprocess.run(
        [
            'python',''
            'adapt_json.py',''
            f'{JSON_FILE}'],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    subprocess.run(
        [
            f'{python_path}',
            '-m', 
            'megadetector.visualization.visualize_detector_output',
            f'{JSON_ADAPTED}', 
            f'{OUTPUT}',
            '--images_dir',
            f'{IMG_FOLDER}'
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    

    output_path = os.path.join(f'{OUTPUT}',f'anno_{os.path.basename(image_path)}')
    subprocess.run(
        [
            'open',
            f'{output_path}'
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    data = load_json(f'{JSON_ADAPTED}').get('predictions')[0].get('prediction').split(';')[-1]
    # print(data)
    # print(len(data))

    return data